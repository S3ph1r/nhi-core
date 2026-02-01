from fastapi import APIRouter
import os
import yaml
from pathlib import Path

router = APIRouter()

REGISTRY_PATH = "/var/lib/nhi/registry/services"

@router.get("/")
async def list_projects():
    """List all registered projects/services."""
    projects = []
    
    # Check if we are running in dev mode on windows or prod linux
    # Fallback for dev environment M:\ mapping if needed, 
    # but for now assume running on Linux or mock.
    
    # Simple Mock for dev if path doesn't exist
    if not os.path.exists(REGISTRY_PATH):
        return [
            {"name": "nhi-core", "type": "lxc", "status": "active", "ip": "192.168.1.117"},
            {"name": "warroom", "type": "vm", "status": "active", "ip": "192.168.1.106"}
        ]

    for f in Path(REGISTRY_PATH).glob("*.yaml"):
        try:
            with open(f, 'r') as file:
                data = yaml.safe_load(file)
                projects.append(data)
        except Exception:
            continue
            
    return projects
