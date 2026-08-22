import os
import subprocess
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, Query
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_admin
from app.db.database import get_db
from app.db.models import User, ServerModel
from app.core.manager import server_manager

router = APIRouter(tags=["system"])

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
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    # Sweep all servers
    for s_id in list(server_manager.processes.keys()):
        server_manager.kill_server(s_id)

    await db.execute(delete(ServerModel))
    await db.execute(delete(User).where(User.id != current_user.id))
    await db.commit()
    return {"success": True, "data": {"deletedServers": 0, "deletedUsers": 0}}

@router.get("/v1/jobs")
async def list_jobs(current_user: User = Depends(get_current_user)):
    return {"success": True, "data": []}
