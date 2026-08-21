import os
import time
import shutil
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.database import get_db
from app.db.models import ServerModel, User
from app.api.deps import get_current_user
from app.core.manager import server_manager
from app.core.installer import ServerInstaller

router = APIRouter(prefix="/v1/servers", tags=["servers"])

class CreateServerPayload(BaseModel):
    name: str
    loader: str = "vanilla"
    mcVersion: str = "1.21.4"
    port: int = 25565
    minMemory: str = "1G"
    maxMemory: str = "4G"
    autoStart: bool = False

@router.get("")
async def list_servers(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(ServerModel))
    servers = result.scalars().all()

    server_list = []
    for s in servers:
        d = s.to_dict()
        proc = server_manager.get_server_process(s.id)
        d["status"] = proc.status if proc else s.status
        d["eulaAccepted"] = server_manager.is_eula_accepted(s.id)
        server_list.append(d)

    return {"success": True, "data": server_list}

@router.post("")
async def create_server(
    payload: CreateServerPayload,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    server_id = f"server-{int(time.time() * 1000)}"
    target_dir = server_manager.get_server_dir(server_id)

    install_result = await ServerInstaller.install_server(target_dir, payload.model_dump())

    new_server = ServerModel(
        id=server_id,
        name=payload.name,
        owner_id=current_user.id,
        loader=payload.loader,
        mc_version=payload.mcVersion,
        status="offline",
        port=payload.port,
        min_memory=payload.minMemory,
        max_memory=payload.maxMemory,
        jar_file=install_result.get("jarFileName"),
        auto_start=payload.autoStart,
        created_at=int(time.time()),
        updated_at=int(time.time()),
    )
    db.add(new_server)
    await db.commit()

    return {"success": True, "data": new_server.to_dict()}

@router.get("/{server_id}")
async def get_server(
    server_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(ServerModel).where(ServerModel.id == server_id))
    server = result.scalars().first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    d = server.to_dict()
    proc = server_manager.get_server_process(server.id)
    d["status"] = proc.status if proc else server.status
    d["eulaAccepted"] = server_manager.is_eula_accepted(server.id)
    return {"success": True, "data": d}

@router.post("/{server_id}/start")
async def start_server(
    server_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(ServerModel).where(ServerModel.id == server_id))
    server = result.scalars().first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    try:
        server_manager.start_server(
            server_id=server.id,
            jar_file=server.jar_file,
            java_path=server.java_path,
            min_memory=server.min_memory,
            max_memory=server.max_memory,
            mc_version=server.mc_version,
        )
        return {"success": True, "data": {"status": "starting"}}
    except ValueError as e:
        if str(e) == "EULA_NOT_ACCEPTED":
            raise HTTPException(status_code=400, detail="EULA_NOT_ACCEPTED")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{server_id}/stop")
async def stop_server(
    server_id: str,
    current_user: User = Depends(get_current_user),
):
    server_manager.stop_server(server_id)
    return {"success": True, "data": {"status": "stopping"}}

@router.post("/{server_id}/restart")
async def restart_server(
    server_id: str,
    current_user: User = Depends(get_current_user),
):
    server_manager.restart_server(server_id)
    return {"success": True, "data": {"status": "restarting"}}

@router.post("/{server_id}/kill")
async def kill_server(
    server_id: str,
    current_user: User = Depends(get_current_user),
):
    server_manager.kill_server(server_id)
    return {"success": True, "data": {"status": "offline"}}

@router.delete("/{server_id}")
async def delete_server(
    server_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    server_manager.kill_server(server_id)
    server_dir = server_manager.get_server_dir(server_id)
    if os.path.exists(server_dir):
        shutil.rmtree(server_dir, ignore_errors=True)

    await db.execute(delete(ServerModel).where(ServerModel.id == server_id))
    await db.commit()
    return {"success": True, "data": None}

@router.post("/{server_id}/eula")
async def accept_eula(
    server_id: str,
    current_user: User = Depends(get_current_user),
):
    server_manager.accept_eula(server_id)
    return {"success": True, "data": {"eulaAccepted": True}}

@router.get("/{server_id}/stats")
async def get_server_stats(
    server_id: str,
    current_user: User = Depends(get_current_user),
):
    stats = server_manager.get_stats(server_id)
    return {"success": True, "data": stats}
