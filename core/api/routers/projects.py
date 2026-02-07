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
    Initialize a new project workspace with template support.
    
    Data:
    - name: str (required) - Project name
    - description: str (optional) - Project description
    - template: str (optional) - Template type: basic, web, api, microservice
    - stack: str (optional) - Technology stack info
    - status: str (optional) - Initial status, default: planning
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
        template = data.get('template', 'basic')
        stack = data.get('stack', '')
        status = data.get('status', 'planning')
        
        # 1. Create directory structure based on template
        project_path.mkdir(parents=True, exist_ok=True)
        (project_path / "docs" / "specs").mkdir(parents=True, exist_ok=True)
        
        # Template-specific structure
        if template == 'web':
            (project_path / "frontend").mkdir(parents=True, exist_ok=True)
            (project_path / "nginx").mkdir(parents=True, exist_ok=True)
        elif template == 'api':
            (project_path / "api").mkdir(parents=True, exist_ok=True)
            (project_path / "tests").mkdir(parents=True, exist_ok=True)
        elif template == 'microservice':
            (project_path / "service").mkdir(parents=True, exist_ok=True)
            (project_path / "deployment").mkdir(parents=True, exist_ok=True)
        
        # 2. Create Enhanced Manifest
        manifest = {
            "project": {
                "name": name,
                "version": "0.1.0",
                "description": data.get('description', 'New NHI Project'),
                "folder": folder_name,
                "template": template,
                "stack": stack
            },
            "status": {
                "stage": status,
                "health": "unknown",
                "created": "2026-02-07",
                "last_updated": "2026-02-07"
            },
            "frontend": {
                "personality": "system"
            },
            "development": {
                "ai_guided": True,
                "nhi_compliant": True
            }
        }
        
        with open(project_path / "project_manifest.yaml", 'w') as f:
            yaml.dump(manifest, f, default_flow_style=False)
            
        # 3. Create Template-specific README
        readme_content = f"""# {name}

{data.get('description', 'New NHI Project')}

## Project Information
- **Template**: {template.title()}
- **Technology Stack**: {stack or 'Not specified'}
- **Status**: {status.title()}
- **Created**: 2026-02-07

## AI-Guided Development
This project is set up for AI-assisted development following NHI standards.

## Next Steps
1. Review and update project specifications in `docs/specs/`
2. Define project requirements and architecture
3. Begin development with AI agent assistance
4. Follow NHI documentation standards

> **Note**: This project follows NHI (Neural Home Infrastructure) standards and guidelines.
"""
        
        with open(project_path / "docs" / "README.md", 'w') as f:
            f.write(readme_content)
            
        return {
            "status": "success",
            "message": f"Project '{name}' initialized with {template} template",
            "path": str(project_path),
            "folder": folder_name,
            "template": template
        }
        
    except Exception as e:
        if project_path.exists():
            shutil.rmtree(project_path)
        raise HTTPException(status_code=500, detail=f"Failed to create project: {str(e)}")


@router.get("/templates")
async def get_project_templates():
    """Get available project templates."""
    return {
        "templates": [
            {
                "id": "basic",
                "name": "Basic Project",
                "description": "Minimal structure for generic projects",
                "structure": ["docs/", "docs/specs/"]
            },
            {
                "id": "web", 
                "name": "Web Application",
                "description": "Full web app with Docker and nginx",
                "structure": ["docs/", "docs/specs/", "frontend/", "nginx/"]
            },
            {
                "id": "api",
                "name": "API Service", 
                "description": "API service with OpenAPI spec",
                "structure": ["docs/", "docs/specs/", "api/", "tests/"]
            },
            {
                "id": "microservice",
                "name": "Microservice",
                "description": "Microservice with deployment config",
                "structure": ["docs/", "docs/specs/", "service/", "deployment/"]
            }
        ]
    }


@router.get("/system/rules")
async def get_system_rules():
    """Get NHI-CORE system rules and policies."""
    from pathlib import Path
    
    rules_files = [
        Path("/home/ai-agent/nhi-core-code/.cursorrules"),
        Path("/home/ai-agent/nhi-core-code/docs/policies"),
        Path("/home/ai-agent/nhi-core-code/rules")
    ]
    
    system_rules = {
        "core_rules": None,
        "policies": [],
        "operational_rules": []
    }
    
    # Read main .cursorrules
    cursorrules_path = rules_files[0]
    if cursorrules_path.exists():
        try:
            with open(cursorrules_path, 'r') as f:
                system_rules["core_rules"] = f.read()
        except Exception:
            system_rules["core_rules"] = "Error reading core rules"
    
    # Read policy files
    policies_path = rules_files[1]
    if policies_path.exists() and policies_path.is_dir():
        for policy_file in policies_path.glob("*.md"):
            try:
                with open(policy_file, 'r') as f:
                    system_rules["policies"].append({
                        "name": policy_file.stem,
                        "content": f.read()
                    })
            except Exception:
                continue
    
    # Read operational rules
    rules_path = rules_files[2]
    if rules_path.exists() and rules_path.is_dir():
        for rule_file in rules_path.glob("*.yaml"):
            try:
                with open(rule_file, 'r') as f:
                    import yaml
                    rule_content = yaml.safe_load(f)
                    system_rules["operational_rules"].append({
                        "name": rule_file.stem,
                        "content": rule_content
                    })
            except Exception:
                continue
    
    return system_rules


