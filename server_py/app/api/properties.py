from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api.deps import get_current_user
from app.db.models import User
from app.core.manager import server_manager

router = APIRouter(prefix="/v1/servers/{server_id}/properties", tags=["properties"])

@router.get("")
async def get_properties(
    server_id: str,
    current_user: User = Depends(get_current_user),
):
    try:
        props = server_manager.get_properties(server_id)
        return {"success": True, "data": props}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("")
@router.put("")
async def save_properties(
    server_id: str,
    properties: Dict[str, Any],
    current_user: User = Depends(get_current_user),
):
    try:
        server_manager.save_properties(server_id, properties)
        return {"success": True, "data": properties}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
