"""
Service Registry - Manifest Generator

Creates YAML manifests for deployed services and maintains the service registry.
"""

import os
import yaml
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class ManifestGenerator:
    """Generates and manages service manifests."""
    
    def __init__(self, base_path: str = "/var/lib/nhi"):
        self.base_path = Path(base_path)
        self.registry_path = self.base_path / "registry" / "services"
        self.schema_path = self.base_path / "schemas" / "service-manifest.json"
        
    def setup(self):
        """Initialize registry directories."""
        self.registry_path.mkdir(parents=True, exist_ok=True)
        (self.base_path / "schemas").mkdir(parents=True, exist_ok=True)
        
        # Create JSON Schema if not exists
        if not self.schema_path.exists():
            self._create_schema()
    
    def create_manifest(
        self,
        name: str,
        vmid: int,
        ip: str,
        container_type: str = "lxc",
        cpu: int = 2,
        memory_mb: int = 2048,
        disk_gb: int = 20,
        ports: Optional[List[Dict]] = None,
        dependencies: Optional[Dict] = None,
        mounts: Optional[List[Dict]] = None,
        description: str = ""
    ) -> Path:
        """
        Create a service manifest.
        
        Args:
            name: Service name (lowercase, alphanumeric + dash)
            vmid: Proxmox VM/Container ID
            ip: IP address
            container_type: 'lxc' or 'vm'
            cpu: CPU cores
            memory_mb: Memory in MB
            disk_gb: Disk size in GB
            ports: List of port dicts [{port, protocol, description}]
            dependencies: Dict with 'required' and 'optional' lists
            mounts: List of mount dicts [{source, target, type}]
            description: Service description
            
        Returns:
            Path to created manifest
        """
        now = datetime.now().isoformat()
        
        manifest = {
            'name': name,
            'description': description,
            'type': container_type,
            'vmid': vmid,
            
            'network': {
                'ip': ip,
                'ports': ports or []
            },
            
            'resources': {
                'cpu': cpu,
                'memory_mb': memory_mb,
                'disk_gb': disk_gb
            },
            
            'dependencies': dependencies or {'required': [], 'optional': []},
            
            'mounts': mounts or [],
            
            'healthcheck': {
                'type': 'tcp',
                'port': ports[0]['port'] if ports else None,
                'interval': 60
            },
            
            'checklist': {
                'lxc_created': True,
                'service_installed': False,
                'ports_configured': bool(ports),
                'manifest_created': True,
                'healthcheck_defined': bool(ports),
                'docs_updated': False
            },
            
            'created': now,
            'updated': now
        }
        
        # Save manifest
        manifest_path = self.registry_path / f"{name}.yaml"
        with open(manifest_path, 'w') as f:
            yaml.dump(manifest, f, default_flow_style=False, allow_unicode=True)
        
        logger.info(f"Created manifest: {manifest_path}")
        
        return manifest_path
    
    def update_manifest(self, name: str, updates: Dict) -> Path:
        """
        Update an existing manifest.
        
        Args:
            name: Service name
            updates: Dict of fields to update
            
        Returns:
            Path to updated manifest
        """
        manifest_path = self.registry_path / f"{name}.yaml"
        
        if not manifest_path.exists():
            raise FileNotFoundError(f"Manifest not found: {name}")
        
        with open(manifest_path, 'r') as f:
            manifest = yaml.safe_load(f)
        
        # Deep update
        self._deep_update(manifest, updates)
        manifest['updated'] = datetime.now().isoformat()
        
        with open(manifest_path, 'w') as f:
            yaml.dump(manifest, f, default_flow_style=False, allow_unicode=True)
        
        logger.info(f"Updated manifest: {manifest_path}")
        
        return manifest_path
    
    def _deep_update(self, base: Dict, updates: Dict):
        """Recursively update nested dict."""
        for key, value in updates.items():
            if isinstance(value, dict) and key in base and isinstance(base[key], dict):
                self._deep_update(base[key], value)
            else:
                base[key] = value
    
    def get_all_manifests(self) -> List[Dict]:
        """Get all service manifests."""
        manifests = []
        
        for manifest_file in self.registry_path.glob("*.yaml"):
            with open(manifest_file, 'r') as f:
                data = yaml.safe_load(f)
                data['_file'] = str(manifest_file)
                manifests.append(data)
        
        return manifests
    
    def generate_registry_index(self) -> Path:
        """Generate aggregated service registry."""
        manifests = self.get_all_manifests()
        
        registry = {
            'version': '1.0',
            'generated': datetime.now().isoformat(),
            'service_count': len(manifests),
            'services': {}
        }
        
        for m in manifests:
            registry['services'][m['name']] = {
                'vmid': m.get('vmid'),
                'ip': m.get('network', {}).get('ip'),
                'type': m.get('type'),
                'ports': [p.get('port') for p in m.get('network', {}).get('ports', [])],
                'status': 'unknown'  # Would be filled by healthcheck
            }
        
        index_path = self.base_path / "registry" / "service_registry.yaml"
        with open(index_path, 'w') as f:
            yaml.dump(registry, f, default_flow_style=False, allow_unicode=True)
        
        logger.info(f"Generated registry index: {index_path}")
        
        return index_path
    
    def _create_schema(self):
        """Create JSON Schema for manifest validation."""
        schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "title": "NHI Service Manifest",
            "type": "object",
            "required": ["name", "type", "vmid", "network", "resources"],
            "properties": {
                "name": {
                    "type": "string",
                    "pattern": "^[a-z][a-z0-9-]*$",
                    "description": "Service name (lowercase, alphanumeric + dash)"
                },
                "type": {
                    "enum": ["lxc", "vm"],
                    "description": "Container type"
                },
                "vmid": {
                    "type": "integer",
                    "minimum": 100,
                    "maximum": 999
                },
                "network": {
                    "type": "object",
                    "required": ["ip"],
                    "properties": {
                        "ip": {"type": "string", "format": "ipv4"},
                        "ports": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "required": ["port"],
                                "properties": {
                                    "port": {"type": "integer", "minimum": 1, "maximum": 65535},
                                    "protocol": {"enum": ["tcp", "udp"], "default": "tcp"},
                                    "description": {"type": "string"}
                                }
                            }
                        }
                    }
                },
                "resources": {
                    "type": "object",
                    "required": ["cpu", "memory_mb"],
                    "properties": {
                        "cpu": {"type": "integer", "minimum": 1, "maximum": 16},
                        "memory_mb": {"type": "integer", "minimum": 512, "maximum": 32768},
                        "disk_gb": {"type": "integer", "minimum": 8, "default": 20}
                    }
                },
                "dependencies": {
                    "type": "object",
                    "properties": {
                        "required": {"type": "array", "items": {"type": "string"}},
                        "optional": {"type": "array", "items": {"type": "string"}}
                    }
                }
            }
        }
        
        with open(self.schema_path, 'w') as f:
            json.dump(schema, f, indent=2)
        
        logger.info(f"Created JSON Schema: {self.schema_path}")
