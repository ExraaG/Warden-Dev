import os
import shutil
import zipfile
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from pydantic import BaseModel

from app.api.deps import get_current_user
from app.db.models import User
from app.core.manager import server_manager

router = APIRouter(prefix="/v1/servers/{server_id}/files", tags=["files"])

class WriteFilePayload(BaseModel):
    path: str
    content: str

class DeleteFilePayload(BaseModel):
    path: str

class RenamePayload(BaseModel):
    oldPath: str
    newPath: str

class CompressPayload(BaseModel):
    paths: list[str]
    zipName: str

class ExtractPayload(BaseModel):
    zipPath: str
    targetPath: Optional[str] = None

@router.get("")
async def list_files(
    server_id: str,
    path: str = "",
    current_user: User = Depends(get_current_user),
):
    try:
        files = server_manager.list_files(server_id, path)
        return {"success": True, "data": files}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/content")
async def get_file_content(
    server_id: str,
    path: str = Query(...),
    current_user: User = Depends(get_current_user),
):
    try:
        content = server_manager.read_file(server_id, path)
        return {"success": True, "data": content}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/content")
async def save_file_content(
    server_id: str,
    payload: WriteFilePayload,
    current_user: User = Depends(get_current_user),
):
    try:
        server_manager.write_file(server_id, payload.path, payload.content)
        return {"success": True, "data": None}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/upload")
async def upload_file(
    server_id: str,
    file: UploadFile = File(...),
    targetPath: str = Form(""),
    current_user: User = Depends(get_current_user),
):
    try:
        base_dir = server_manager.get_server_dir(server_id)
        dest_dir = os.path.abspath(os.path.join(base_dir, targetPath.lstrip("/")))
        if not dest_dir.startswith(base_dir):
            raise PermissionError("Access denied")

        os.makedirs(dest_dir, exist_ok=True)
        final_path = os.path.join(dest_dir, file.filename)

        with open(final_path, "wb") as f:
            content = await file.read()
            f.write(content)

        return {"success": True, "data": {"filename": file.filename}}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("")
async def delete_file(
    server_id: str,
    payload: DeleteFilePayload,
    current_user: User = Depends(get_current_user),
):
    try:
        server_manager.delete_file(server_id, payload.path)
        return {"success": True, "data": None}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/rename")
async def rename_file(
    server_id: str,
    payload: RenamePayload,
    current_user: User = Depends(get_current_user),
):
    try:
        base_dir = server_manager.get_server_dir(server_id)
        src = os.path.abspath(os.path.join(base_dir, payload.oldPath.lstrip("/")))
        dst = os.path.abspath(os.path.join(base_dir, payload.newPath.lstrip("/")))
        if not src.startswith(base_dir) or not dst.startswith(base_dir):
            raise PermissionError("Access denied")

        os.rename(src, dst)
        return {"success": True, "data": None}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
