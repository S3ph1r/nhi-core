from fastapi import APIRouter, HTTPException
from pathlib import Path
import os
from typing import List, Dict, Optional

router = APIRouter()

PROJECTS_ROOT = Path("/home/ai-agent/projects")
CORE_DEV_PATH = Path("/home/ai-agent/nhi-core-code")
CORE_PROD_PATH = Path("/opt/nhi-core")

def get_docs_path(project_folder: str) -> Optional[Path]:
    """Resolve the docs directory for a given project folder."""
    
    # Special case for NHI-CORE
    if project_folder in ["nhi-core", "nhi-core-code"]:
        if CORE_DEV_PATH.exists():
            return CORE_DEV_PATH / "docs"
        elif CORE_PROD_PATH.exists():
            return CORE_PROD_PATH / "docs"
        return None
    
    # Standard projects
    project_path = PROJECTS_ROOT / project_folder
    if project_path.exists() and project_path.is_dir():
        docs_path = project_path / "docs"
        if docs_path.exists():
            return docs_path
            
    return None

@router.get("/{project_folder}/structure")
async def get_docs_structure(project_folder: str):
    """
    Get the documentation file structure for a project.
    Returns a list of markdown files.
    """
    docs_path = get_docs_path(project_folder)
    
    if not docs_path or not docs_path.exists():
        raise HTTPException(status_code=404, detail=f"Documentation not found for {project_folder}")
    
    files = []
    try:
        # Walk through the docs directory
        for root, _, filenames in os.walk(docs_path):
            for filename in filenames:
                if filename.endswith(('.md', '.markdown', '.txt')):
                    full_path = Path(root) / filename
                    rel_path = full_path.relative_to(docs_path)
                    
                    files.append({
                        "name": str(rel_path),
                        "path": str(rel_path),
                        "description": filename.replace('-', ' ').replace('.md', '').title()
                    })
        
        # Sort files (README first, then alphabetical)
        files.sort(key=lambda x: (0 if 'readme' in x['name'].lower() else 1, x['name']))
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
    return {"files": files, "project": project_folder}

@router.get("/{project_folder}/{file_path:path}")
async def get_doc_content(project_folder: str, file_path: str):
    """
    Get the content of a specific documentation file.
    """
    docs_path = get_docs_path(project_folder)
    
    if not docs_path or not docs_path.exists():
        raise HTTPException(status_code=404, detail=f"Documentation not found for {project_folder}")
    
    # Sanitize path to prevent directory traversal
    target_file = (docs_path / file_path).resolve()
    
    # Ensure legitimate file within docs dir
    if not str(target_file).startswith(str(docs_path.resolve())):
        raise HTTPException(status_code=403, detail="Access denied")
        
    if not target_file.exists():
        raise HTTPException(status_code=404, detail="File not found")
        
    try:
        content = target_file.read_text(encoding='utf-8')
        return {
            "content": content,
            "filename": target_file.name,
            "language": "markdown" # Assume markdown for now
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
