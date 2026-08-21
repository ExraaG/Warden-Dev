import uuid
import time
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.models import ScheduledTask, User
from app.api.deps import get_current_user, require_admin

router = APIRouter(prefix="/v1/tasks", tags=["tasks"])

class CreateTaskPayload(BaseModel):
    serverId: Optional[str] = None
    name: str
    action: str
    payload: Optional[str] = ""
    cronExpression: str
    enabled: bool = True

@router.get("")
async def list_tasks(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(ScheduledTask))
    tasks = result.scalars().all()
    return {"success": True, "data": [t.to_dict() for t in tasks]}

@router.post("")
async def create_task(
    payload: CreateTaskPayload,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    task = ScheduledTask(
        id=str(uuid.uuid4()),
        server_id=payload.serverId,
        name=payload.name,
        action=payload.action,
        payload=payload.payload or "",
        cron_expression=payload.cronExpression,
        enabled=payload.enabled,
        created_at=int(time.time()),
    )
    db.add(task)
    await db.commit()
    return {"success": True, "data": task.to_dict()}

@router.delete("/{task_id}")
async def delete_task(
    task_id: str,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    await db.execute(delete(ScheduledTask).where(ScheduledTask.id == task_id))
    await db.commit()
    return {"success": True, "data": None}
