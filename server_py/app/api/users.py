import os
import time
import uuid
import shutil
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db, hash_password
from app.db.models import User, ServerModel
from app.api.deps import get_current_user, require_admin
from app.core.manager import server_manager

router = APIRouter(prefix="/v1/users", tags=["users"])

class CreateUserPayload(BaseModel):
    username: str
    password: str
    role: str = "player"

class UpdateUserPayload(BaseModel):
    role: Optional[str] = None
    password: Optional[str] = None

class DeleteMyServersPayload(BaseModel):
    confirmation: str

@router.get("")
async def list_users(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User))
    users = result.scalars().all()
    return {"success": True, "data": [u.to_dict() for u in users]}

@router.post("")
async def create_user(
    payload: CreateUserPayload,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.username == payload.username))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Username already exists")

    new_user = User(
        id=str(uuid.uuid4()),
        username=payload.username,
        password_hash=hash_password(payload.password),
        role=payload.role,
        created_at=int(time.time()),
        updated_at=int(time.time()),
    )
    db.add(new_user)
    await db.commit()
    return {"success": True, "data": new_user.to_dict()}

@router.patch("/{user_id}")
async def update_user(
    user_id: str,
    payload: UpdateUserPayload,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if payload.role:
        user.role = payload.role
    if payload.password:
        user.password_hash = hash_password(payload.password)
    user.updated_at = int(time.time())
    await db.commit()
    return {"success": True, "data": user.to_dict()}

@router.delete("/me/servers")
async def delete_all_my_servers(
    payload: DeleteMyServersPayload,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if payload.confirmation != "DELETE ALL MY SERVERS":
        raise HTTPException(status_code=400, detail="Invalid confirmation text. Must type exactly: DELETE ALL MY SERVERS")

    # Fetch user's servers
    result = await db.execute(select(ServerModel).where(ServerModel.owner_id == current_user.id))
    servers = result.scalars().all()

    for s in servers:
        server_manager.kill_server(s.id)
        s_dir = server_manager.get_server_dir(s.id)
        if os.path.exists(s_dir):
            shutil.rmtree(s_dir, ignore_errors=True)

    await db.execute(delete(ServerModel).where(ServerModel.owner_id == current_user.id))
    await db.commit()
    return {"success": True, "data": {"deletedCount": len(servers)}}

@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")

    await db.execute(delete(User).where(User.id == user_id))
    await db.commit()
    return {"success": True, "data": None}