@router.get("/system/docs/{doc_path:path}")
async def get_system_documentation(doc_path: str):
    """Get NHI-CORE technical documentation."""
    from pathlib import Path
    from fastapi import HTTPException
    
    # Security: limit to docs directory
    base_docs_path = Path("/home/ai-agent/nhi-core-code/docs")
    requested_path = base_docs_path / doc_path
    
    # Resolve and check if it's within base path
    try:
        requested_path = requested_path.resolve()
        if not str(requested_path).startswith(str(base_docs_path.resolve())):
            raise HTTPException(status_code=403, detail="Access denied")
    except Exception:
        raise HTTPException(status_code=404, detail="Documentation not found")
    
    if not requested_path.exists() or not requested_path.is_file():
        raise HTTPException(status_code=404, detail="Documentation file not found")
    
    try:
        with open(requested_path, 'r') as f:
            content = f.read()
        
        return {
            "path": str(requested_path),
            "name": requested_path.name,
            "content": content,
            "type": requested_path.suffix
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading documentation: {str(e)}")


@router.put("/{project_name}/status")
async def update_project_status(project_name: str, data: dict):
    """Update project status (planning/dev/test/prod/archive)."""
    from pathlib import Path
    from fastapi import HTTPException
    import yaml
    import datetime
    
    project_path = PROJECTS_ROOT / project_name
    manifest_path = project_path / "project_manifest.yaml"
    
    if not project_path.exists():
        raise HTTPException(status_code=404, detail=f"Project '{project_name}' not found")
    
    if not manifest_path.exists():
        raise HTTPException(status_code=404, detail=f"Project manifest not found")
    
    try:
        # Load existing manifest
        with open(manifest_path, 'r') as f:
            manifest = yaml.safe_load(f)
        
        new_status = data.get('status')
        if not new_status:
            raise HTTPException(status_code=400, detail="Status is required")
        
        # Validate status
        valid_statuses = ['planning', 'development', 'testing', 'production', 'archive']
        if new_status not in valid_statuses:
            raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
        
        # Update status
        manifest['status']['stage'] = new_status
        manifest['status']['last_updated'] = datetime.datetime.now().isoformat()
        
        # Save updated manifest
        with open(manifest_path, 'w') as f:
            yaml.dump(manifest, f, default_flow_style=False)
        
        return {
            "status": "success",
            "message": f"Project status updated to {new_status}",
            "project": project_name,
            "new_status": new_status
        }
        
    except yaml.YAMLError:
        raise HTTPException(status_code=500, detail="Error reading project manifest")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update status: {str(e)}")


@router.delete("/{project_name}")
async def delete_project(project_name: str, data: dict = {}):
    """Delete a project with confirmation."""
    from pathlib import Path
    from fastapi import HTTPException
    import shutil
    
    project_path = PROJECTS_ROOT / project_name
    
    if not project_path.exists():
        raise HTTPException(status_code=404, detail=f"Project '{project_name}' not found")
    
    # Check if it's NHI-CORE (system project)
    manifest_path = project_path / "project_manifest.yaml"
    if manifest_path.exists():
        try:
            import yaml
            with open(manifest_path, 'r') as f:
                manifest = yaml.safe_load(f)
            
            # Check if this is NHI-CORE system
            if manifest.get('project', {}).get('name') == 'NHI-CORE':
                raise HTTPException(status_code=403, detail="Cannot delete system project NHI-CORE")
        except yaml.YAMLError:
            pass  # Continue with deletion if manifest is corrupted
    
    # Require confirmation
    confirm = data.get('confirm', False)
    if not confirm:
        return {
            "status": "warning",
            "message": "Deletion requires confirmation",
            "confirm_required": True,
            "project": project_name
        }
    
    try:
        # Backup project info before deletion
        project_info = {
            "name": project_name,
            "path": str(project_path),
            "deleted_at": "2026-02-07"
        }
        
        # Delete project directory
        shutil.rmtree(project_path)
        
        return {
            "status": "success",
            "message": f"Project '{project_name}' deleted successfully",
            "project_info": project_info
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete project: {str(e)}")
