import json
from typing import Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.models import Setting, User
from app.api.deps import get_current_user, require_admin

router = APIRouter(prefix="/v1/settings", tags=["settings"])

@router.get("")
async def get_settings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Setting))
    settings_list = result.scalars().all()
    data: Dict[str, Any] = {
        "timezone": "Europe/Vienna",
        "craftyUrl": "",
        "autoUpdateEnabled": True,
        "autoUpdateTime": "04:00",
        "customTasks": [],
    }
    for s in settings_list:
        try:
            data[s.key] = json.loads(s.value)
        except Exception:
            data[s.key] = s.value
    return {"success": True, "data": data}

@router.post("")
async def save_settings(
    settings_payload: Dict[str, Any],
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    for k, v in settings_payload.items():
        val_str = json.dumps(v) if not isinstance(v, str) else v
        result = await db.execute(select(Setting).where(Setting.key == k))
        existing = result.scalars().first()
        if existing:
            existing.value = val_str
        else:
            db.add(Setting(key=k, value=val_str))
    await db.commit()
    return {"success": True, "data": settings_payload}
