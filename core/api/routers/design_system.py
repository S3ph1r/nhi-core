"""
Design System Router - Serves NHIDS static files and info
"""

import os
import yaml
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, Response
from pathlib import Path

router = APIRouter()

DESIGN_SYSTEM_PATH = Path("/var/lib/nhi/design-system")


@router.get("/info")
async def get_design_system_info():
    """Get design system metadata and available personalities."""
    registry_path = DESIGN_SYSTEM_PATH / "registry.yaml"
    
    if not registry_path.exists():
        raise HTTPException(status_code=404, detail="Design system not configured")
    
    with open(registry_path, 'r') as f:
        registry = yaml.safe_load(f)
    
    return {
        "version": registry.get("version", "unknown"),
        "core_version": registry.get("core", {}).get("version", "unknown"),
        "personalities": registry.get("personalities", []),
        "defaults": registry.get("defaults", {})
    }


@router.get("/core/tokens.css")
async def get_tokens_css():
    """Serve core tokens CSS."""
    file_path = DESIGN_SYSTEM_PATH / "core" / "tokens.css"
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="tokens.css not found")
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    return Response(content=content, media_type="text/css")


@router.get("/core/primitives.css")
async def get_primitives_css():
    """Serve core primitives CSS."""
    file_path = DESIGN_SYSTEM_PATH / "core" / "primitives.css"
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="primitives.css not found")
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    return Response(content=content, media_type="text/css")


@router.get("/core/icons.css")
async def get_icons_css():
    """Serve core icons CSS."""
    file_path = DESIGN_SYSTEM_PATH / "core" / "icons.css"
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="icons.css not found")
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    return Response(content=content, media_type="text/css")


@router.get("/core/icons-phosphor.css")
async def get_icons_phosphor_css():
    """Serve phosphor icons bridge CSS."""
    file_path = DESIGN_SYSTEM_PATH / "core" / "icons-phosphor.css"
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="icons-phosphor.css not found")
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    return Response(content=content, media_type="text/css")


@router.get("/core/icons-heroicons.css")
async def get_icons_heroicons_css():
    """Serve heroicons bridge CSS."""
    file_path = DESIGN_SYSTEM_PATH / "core" / "icons-heroicons.css"
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="icons-heroicons.css not found")
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    return Response(content=content, media_type="text/css")


@router.get("/themes/{personality}.css")
async def get_theme_css(personality: str):
    """Serve a personality theme CSS."""
    file_path = DESIGN_SYSTEM_PATH / "personalities" / personality / "theme.css"
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Theme '{personality}' not found")
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    return Response(content=content, media_type="text/css")


@router.get("/themes/{personality}/manifest")
async def get_theme_manifest(personality: str):
    """Get a personality's manifest."""
    file_path = DESIGN_SYSTEM_PATH / "personalities" / personality / "manifest.yaml"
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Theme '{personality}' not found")
    
    with open(file_path, 'r') as f:
        manifest = yaml.safe_load(f)
    
    return manifest


@router.get("/bundle/{personality}.css")
async def get_bundled_css(personality: str):
    """Get a bundled CSS file with tokens + primitives + icons + theme."""
    tokens_path = DESIGN_SYSTEM_PATH / "core" / "tokens.css"
    primitives_path = DESIGN_SYSTEM_PATH / "core" / "primitives.css"
    icons_path = DESIGN_SYSTEM_PATH / "core" / "icons.css"
    theme_path = DESIGN_SYSTEM_PATH / "personalities" / personality / "theme.css"
    
    if not theme_path.exists():
        raise HTTPException(status_code=404, detail=f"Theme '{personality}' not found")
    
    bundle = []
    
    # Read and append each file
    if tokens_path.exists():
        with open(tokens_path, 'r') as f:
            bundle.append(f"/* === TOKENS === */\n{f.read()}")
    
    if primitives_path.exists():
        with open(primitives_path, 'r') as f:
            bundle.append(f"/* === PRIMITIVES === */\n{f.read()}")

    if icons_path.exists():
        with open(icons_path, 'r') as f:
            bundle.append(f"/* === ICONS === */\n{f.read()}")
    
    with open(theme_path, 'r') as f:
        # Remove @import statements as we're bundling
        theme_content = f.read()
        theme_content = '\n'.join(
            line for line in theme_content.split('\n')
            if not line.strip().startswith('@import')
        )
        bundle.append(f"/* === THEME: {personality} === */\n{theme_content}")
    
    return Response(content='\n\n'.join(bundle), media_type="text/css")
