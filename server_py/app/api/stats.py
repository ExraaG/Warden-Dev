import time
import psutil
from fastapi import APIRouter, Depends
from app.api.deps import get_current_user
from app.db.models import User

router = APIRouter(prefix="/v1/stats", tags=["stats"])

@router.get("")
async def get_system_stats(current_user: User = Depends(get_current_user)):
    vm = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    boot_time = psutil.boot_time()

    return {
        "success": True,
        "data": {
            "cpuPercent": round(psutil.cpu_percent(interval=None), 1),
            "memory": {
                "totalBytes": vm.total,
                "usedBytes": vm.used,
                "freeBytes": vm.available,
                "percent": vm.percent,
            },
            "disk": {
                "totalBytes": disk.total,
                "usedBytes": disk.used,
                "freeBytes": disk.free,
                "percent": disk.percent,
            },
            "uptimeSeconds": int(time.time() - boot_time),
        }
    }
