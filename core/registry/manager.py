"""
Registry Manager - Service Registry CRUD Operations

Manages /var/lib/nhi/registry/services/*.yaml files with schema validation.
"""

import os
import yaml
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class RegistryManager:
    """Manages NHI service registry entries."""
    
    REGISTRY_PATH = Path("/var/lib/nhi/registry/services")
    SCHEMA_PATH = Path("/var/lib/nhi/schemas/service.schema.json")
    
    def __init__(self):
        self.registry_path = self.REGISTRY_PATH
        self.registry_path.mkdir(parents=True, exist_ok=True)
        self._schema = None
    
    @property
    def schema(self) -> Dict:
        """Load schema lazily."""
        if self._schema is None and self.SCHEMA_PATH.exists():
            with open(self.SCHEMA_PATH, 'r') as f:
                self._schema = json.load(f)
        return self._schema
    
    def list_services(self) -> List[str]:
        """List all registered service names."""
        services = []
        for f in self.registry_path.glob("*.yaml"):
            services.append(f.stem)
        return sorted(services)
    
    def get_service(self, name: str) -> Optional[Dict]:
        """Get service data by name."""
        path = self.registry_path / f"{name}.yaml"
        if not path.exists():
            return None
        with open(path, 'r') as f:
            return yaml.safe_load(f)
    
    def create_skeleton(self, name: str, vmid: int, ip: str = None, 
                        description: str = None) -> Path:
        """
        Create a skeleton registry entry for a new service.
        
        Args:
            name: Service name (lowercase, hyphens allowed)
            vmid: Proxmox VM/LXC ID
            ip: Optional IP address
            description: Optional description
            
        Returns:
            Path to created file
        """
        now = datetime.now().isoformat()
        
        skeleton = {
            "name": name,
            "description": description or f"Service {name} (auto-generated skeleton)",
            "type": "lxc",
            "vmid": vmid,
            "network": {
                "ip": ip or f"192.168.1.{vmid % 256}",
                "ports": []
            },
            "resources": {
                "cpu": 2,
                "memory_mb": 2048,
                "disk_gb": 8
            },
            "dependencies": {
                "required": [],
                "optional": []
            },
            "healthcheck": {
                "type": "tcp",
                "port": 22,
                "interval": 60
            },
            "created": now,
            "updated": now,
            "_status": "skeleton"  # Marker that this needs review
        }
        
        path = self.registry_path / f"{name}.yaml"
        
        # Add header comment
        content = f"""# NHI Service Registry: {name}
# Auto-generated skeleton - PLEASE REVIEW AND UPDATE
# Fields marked with TODO need your attention

{yaml.dump(skeleton, default_flow_style=False, sort_keys=False)}
"""
        
        with open(path, 'w') as f:
            f.write(content)
        
        return path
    
    def update_service(self, name: str, updates: Dict) -> bool:
        """Update specific fields of a service."""
        data = self.get_service(name)
        if data is None:
            return False
        
        # Deep merge updates
        def deep_merge(base, updates):
            for key, value in updates.items():
                if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                    deep_merge(base[key], value)
                else:
                    base[key] = value
        
        deep_merge(data, updates)
        data['updated'] = datetime.now().isoformat()
        
        # Remove status marker if present
        if '_status' in data:
            del data['_status']
        
        path = self.registry_path / f"{name}.yaml"
        with open(path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)
        
        return True
    
    def validate(self, name: str) -> Dict:
        """
        Validate a service registry entry against schema.
        
        Returns:
            Dict with 'valid', 'errors', and 'warnings'
        """
        data = self.get_service(name)
        if data is None:
            return {"valid": False, "errors": [f"Service {name} not found"]}
        
        result = {"valid": True, "errors": [], "warnings": []}
        
        # Check required fields from schema
        schema = self.schema
        if schema:
            required = schema.get('required', [])
            for field in required:
                if field not in data:
                    result["valid"] = False
                    result["errors"].append(f"Missing required field: {field}")
        
        # Check for skeleton marker
        if data.get('_status') == 'skeleton':
            result["warnings"].append("This is an auto-generated skeleton - needs review")
        
        # Check dependencies exist
        deps = data.get('dependencies', {})
        all_services = set(self.list_services())
        for dep in deps.get('required', []) + deps.get('optional', []):
            if dep not in all_services:
                result["warnings"].append(f"Dependency '{dep}' is not registered")
        
        return result
    
    def find_skeletons(self) -> List[str]:
        """Find services that are still skeleton (need review)."""
        skeletons = []
        for name in self.list_services():
            data = self.get_service(name)
            if data and data.get('_status') == 'skeleton':
                skeletons.append(name)
        return skeletons
    
    def delete_service(self, name: str) -> bool:
        """Delete a service registry entry."""
        path = self.registry_path / f"{name}.yaml"
        if path.exists():
            path.unlink()
            return True
        return False
