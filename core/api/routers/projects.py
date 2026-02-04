from fastapi import APIRouter
import os
import yaml
from pathlib import Path

router = APIRouter()

PROJECTS_ROOT = Path("/home/ai-agent/projects")

@router.get("/")
async def list_projects():
    """List all projects in the projects root directory."""
    projects = []
    
    # 0. Add Core Project (NHI-CORE)
    core_path = Path("/home/ai-agent/nhi-core-code")
    if core_path.exists():
        core_data = {
            "name": "NHI-CORE",
            "folder": "nhi-core",
            "path": str(core_path),
            "description": "Neural Home Infrastructure Control Plane (Core System)",
            "personality": "system",
            "git_branch": "main",
            "version": "1.1.0"
        }
        projects.append(core_data)
        
    # 1. Add known core projects (mock if necessary or scan specifically)
    # 2. Scan disk
    if PROJECTS_ROOT.exists():
        for item in PROJECTS_ROOT.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                project_data = {
                    "name": item.name,
                    "folder": item.name,  # Preserve folder name for URL routing
                    "path": str(item),
                    "description": "No description",
                    "personality": "system"
                }
                
                # Check for manifest (project_manifest.yaml or package.json)
                manifest_path = item / "project_manifest.yaml"
                package_json = item / "package.json"
                
                if manifest_path.exists():
                    try:
                        with open(manifest_path, 'r') as f:
                            manifest = yaml.safe_load(f)
                            project_data.update(manifest.get('project', {}))
                            # Normalize fields
                            if 'name' in manifest.get('project', {}):
                                project_data['name'] = manifest['project']['name']
                    except:
                        pass
                elif package_json.exists():
                    try:
                        with open(package_json, 'r') as f:
                            import json
                            pkg = json.load(f)
                            project_data['description'] = pkg.get('description', '')
                    except:
                        pass
                
                projects.append(project_data)
    
    # Return wrapped in object as expected by frontend
    return {"projects": projects}


def get_project_path(folder: str) -> Path:
    """Resolve project path from folder name."""
    if folder == "nhi-core":
        return Path("/home/ai-agent/nhi-core-code")
    return PROJECTS_ROOT / folder


@router.get("/{folder}/manifest")
async def get_project_manifest(folder: str):
    """Get the project_manifest.yaml content for a project."""
    from fastapi import HTTPException
    
    project_path = get_project_path(folder)
    
    if not project_path.exists():
        raise HTTPException(status_code=404, detail=f"Project '{folder}' not found")
    
    manifest_path = project_path / "project_manifest.yaml"
    
    if not manifest_path.exists():
        # Return empty manifest structure
        return {
            "exists": False,
            "message": f"No manifest found at {manifest_path}",
            "content": None
        }
    
    try:
        with open(manifest_path, 'r') as f:
            content = yaml.safe_load(f)
        
        # Also return raw text for display
        with open(manifest_path, 'r') as f:
            raw = f.read()
        
        return {
            "exists": True,
            "path": str(manifest_path),
            "content": content,
            "raw": raw
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
