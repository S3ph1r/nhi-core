"""
Project Scaffolder - New Project Generation

Creates standardized project structure following NHI methodology.
"""

import os
import subprocess
from datetime import date
from pathlib import Path
from typing import Optional


class ProjectScaffolder:
    """Generates new NHI-compliant project structures."""
    
    PROJECTS_ROOT = Path("/home/ai-agent/projects")
    
    MANIFEST_TEMPLATE = '''# {name} - Project Manifest

name: {name}
description: "{description}"
version: "0.1.0"
status:
  stage: "planning"
  last_updated: "{created}T00:00:00Z"

type: {project_type}
created: "{created}"
author: "NHI System"

# Where this project is hosted (if deployed)
registration:
  registered: false
  vmid: null
  port: null

# Frontend Configuration (if applicable)
frontend:
  type: "nhi-native"
  personality: "{personality}"
  framework: "vanilla"
  build_required: false

# Dependencies
dependencies:
  api: []
  services: []  # TODO: Add services this project depends on

# Repository
repository:
  type: git
  url: null
  branch: main

# Documentation paths
docs:
  readme: docs/README.md
  architecture: docs/architecture.md

# Roadmap
roadmap:
  mvp:
    - "Initial implementation"
  v1:
    - "Feature expansion"
'''
    
    README_TEMPLATE = '''# {name}

> {description}

## 🚀 Quick Start

```bash
# TODO: Add startup instructions
```

## 📖 Documentation

- [Architecture](./architecture.md)

## 📊 Status

| Phase | Status | Notes |
|-------|--------|-------|
| Planning | ✅ | Manifest created |
| MVP | 🚧 | In progress |
'''

    ARCHITECTURE_TEMPLATE = '''# {name} - Architecture

> **Version:** 0.1  
> **Date:** {created}

## Overview

TODO: Describe the architecture of this project.

## Components

TODO: List main components.

## Data Flow

TODO: Describe how data flows through the system.
'''
    
    def __init__(self, projects_root: Path = None):
        self.projects_root = projects_root or self.PROJECTS_ROOT
        self.projects_root.mkdir(parents=True, exist_ok=True)
    
    def create_project(
        self,
        name: str,
        description: str = None,
        project_type: str = "web-app",
        personality: str = "system",
        init_git: bool = True
    ) -> dict:
        """
        Create a new project with standard NHI structure.
        
        Args:
            name: Project name (lowercase, hyphens)
            description: Project description
            project_type: One of web-app, api, cli, library, service
            personality: NHIDS personality (system, document, media)
            init_git: Initialize git repository
            
        Returns:
            Dict with created paths and status
        """
        project_path = self.projects_root / name
        
        if project_path.exists():
            return {
                "success": False,
                "error": f"Project '{name}' already exists at {project_path}"
            }
        
        description = description or f"NHI Project: {name}"
        created = date.today().isoformat()
        
        # Create directory structure
        dirs = [
            project_path / "src",
            project_path / "tests",
            project_path / "docs",
            project_path / ".agent" / "workflows"
        ]
        
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)
        
        # Create manifest
        manifest_content = self.MANIFEST_TEMPLATE.format(
            name=name,
            description=description,
            project_type=project_type,
            personality=personality,
            created=created
        )
        (project_path / "project_manifest.yaml").write_text(manifest_content)
        
        # Create README
        readme_content = self.README_TEMPLATE.format(
            name=name,
            description=description
        )
        (project_path / "docs" / "README.md").write_text(readme_content)
        
        # Create architecture.md
        arch_content = self.ARCHITECTURE_TEMPLATE.format(
            name=name,
            created=created
        )
        (project_path / "docs" / "architecture.md").write_text(arch_content)
        
        # Create .gitignore
        gitignore_content = '''# Python
__pycache__/
*.py[cod]
.venv/
venv/

# Node
node_modules/

# IDE
.vscode/
.idea/

# OS
.DS_Store
Thumbs.db

# Secrets (NEVER commit)
.env
*.key
'''
        (project_path / ".gitignore").write_text(gitignore_content)
        
        # Initialize git
        git_initialized = False
        if init_git:
            try:
                subprocess.run(
                    ["git", "init"],
                    cwd=project_path,
                    capture_output=True,
                    check=True
                )
                subprocess.run(
                    ["git", "add", "."],
                    cwd=project_path,
                    capture_output=True,
                    check=True
                )
                subprocess.run(
                    ["git", "commit", "-m", "Initial project scaffold"],
                    cwd=project_path,
                    capture_output=True,
                    check=True
                )
                git_initialized = True
            except Exception as e:
                git_initialized = False
        
        return {
            "success": True,
            "path": str(project_path),
            "files_created": [
                "project_manifest.yaml",
                "docs/README.md",
                "docs/architecture.md",
                ".gitignore",
                "src/",
                "tests/",
                ".agent/workflows/"
            ],
            "git_initialized": git_initialized
        }
    
    def list_projects(self) -> list:
        """List all projects in projects root."""
        projects = []
        for item in self.projects_root.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                has_manifest = (item / "project_manifest.yaml").exists()
                projects.append({
                    "name": item.name,
                    "path": str(item),
                    "has_manifest": has_manifest
                })
        return sorted(projects, key=lambda x: x['name'])
    
    def validate_project(self, name: str) -> dict:
        """Check if a project follows NHI standards."""
        project_path = self.projects_root / name
        
        if not project_path.exists():
            return {"valid": False, "errors": ["Project not found"]}
        
        result = {"valid": True, "errors": [], "warnings": []}
        
        # Required files
        required = [
            "project_manifest.yaml",
            "docs/README.md"
        ]
        
        for f in required:
            if not (project_path / f).exists():
                result["valid"] = False
                result["errors"].append(f"Missing required: {f}")
        
        # Recommended files
        recommended = [
            "docs/architecture.md",
            ".gitignore"
        ]
        
        for f in recommended:
            if not (project_path / f).exists():
                result["warnings"].append(f"Missing recommended: {f}")
        
        # Check git
        if not (project_path / ".git").exists():
            result["warnings"].append("Not a git repository")
        
        return result
