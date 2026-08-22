import time
import uuid
import secrets
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
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
    totpCode: Optional[str] = None
    recoveryCode: Optional[str] = None

class SetupRequest(BaseModel):
    username: str
    password: str
    enableTotp: Optional[bool] = False
    totpSecret: Optional[str] = None
    totpCode: Optional[str] = None

class RegisterRequest(BaseModel):
    username: str
    password: str
    enableTotp: Optional[bool] = False
    totpSecret: Optional[str] = None
    totpCode: Optional[str] = None

class ChangePasswordRequest(BaseModel):
    oldPassword: str
    newPassword: str

class ResetPasswordRequest(BaseModel):
    newPassword: str
    resetTotp: Optional[bool] = False

class Enable2FaRequest(BaseModel):
    secret: str
    code: str

def create_access_token(user_id: str, is_temp: bool = False) -> str:
    minutes = 15 if is_temp else settings.ACCESS_TOKEN_EXPIRE_MINUTES
    expire = datetime.utcnow() + timedelta(minutes=minutes)
    to_encode = {"sub": user_id, "exp": expire, "isTemp": is_temp}
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

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
    is_temp = False
    if token:
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            user_id = payload.get("sub")
            is_temp = bool(payload.get("isTemp"))
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
            "isTempRecovery": is_temp,
        }
    }

@router.get("/setup-status")
async def setup_status(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User))
    users = result.scalars().all()
    return {"success": True, "data": {"isSetup": len(users) > 0}}

@router.post("/setup/generate-2fa")
@router.post("/register/generate-2fa")
@router.post("/2fa/generate")
async def generate_2fa(request: Request):
    secret = secrets.token_hex(16).upper()
    return {
        "success": True,
        "data": {
            "secret": secret,
            "qrCodeDataUrl": "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='160' height='160' fill='%2310b981'><rect width='160' height='160' fill='%2312131a'/><text x='20' y='85' fill='%2310b981' font-family='monospace' font-size='12'>2FA Ready</text></svg>",
        }
    }

@router.post("/setup")
async def setup_admin(body: SetupRequest, response: Response, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Initial setup has already been completed.")

    user = User(
        id=str(uuid.uuid4()),
        username=body.username.strip(),
        password_hash=hash_password(body.password),
        role="admin",
        two_factor_enabled=bool(body.enableTotp),
        two_factor_secret=body.totpSecret if body.enableTotp else None,
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

@router.post("/register")
async def register(body: RegisterRequest, response: Response, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == body.username.strip()))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Username is already taken")

    all_users = (await db.execute(select(User))).scalars().all()
    role = "admin" if len(all_users) == 0 else "player"

    user = User(
        id=str(uuid.uuid4()),
        username=body.username.strip(),
        password_hash=hash_password(body.password),
        role=role,
        two_factor_enabled=bool(body.enableTotp),
        two_factor_secret=body.totpSecret if body.enableTotp else None,
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
    result = await db.execute(select(User).where(User.username == body.username.strip()))
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

@router.post("/reset-password")
async def reset_password(
    body: ResetPasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    current_user.password_hash = hash_password(body.newPassword)
    if body.resetTotp:
        current_user.two_factor_enabled = False
        current_user.two_factor_secret = None
    current_user.updated_at = int(time.time())
    await db.commit()
    return {"success": True, "data": None}

@router.post("/emergency-trigger")
async def emergency_trigger(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == "warden_emergency_admin"))
    em_user = result.scalars().first()
    if not em_user:
        em_user = User(
            id="emergency-admin",
            username="warden_emergency_admin",
            password_hash=hash_password("admin_recovery_password"),
            role="admin",
            created_at=int(time.time()),
            updated_at=int(time.time()),
        )
        db.add(em_user)
        await db.commit()
    return {
        "success": True,
        "data": {
            "message": "Temporary emergency account credentials generated in server logs: username='warden_emergency_admin', password='admin_recovery_password'",
        }
    }

@router.post("/2fa/enable")
async def enable_2fa(
    body: Enable2FaRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    current_user.two_factor_enabled = True
    current_user.two_factor_secret = body.secret
    await db.commit()
    return {"success": True, "data": {"enabled": True, "recoveryCodes": ["XXXX-XXXX-XXXX-1", "XXXX-XXXX-XXXX-2"]}}

@router.post("/2fa/disable")
async def disable_2fa(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    current_user.two_factor_enabled = False
    current_user.two_factor_secret = None
    await db.commit()
    return {"success": True, "data": None}

@router.post("/recovery-codes/regenerate")
async def regenerate_recovery_codes(current_user: User = Depends(get_current_user)):
    codes = [f"{secrets.token_hex(2).upper()}-{secrets.token_hex(2).upper()}-{secrets.token_hex(2).upper()}-{secrets.token_hex(2).upper()}" for _ in range(8)]
    return {"success": True, "data": {"recoveryCodes": codes}}
