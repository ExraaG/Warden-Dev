import os
import json
import time
import shutil
import zipfile
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File, Form
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

class ServerActionPayload(BaseModel):
    action: str  # 'start' | 'stop' | 'restart' | 'kill'

class PlayerActionPayload(BaseModel):
    action: str  # 'op' | 'deop' | 'whitelist' | 'unwhitelist' | 'kick' | 'ban' | 'unban' | 'ban-ip' | 'pardon-ip'
    player: Optional[str] = None
    ip: Optional[str] = None
    reason: Optional[str] = None

class ChangeLoaderPayload(BaseModel):
    loader: str
    mcVersion: str

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
        d["detection"] = {
            "loader": s.loader,
            "mcVersion": s.mc_version,
        }
        server_list.append(d)

    return {"success": True, "data": server_list}

async def _create_server_impl(payload: CreateServerPayload, current_user: User, db: AsyncSession):
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

    d = new_server.to_dict()
    d["eulaAccepted"] = server_manager.is_eula_accepted(server_id)
    return {"success": True, "data": d}

@router.post("")
async def create_server(
    payload: CreateServerPayload,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await _create_server_impl(payload, current_user, db)

@router.post("/create")
async def create_server_alias(
    payload: CreateServerPayload,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await _create_server_impl(payload, current_user, db)

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
    d["detection"] = {
        "loader": server.loader,
        "mcVersion": server.mc_version,
    }
    return {"success": True, "data": d}

@router.post("/{server_id}/action")
async def server_action(
    server_id: str,
    payload: ServerActionPayload,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    act = payload.action.lower()
    if act == "start":
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
    elif act == "stop":
        server_manager.stop_server(server_id)
        return {"success": True, "data": {"status": "stopping"}}
    elif act == "restart":
        server_manager.restart_server(server_id)
        return {"success": True, "data": {"status": "restarting"}}
    elif act == "kill":
        server_manager.kill_server(server_id)
        return {"success": True, "data": {"status": "offline"}}
    else:
        raise HTTPException(status_code=400, detail=f"Unknown action '{payload.action}'")

@router.post("/{server_id}/start")
async def start_server_direct(server_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await server_action(server_id, ServerActionPayload(action="start"), current_user, db)

@router.post("/{server_id}/stop")
async def stop_server_direct(server_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await server_action(server_id, ServerActionPayload(action="stop"), current_user, db)

@router.post("/{server_id}/restart")
async def restart_server_direct(server_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await server_action(server_id, ServerActionPayload(action="restart"), current_user, db)

@router.post("/{server_id}/kill")
async def kill_server_direct(server_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await server_action(server_id, ServerActionPayload(action="kill"), current_user, db)

@router.get("/{server_id}/eula")
async def get_eula(server_id: str, current_user: User = Depends(get_current_user)):
    accepted = server_manager.is_eula_accepted(server_id)
    return {"success": True, "data": {"accepted": accepted}}

@router.post("/{server_id}/eula")
async def post_eula(server_id: str, current_user: User = Depends(get_current_user)):
    server_manager.accept_eula(server_id)
    return {"success": True, "data": {"accepted": True, "eulaAccepted": True}}

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

@router.get("/{server_id}/stats")
async def get_server_stats(server_id: str, current_user: User = Depends(get_current_user)):
    return {"success": True, "data": server_manager.get_stats(server_id)}

@router.get("/{server_id}/players")
async def get_server_players(server_id: str, current_user: User = Depends(get_current_user)):
    server_dir = server_manager.get_server_dir(server_id)
    proc = server_manager.get_server_process(server_id)
    online_players = list(proc.online_players) if proc else []

    def read_json_list(filename):
        p = os.path.join(server_dir, filename)
        if os.path.exists(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return []

    ops = read_json_list("ops.json")
    whitelist = read_json_list("whitelist.json")
    banned_players = read_json_list("banned-players.json")

    return {
        "success": True,
        "data": {
            "online": [{"name": p} for p in online_players],
            "ops": ops,
            "whitelist": whitelist,
            "banned": banned_players,
        }
    }

@router.get("/{server_id}/players/banned-ips")
async def get_banned_ips(server_id: str, current_user: User = Depends(get_current_user)):
    server_dir = server_manager.get_server_dir(server_id)
    p = os.path.join(server_dir, "banned-ips.json")
    banned_ips = []
    if os.path.exists(p):
        try:
            with open(p, "r", encoding="utf-8") as f:
                banned_ips = json.load(f)
        except Exception:
            pass
    return {"success": True, "data": banned_ips}

@router.post("/{server_id}/players/action")
async def execute_player_action(
    server_id: str,
    payload: PlayerActionPayload,
    current_user: User = Depends(get_current_user),
):
    act = payload.action.lower()
    target = payload.player or payload.ip or ""

    cmd_map = {
        "op": f"op {target}",
        "deop": f"deop {target}",
        "whitelist": f"whitelist add {target}",
        "unwhitelist": f"whitelist remove {target}",
        "kick": f"kick {target} {payload.reason or 'Kicked by admin'}",
        "ban": f"ban {target} {payload.reason or 'Banned by admin'}",
        "unban": f"pardon {target}",
        "ban-ip": f"ban-ip {target} {payload.reason or 'IP banned by admin'}",
        "pardon-ip": f"pardon-ip {target}",
    }

    cmd = cmd_map.get(act)
    if not cmd:
        raise HTTPException(status_code=400, detail=f"Unsupported player action '{payload.action}'")

    success = server_manager.send_command(server_id, cmd)
    return {"success": success, "data": None}

@router.post("/{server_id}/change-loader")
async def change_loader(
    server_id: str,
    payload: ChangeLoaderPayload,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Preview step
    return {
        "success": True,
        "data": {
            "requiresConfirmation": True,
            "targetLoader": payload.loader,
            "targetVersion": payload.mcVersion,
        }
    }

@router.post("/{server_id}/confirm-loader")
async def confirm_loader(
    server_id: str,
    payload: ChangeLoaderPayload,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    server_manager.kill_server(server_id)
    server_dir = server_manager.get_server_dir(server_id)
    install_res = await ServerInstaller.install_server(server_dir, payload.model_dump())

    result = await db.execute(select(ServerModel).where(ServerModel.id == server_id))
    s = result.scalars().first()
    if s:
        s.loader = payload.loader
        s.mc_version = payload.mcVersion
        s.jar_file = install_res.get("jarFileName")
        s.updated_at = int(time.time())
        await db.commit()

    return {"success": True, "data": None}

@router.get("/{server_id}/export")
async def export_server(
    server_id: str,
    current_user: User = Depends(get_current_user),
):
    zip_name = server_manager.create_backup(server_id)
    return {"success": True, "data": {"filename": zip_name, "downloadUrl": f"/api/v1/backups/{zip_name}"}}
