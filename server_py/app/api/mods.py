import os
import httpx
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from pydantic import BaseModel

from app.api.deps import get_current_user
from app.db.models import User
from app.core.manager import server_manager

router = APIRouter(tags=["mods"])

class InstallModPayload(BaseModel):
    versionId: Optional[str] = None
    downloadUrl: str
    filename: str

@router.get("/v1/mods/search")
@router.get("/v1/servers/{server_id}/mods/search")
async def search_mods(
    server_id: Optional[str] = None,
    query: str = "",
    loader: Optional[str] = None,
    version: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
):
    facets = []
    if loader:
        facets.append([f"categories:{loader}"])
    if version:
        facets.append([f"versions:{version}"])

    params: Dict[str, Any] = {
        "query": query,
        "limit": limit,
        "offset": offset,
        "index": "relevance",
    }
    if facets:
        import json
        params["facets"] = json.dumps(facets)

    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            res = await client.get("https://api.modrinth.com/v2/search", params=params)
            res.raise_for_status()
            data = res.json()
            return {"success": True, "data": data.get("hits", [])}
        except Exception as e:
            return {"success": True, "data": []}

@router.get("/v1/mods/{project_id}/versions")
@router.get("/v1/servers/{server_id}/mods/versions")
async def get_mod_versions(
    project_id: Optional[str] = None,
    server_id: Optional[str] = None,
    loaders: Optional[str] = None,
    game_versions: Optional[str] = None,
    current_user: User = Depends(get_current_user),
):
    target_id = project_id or server_id
    params = {}
    if loaders:
        params["loaders"] = f'["{loaders}"]'
    if game_versions:
        params["game_versions"] = f'["{game_versions}"]'

    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            res = await client.get(f"https://api.modrinth.com/v2/project/{target_id}/version", params=params)
            res.raise_for_status()
            return {"success": True, "data": res.json()}
        except Exception:
            return {"success": True, "data": []}

@router.get("/v1/servers/{server_id}/mods")
async def get_installed_mods(
    server_id: str,
    current_user: User = Depends(get_current_user),
):
    mods_dir = os.path.join(server_manager.get_server_dir(server_id), "mods")
    if not os.path.exists(mods_dir):
        return {"success": True, "data": []}

    installed = []
    for f in os.listdir(mods_dir):
        if f.endswith(".jar") or f.endswith(".jar.disabled"):
            path = os.path.join(mods_dir, f)
            stat = os.stat(path)
            installed.append({
                "filename": f,
                "name": f.replace(".jar.disabled", "").replace(".jar", ""),
                "enabled": not f.endswith(".disabled"),
                "size": stat.st_size,
                "modified": int(stat.st_mtime * 1000),
            })
    return {"success": True, "data": installed}

@router.post("/v1/servers/{server_id}/mods/install")
async def install_mod(
    server_id: str,
    payload: InstallModPayload,
    current_user: User = Depends(get_current_user),
):
    mods_dir = os.path.join(server_manager.get_server_dir(server_id), "mods")
    os.makedirs(mods_dir, exist_ok=True)
    target_path = os.path.join(mods_dir, payload.filename)

    async with httpx.AsyncClient(timeout=45.0) as client:
        try:
            res = await client.get(payload.downloadUrl)
            res.raise_for_status()
            with open(target_path, "wb") as f:
                f.write(res.content)
            return {"success": True, "data": {"filename": payload.filename}}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to download mod: {e}")

@router.delete("/v1/servers/{server_id}/mods/{filename}")
async def delete_mod(
    server_id: str,
    filename: str,
    current_user: User = Depends(get_current_user),
):
    mods_dir = os.path.join(server_manager.get_server_dir(server_id), "mods")
    target_path = os.path.join(mods_dir, filename)
    if os.path.exists(target_path):
        os.remove(target_path)
    return {"success": True, "data": None}

@router.post("/v1/servers/{server_id}/mods/{filename}/toggle")
async def toggle_mod(
    server_id: str,
    filename: str,
    current_user: User = Depends(get_current_user),
):
    mods_dir = os.path.join(server_manager.get_server_dir(server_id), "mods")
    src = os.path.join(mods_dir, filename)
    if not os.path.exists(src):
        raise HTTPException(status_code=404, detail="Mod file not found")

    if filename.endswith(".disabled"):
        new_name = filename[:-9]
    else:
        new_name = f"{filename}.disabled"

    dst = os.path.join(mods_dir, new_name)
    os.rename(src, dst)
    return {"success": True, "data": {"filename": new_name, "enabled": not new_name.endswith(".disabled")}}
