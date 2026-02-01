from fastapi import APIRouter
from core.backup import BackupManager
from core.backup.dependency_resolver import DependencyResolver

router = APIRouter()

@router.get("/status")
async def get_backup_status():
    """Get current backup configuration and status."""
    # In a real scenario, we would inject config here
    # For now returning placeholder or reading from direct instantiation if safe
    return {
        "enabled": False,
        "last_backup": None,
        "policy": "core+infra"
    }

@router.post("/run")
async def trigger_backup():
    """Trigger an immediate backup."""
    return {"status": "started", "job_id": "mock-job-123"}
