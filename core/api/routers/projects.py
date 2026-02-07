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
    
    # ---------------------------------------------------------
    # TIER 1: SYSTEM CONTOL PLANE (NHI-CORE)
    # ---------------------------------------------------------
    core_path = Path("/home/ai-agent/nhi-core-code")
    if core_path.exists():
        # Synthesize manifest for Core
        core_data = {
            "name": "NHI-CORE",
            "folder": "nhi-core-code",
            "path": str(core_path),
            "description": "Neural Home Infrastructure Control Plane (Core System)",
            "personality": "system",
            "type": "system",
            "status": "production",
            "git_branch": "main",
            "version": "1.1.0"
        }
        projects.append(core_data)
        
    # ---------------------------------------------------------
    # TIER 2: APPLICATION ECOSYSTEM
    # ---------------------------------------------------------
    if PROJECTS_ROOT.exists():
        for item in PROJECTS_ROOT.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                # Base Object
                project_data = {
                    "name": item.name,
                    "folder": item.name,
                    "path": str(item),
                    "description": "No description provided.",
                    "personality": "system",
                    "type": "application",
                    "status": "development" # Default
                }
                
                # Try to load Manifest
                manifest_path = item / "project_manifest.yaml"
                if manifest_path.exists():
                    try:
                        with open(manifest_path, 'r') as f:
                            manifest = yaml.safe_load(f) or {}
                            
                            # 1. Project Metadata
                            proj_meta = manifest.get('project', {})
                            if 'name' in proj_meta: project_data['name'] = proj_meta['name']
                            if 'description' in proj_meta: project_data['description'] = proj_meta['description']
                            
                            # 2. Frontend/Personality
                            fe_meta = manifest.get('frontend', {})
                            if 'personality' in fe_meta: project_data['personality'] = fe_meta['personality']
                            
                            # 3. Status
                            status_meta = manifest.get('status', {})
                            # Handle both string "beta" and object {"stage": "dev"}
                            if isinstance(status_meta, str):
                                project_data['status'] = status_meta
                            elif isinstance(status_meta, dict):
                                project_data['status'] = status_meta.get('stage', 'development')

                            # 4. Version
                            if 'version' in proj_meta:
                                project_data['version'] = proj_meta['version']

                    except Exception:
                        project_data['description'] = "Error reading manifest."
                
                projects.append(project_data)
    
    return {"projects": projects}


def get_project_path(folder: str) -> Path:
    """Resolve project path from folder name."""
    if folder == "nhi-core-code":
        return Path("/home/ai-agent/nhi-core-code")
    return PROJECTS_ROOT / folder


@router.get("/{folder}/manifest")
async def get_project_manifest(folder: str):
    """Get the project_manifest.yaml content."""
    from fastapi import HTTPException
    
    project_path = get_project_path(folder)
    
    if not project_path.exists():
        raise HTTPException(status_code=404, detail=f"Project '{folder}' not found")
    
    manifest_path = project_path / "project_manifest.yaml"
    
    # Synthesize for Core if missing
    if folder == "nhi-core-code" and not manifest_path.exists():
        fake_manifest = """# SYNTHESIZED MANIFEST FOR NHI-CORE
project:
  name: NHI-CORE
  description: System Control Plane
  version: 1.1.0
type: system
status: production
"""
        return {
            "exists": True,
            "path": "(synthesized)",
            "content": yaml.safe_load(fake_manifest),
            "raw": fake_manifest
        }

    if not manifest_path.exists():
        return {
            "exists": False,
            "message": f"No manifest found at {manifest_path}",
            "content": None
        }
    
    try:
        with open(manifest_path, 'r') as f:
            content = yaml.safe_load(f)
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


@router.post("/")
async def create_project(data: dict):
    """
    Initialize a new project workspace.
    
    Data:
    - name: str (required) - Used for folder name
    - description: str (optional)
    """
    from fastapi import HTTPException
    import shutil
    
    name = data.get('name')
    if not name:
        raise HTTPException(status_code=400, detail="Project name is required")
    
    # Sanitize name
    folder_name = "".join(c for c in name if c.isalnum() or c in ('-', '_')).strip()
    if not folder_name:
        raise HTTPException(status_code=400, detail="Invalid project name")
        
    project_path = PROJECTS_ROOT / folder_name
    
    if project_path.exists():
        raise HTTPException(status_code=409, detail=f"Project '{folder_name}' already exists")
        
    try:
        # 1. Create directory structure (Context Initializer)
        project_path.mkdir(parents=True, exist_ok=True)
        (project_path / "docs" / "specs").mkdir(parents=True, exist_ok=True)
        
        # 2. Create Minimal Manifest
        manifest = {
            "project": {
                "name": name,
                "version": "0.1.0",
                "description": data.get('description', 'New NHI Project'),
                "folder": folder_name
            },
            "status": {
                "stage": "planning",
                "health": "unknown"
            },
            "frontend": {
                "personality": "system" # Default
            }
        }
        
        with open(project_path / "project_manifest.yaml", 'w') as f:
            yaml.dump(manifest, f, default_flow_style=False)
            
        # 3. Create Placeholder README
        with open(project_path / "docs" / "README.md", 'w') as f:
            f.write(f"# {name}\n\n{data.get('description', '')}\n\n> **Workspace Initialized**\n> Please upload your specification to `docs/specs/` to begin.")
            
        return {
            "status": "success",
            "message": f"Workspace '{name}' initialized",
            "path": str(project_path),
            "folder": folder_name
        }
        
    except Exception as e:
        if project_path.exists():
            shutil.rmtree(project_path)
        raise HTTPException(status_code=500, detail=f"Failed to create project: {str(e)}")
