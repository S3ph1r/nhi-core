from fastapi import APIRouter
import platform
import psutil
import socket

router = APIRouter()

@router.get("/status")
async def get_system_status():
    """Get core system health metrics."""
    return {
        "hostname": socket.gethostname(),
        "os": platform.system(),
        "release": platform.release(),
        "cpu_usage": psutil.cpu_percent(),
        "memory": psutil.virtual_memory()._asdict(),
        "disk": psutil.disk_usage('/')._asdict()
    }
