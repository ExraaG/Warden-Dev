from typing import List, Dict
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from app.api.deps import get_current_user
from app.db.models import User
from app.core.manager import server_manager

router = APIRouter(tags=["console"])

class CommandPayload(BaseModel):
    command: str

@router.get("/v1/servers/{server_id}/console")
async def get_console_logs(
    server_id: str,
    current_user: User = Depends(get_current_user),
):
    logs = server_manager.get_logs(server_id)
    return {"success": True, "data": logs}

@router.post("/v1/servers/{server_id}/console")
async def send_console_command(
    server_id: str,
    payload: CommandPayload,
    current_user: User = Depends(get_current_user),
):
    success = server_manager.send_command(server_id, payload.command)
    return {"success": success, "data": None}

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, server_id: str, websocket: WebSocket):
        await websocket.accept()
        if server_id not in self.active_connections:
            self.active_connections[server_id] = []
        self.active_connections[server_id].append(websocket)

    def disconnect(self, server_id: str, websocket: WebSocket):
        if server_id in self.active_connections:
            if websocket in self.active_connections[server_id]:
                self.active_connections[server_id].remove(websocket)

    async def broadcast_line(self, server_id: str, line: str):
        if server_id in self.active_connections:
            for connection in self.active_connections[server_id]:
                try:
                    await connection.send_text(line)
                except Exception:
                    pass

ws_manager = ConnectionManager()

# Hook server manager logs to WebSocket broadcaster
def on_global_log(server_id: str, line: str):
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.create_task(ws_manager.broadcast_line(server_id, line))
    except Exception:
        pass

server_manager.add_log_callback(on_global_log)

@router.websocket("/ws/servers/{server_id}/console")
async def websocket_console(websocket: WebSocket, server_id: str):
    await ws_manager.connect(server_id, websocket)
    # Send historical logs first
    logs = server_manager.get_logs(server_id)
    for log in logs[-100:]:
        await websocket.send_text(log)

    try:
        while True:
            cmd = await websocket.receive_text()
            if cmd:
                server_manager.send_command(server_id, cmd)
    except WebSocketDisconnect:
        ws_manager.disconnect(server_id, websocket)
    except Exception:
        ws_manager.disconnect(server_id, websocket)
