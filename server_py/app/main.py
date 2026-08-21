import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from app.config import settings
from app.db.database import init_db
from app.core.manager import server_manager

from app.api.auth import router as auth_router
from app.api.servers import router as servers_router
from app.api.console import router as console_router
from app.api.files import router as files_router
from app.api.properties import router as properties_router
from app.api.mods import router as mods_router
from app.api.tasks import router as tasks_router
from app.api.settings import router as settings_router
from app.api.stats import router as stats_router
from app.api.meta import router as meta_router
from app.api.system import router as system_router
from app.api.users import router as users_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    server_manager.sweep_orphaned_processes()
    print(f"[Warden Python Engine] Running on port {settings.PORT}")
    yield
    # Shutdown
    for proc in server_manager.processes.values():
        if proc.status == "online":
            proc.stop(timeout=5)

app = FastAPI(title="Warden Backend", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes
api_prefix = "/api"
app.include_router(auth_router, prefix=api_prefix)
app.include_router(servers_router, prefix=api_prefix)
app.include_router(console_router, prefix=api_prefix)
app.include_router(files_router, prefix=api_prefix)
app.include_router(properties_router, prefix=api_prefix)
app.include_router(mods_router, prefix=api_prefix)
app.include_router(tasks_router, prefix=api_prefix)
app.include_router(settings_router, prefix=api_prefix)
app.include_router(stats_router, prefix=api_prefix)
app.include_router(meta_router, prefix=api_prefix)
app.include_router(system_router, prefix=api_prefix)
app.include_router(users_router, prefix=api_prefix)

@app.get("/api/health")
async def health_check():
    return {"status": "ok", "engine": "warden-python"}

# Frontend static file serving
static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "static"))
next_dir = os.path.join(static_dir, "_next")
if os.path.exists(next_dir):
    app.mount("/_next", StaticFiles(directory=next_dir), name="_next")

@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    if full_path.startswith("api/") or full_path.startswith("ws/"):
        return JSONResponse(status_code=404, content={"detail": "Not Found"})

    if os.path.exists(static_dir):
        # 1. Exact file match (e.g. /favicon.ico, /warden_logo.png)
        file_path = os.path.join(static_dir, full_path)
        if full_path and os.path.isfile(file_path):
            return FileResponse(file_path)

        # 2. Named HTML page (e.g. /console -> console.html)
        html_page = os.path.join(static_dir, f"{full_path}.html")
        if full_path and os.path.isfile(html_page):
            return FileResponse(html_page)

        # 3. Fallback to index.html for SPA routing
        index_path = os.path.join(static_dir, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)

    return JSONResponse(
        content={
            "name": "Warden",
            "status": "running",
            "version": "1.0.0-py",
            "message": "Warden Python API is running.",
        }
    )
