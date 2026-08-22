import os
import shutil
import subprocess
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_admin
from app.db.database import get_db
from app.db.models import User, ServerModel, ScheduledTask, Setting
from app.core.manager import server_manager
from app.config import settings

router = APIRouter(tags=["system"])

class DevResetPayload(BaseModel):
    resetServers: Optional[bool] = True
    resetUsers: Optional[bool] = False
    keepCurrentAdmin: Optional[bool] = True

@router.get("/v1/system/update-status")
async def get_update_status(force: bool = Query(False)):
    return {
        "success": True,
        "data": {
            "updateAvailable": False,
            "currentCommit": "dev-py",
            "latestCommit": "dev-py",
            "commitMessage": "Warden Python Engine running",
            "author": "AlexH",
        }
    }

@router.get("/v1/system/update-progress")
async def get_update_progress():
    return {
        "success": True,
        "data": {
            "status": "idle",
            "step": 0,
            "totalSteps": 4,
            "stepName": "Ready",
            "percent": 0,
        }
    }

@router.post("/v1/system/self-update")
async def self_update(current_user: User = Depends(get_current_user)):
    return {"success": True, "data": {"status": "starting"}}

@router.post("/v1/system/dev-reset")
async def dev_reset(
    payload: Optional[DevResetPayload] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    p = payload or DevResetPayload()

    deleted_servers = 0
    deleted_users = 0

    if p.resetServers:
        for s_id in list(server_manager.processes.keys()):
            server_manager.kill_server(s_id)
        if os.path.exists(settings.servers_dir):
            shutil.rmtree(settings.servers_dir, ignore_errors=True)
            os.makedirs(settings.servers_dir, exist_ok=True)
        await db.execute(delete(ServerModel))
        deleted_servers = 1

    if p.resetUsers:
        if p.keepCurrentAdmin:
            await db.execute(delete(User).where(User.id != current_user.id))
        else:
            await db.execute(delete(User))
        deleted_users = 1

    await db.execute(delete(ScheduledTask))
    await db.commit()

    return {
        "success": True,
        "data": {
            "deletedServers": deleted_servers,
            "deletedUsers": deleted_users,
        }
    }

@router.get("/v1/jobs")
async def list_jobs(current_user: User = Depends(get_current_user)):
    return {"success": True, "data": []}
