from fastapi import APIRouter
import platform
import psutil
import socket
import json
import os
from datetime import datetime
from core.scanner import ProxmoxScanner

router = APIRouter()

SYSTEM_MAP_PATH = "/var/lib/nhi/context/system-map.json"

@router.get("/status")
async def get_system_status():
    """Get core system basic info."""
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
    """Get system health (Local + Cluster)."""
    # Local (Container) Stats
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    # Short interval for quick response
    cpu = psutil.cpu_percent(interval=None) 
    
    # Uptime
    uptime_seconds = int(datetime.now().timestamp() - psutil.boot_time())
    days, r = divmod(uptime_seconds, 86400)
    hours, r = divmod(r, 3600)
    uptime_str = f"{days}d {hours}h"
    
    # Cluster Stats (Live from Proxmox)
    cluster_stats = {}
    try:
        scanner = ProxmoxScanner()
        nodes = scanner.get_nodes()
        
        cluster_cpu_usage = 0
        cluster_cpu_max = 0
        cluster_mem_used = 0
        cluster_mem_total = 0
        
        for node in nodes:
             # Proxmox returns cpu as 0.0-1.0 usage factor usually, or sometimes per core?
             # 'cpu' field in node dict from API is usually 0.XX
             cluster_cpu_usage += node.get('cpu', 0)
             cluster_cpu_max += node.get('maxcpu', 0)
             cluster_mem_used += node.get('mem', 0)
             cluster_mem_total += node.get('maxmem', 0)
             
        # Normalize CPU percentage (average across nodes or sum?)
        # Usage is e.g. 0.05 for 5%. 
        # But if we want cluster total load... let's just send raw numbers or formatted.
        # Frontend expects % usually.
        # Let's send aggregated % relative to total capacity? 
        # Actually Proxmox 'cpu' is load relative to maxcpu of that node.
        # Let's average the load across nodes.
        avg_load = (cluster_cpu_usage / len(nodes)) * 100 if nodes else 0

        cluster_stats = {
            "status": "online",
            "nodes_count": len(nodes),
            "cpu_percent": round(avg_load, 1),
            "memory_used": cluster_mem_used,
            "memory_total": cluster_mem_total,
            "nodes": [n['name'] for n in nodes]
        }
    except Exception as e:
        print(f"Cluster scan failed: {e}")
        cluster_stats = {"status": "error", "message": str(e)}

    return {
        "local": {
            "cpu": cpu,
            "memory": {"percent": mem.percent, "used": mem.used, "total": mem.total},
            "disk": {"percent": disk.percent, "used": disk.used, "total": disk.total},
            "uptime": uptime_str,
            "hostname": socket.gethostname()
        },
        "cluster": cluster_stats
    }

@router.get("/resources")
async def get_resources():
    """Get list of resources from SSOT (system-map.json)."""
    resources = []
    
    if os.path.exists(SYSTEM_MAP_PATH):
        try:
            with open(SYSTEM_MAP_PATH, 'r') as f:
                data = json.load(f)
                resources = data.get("resources", [])
        except Exception as e:
            print(f"Failed to load system map: {e}")
    
    # Count projects
    projects_count = 0
    try:
        projects_dir = "/home/ai-agent/projects"
        if os.path.exists(projects_dir):
            projects_count = len([d for d in os.listdir(projects_dir) 
                                  if os.path.isdir(os.path.join(projects_dir, d))])
    except:
        pass
    
    return {
        "resources": resources,
        "projects_count": projects_count,
        "last_backup": "N/A"
    }


@router.get("/catalog")
async def get_system_catalog():
    """Get comprehensive system catalog with all file associations."""
    from core.context.system_map_builder import SystemMapBuilder
    
    builder = SystemMapBuilder()
    catalog = builder.build_catalog()
    
    return catalog


@router.post("/catalog/refresh")
async def refresh_system_catalog():
    """Regenerate and save system catalog."""
    from core.context.system_map_builder import SystemMapBuilder
    
    builder = SystemMapBuilder()
    output_path = builder.save_catalog()
    
    return {
        "status": "success",
        "path": output_path,
        "summary": builder.build_catalog()["summary"]
    }
