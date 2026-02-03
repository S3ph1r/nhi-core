from fastapi import APIRouter
import platform
import psutil
import socket
import subprocess
import json
from datetime import datetime, timedelta

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

@router.get("/health")
async def get_health():
    """Get system health for dashboard overview."""
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    # Get uptime
    uptime_seconds = int(datetime.now().timestamp() - psutil.boot_time())
    days, remainder = divmod(uptime_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    uptime_str = f"{days}d {hours}h" if days > 0 else f"{hours}h"
    
    return {
        "cpu": psutil.cpu_percent(interval=0.5),
        "memory": {
            "percent": mem.percent,
            "used": mem.used,
            "total": mem.total
        },
        "disk": {
            "percent": disk.percent,
            "used": disk.used,
            "total": disk.total
        },
        "uptime": uptime_str,
        "hostname": socket.gethostname()
    }

@router.get("/resources")
async def get_resources():
    """Get Proxmox LXC/VM resources list."""
    resources = []
    
    try:
        # Get LXC list from Proxmox via pvesh
        result = subprocess.run(
            ["pvesh", "get", "/nodes/homelab/lxc", "--output-format", "json"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            lxcs = json.loads(result.stdout)
            for lxc in lxcs:
                resources.append({
                    "type": "lxc",
                    "vmid": lxc.get("vmid"),
                    "name": lxc.get("name", ""),
                    "status": lxc.get("status", "unknown"),
                    "maxmem": lxc.get("maxmem", 0),
                    "cpu": lxc.get("cpu", 0),
                    "node": "homelab"
                })
    except Exception as e:
        # If pvesh not available, return empty list
        pass
    
    # Count projects (from /home/ai-agent/projects)
    projects_count = 0
    try:
        import os
        projects_dir = "/home/ai-agent/projects"
        if os.path.exists(projects_dir):
            projects_count = len([d for d in os.listdir(projects_dir) 
                                  if os.path.isdir(os.path.join(projects_dir, d))])
    except:
        pass
    
    return {
        "resources": resources,
        "projects_count": projects_count,
        "last_backup": "N/A"  # TODO: Get from backup system
    }

