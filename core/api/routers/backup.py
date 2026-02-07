from fastapi import APIRouter, HTTPException
from core.backup import BackupManager
from typing import Dict, List

router = APIRouter()
manager = BackupManager()

@router.get("/status")
async def get_backup_status():
    """Get current backup configuration and status."""
    return manager.status()

@router.get("/policy")
async def get_backup_policy():
    """Get the full service backup policy matrix."""
    return manager.get_policy_matrix()

@router.post("/run/{target_id}")
async def trigger_phoenix_backup(target_id: str):
    """Trigger an immediate Data-Only (Phoenix) backup."""
    result = manager.run_phoenix_backup(target_id)
    if not result.success:
        raise HTTPException(status_code=500, detail=result.message)
    return result

@router.post("/full-backup/{vmid}")
async def trigger_vzdump_backup(vmid: int, storage: str = None):
    """Trigger a full Proxmox vzdump backup."""
    try:
        results = manager.backup_now(storage=storage)
        # Filter for the requested VMID if backup_now returns a list
        target_result = next((r for r in results if r.vmid == vmid), None)
        if target_result and not target_result.success:
             raise HTTPException(status_code=500, detail=target_result.message)
        return target_result or {"status": "vzdump operation completed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
