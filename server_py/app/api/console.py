import asyncio
from typing import List, Dict
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
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
        # Captured on first WS connect — the running asyncio event loop
        self._loop: asyncio.AbstractEventLoop | None = None

    async def connect(self, server_id: str, websocket: WebSocket):
        await websocket.accept()
        # Capture the running loop so the reader thread can schedule into it
        if self._loop is None:
            self._loop = asyncio.get_running_loop()
        if server_id not in self.active_connections:
            self.active_connections[server_id] = []
        self.active_connections[server_id].append(websocket)

    def disconnect(self, server_id: str, websocket: WebSocket):
        if server_id in self.active_connections:
            if websocket in self.active_connections[server_id]:
                self.active_connections[server_id].remove(websocket)

    async def broadcast_line(self, server_id: str, line: str):
        if server_id not in self.active_connections:
            return
        dead = []
        for ws in list(self.active_connections[server_id]):
            try:
                await ws.send_text(line)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(server_id, ws)

    def broadcast_line_threadsafe(self, server_id: str, line: str):
        """Called from the Java-process reader thread — schedules broadcast on the event loop."""
        if self._loop is None or not self.active_connections.get(server_id):
            return
        try:
            asyncio.run_coroutine_threadsafe(
                self.broadcast_line(server_id, line),
                self._loop,
            )
        except Exception:
            pass


ws_manager = ConnectionManager()


def on_global_log(server_id: str, line: str):
    """Registered as a server_manager log callback — called from the reader thread."""
    ws_manager.broadcast_line_threadsafe(server_id, line)


server_manager.add_log_callback(on_global_log)


# WebSocket endpoint is registered WITHOUT the /api prefix in main.py
# so the client connects to ws://host/ws/servers/{server_id}/console
@router.websocket("/ws/servers/{server_id}/console")
async def websocket_console(websocket: WebSocket, server_id: str):
    await ws_manager.connect(server_id, websocket)
    # Replay last 200 lines of historical logs
    logs = server_manager.get_logs(server_id)
    for log in logs[-200:]:
        try:
            await websocket.send_text(log)
        except Exception:
            break

    try:
        while True:
            cmd = await websocket.receive_text()
            if cmd and cmd.strip():
                server_manager.send_command(server_id, cmd.strip())
    except WebSocketDisconnect:
        ws_manager.disconnect(server_id, websocket)
    except Exception:
        ws_manager.disconnect(server_id, websocket)
