import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from pydantic import BaseModel
from jose import jwt
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.database import get_db, verify_password, hash_password
from app.db.models import User
from app.api.deps import get_current_user, require_admin

router = APIRouter(prefix="/v1/auth", tags=["auth"])

class LoginRequest(BaseModel):
    username: str
    password: str

class SetupRequest(BaseModel):
    username: str
    password: str

class ChangePasswordRequest(BaseModel):
    oldPassword: str
    newPassword: str

class CreateUserRequest(BaseModel):
    username: str
    password: str
    role: str = "player"

def create_access_token(user_id: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"sub": user_id, "exp": expire}
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

class RegisterRequest(BaseModel):
    username: str
    password: str
    enableTotp: Optional[bool] = False

@router.get("/status")
async def auth_status(request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User))
    users = result.scalars().all()
    has_users = len(users) > 0

    token = request.headers.get("X-Warden-Token")
    if not token and "Authorization" in request.headers:
        auth_hdr = request.headers.get("Authorization", "")
        if auth_hdr.startswith("Bearer "):
            token = auth_hdr[7:]
    if not token and "warden_token" in request.cookies:
        token = request.cookies.get("warden_token")

    user_data = None
    authenticated = False
    if token:
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            user_id = payload.get("sub")
            if user_id:
                u_res = await db.execute(select(User).where(User.id == user_id))
                user = u_res.scalars().first()
                if user:
                    user_data = user.to_dict()
                    authenticated = True
        except Exception:
            pass

    return {
        "success": True,
        "data": {
            "hasUsers": has_users,
            "authenticated": authenticated,
            "user": user_data,
        }
    }

@router.get("/setup-status")
async def setup_status(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User))
    users = result.scalars().all()
    return {"success": True, "data": {"isSetup": len(users) > 0}}

@router.post("/register")
async def register(body: RegisterRequest, response: Response, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == body.username))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Username is already taken")

    all_users = (await db.execute(select(User))).scalars().all()
    role = "admin" if len(all_users) == 0 else "player"

    user = User(
        id=str(uuid.uuid4()),
        username=body.username,
        password_hash=hash_password(body.password),
        role=role,
        created_at=int(time.time()),
        updated_at=int(time.time()),
    )
    db.add(user)
    await db.commit()

    token = create_access_token(user.id)
    response.set_cookie(
        key="warden_token",
        value=token,
        httponly=True,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax",
    )
    return {"success": True, "data": {"token": token, "user": user.to_dict()}}

@router.post("/setup")
async def setup_admin(body: SetupRequest, response: Response, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Initial setup has already been completed.")

    user = User(
        id=str(uuid.uuid4()),
        username=body.username,
        password_hash=hash_password(body.password),
        role="admin",
        created_at=int(time.time()),
        updated_at=int(time.time()),
    )
    db.add(user)
    await db.commit()

    token = create_access_token(user.id)
    response.set_cookie(
        key="warden_token",
        value=token,
        httponly=True,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax",
    )
    return {"success": True, "data": {"token": token, "user": user.to_dict()}}

@router.post("/login")
async def login(body: LoginRequest, response: Response, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == body.username))
    user = result.scalars().first()

    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = create_access_token(user.id)
    response.set_cookie(
        key="warden_token",
        value=token,
        httponly=True,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax",
    )
    return {"success": True, "data": {"token": token, "user": user.to_dict()}}

@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("warden_token")
    return {"success": True, "data": None}

@router.get("/me")
async def me(current_user: User = Depends(get_current_user)):
    return {"success": True, "data": current_user.to_dict()}

@router.post("/change-password")
async def change_password(
    body: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not verify_password(body.oldPassword, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    current_user.password_hash = hash_password(body.newPassword)
    current_user.updated_at = int(time.time())
    await db.commit()
    return {"success": True, "data": None}

@router.get("/users")
async def list_users(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User))
    users = result.scalars().all()
    return {"success": True, "data": [u.to_dict() for u in users]}

@router.post("/users")
async def create_user(
    body: CreateUserRequest,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.username == body.username))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Username already exists")

    new_user = User(
        id=str(uuid.uuid4()),
        username=body.username,
        password_hash=hash_password(body.password),
        role=body.role,
        created_at=int(time.time()),
        updated_at=int(time.time()),
    )
    db.add(new_user)
    await db.commit()
    return {"success": True, "data": new_user.to_dict()}

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own admin account")

    await db.execute(delete(User).where(User.id == user_id))
    await db.commit()
    return {"success": True, "data": None}
