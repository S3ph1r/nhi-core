"""
Context Generator - AI Context File Generation

Produces .cursorrules (Markdown) and system-map.json for AI assistants.
UPDATED v1.1: Generates dynamic .cursorrules that references JSON SSOT.
"""

import os
import json
import yaml
from datetime import datetime
from typing import Dict, List, Optional


class ContextGenerator:
    """Generates AI context files from infrastructure data."""
    
    PORT_STANDARDS = {
        '80, 443': 'Reverse Proxy (Traefik/Nginx)',
        '5432': 'PostgreSQL (Shared DB)',
        '6379': 'Redis (Shared Cache)',
        '8000-8999': 'Applicazioni Python/FastAPI',
        '3000-3999': 'Applicazioni Node.js',
        '9000-9099': 'Monitoring (Prometheus/Grafana)'
    }
    
    def __init__(self, infrastructure: Dict = None, data_path: str = "/var/lib/nhi"):
        self.data_path = data_path
        self.context_path = os.path.join(data_path, 'context')
        self.infrastructure = infrastructure or self._load_infrastructure()
    
    def _load_infrastructure(self) -> Dict:
        infra_path = os.path.join(self.data_path, 'infrastructure.yaml')
        if os.path.exists(infra_path):
            with open(infra_path, 'r') as f:
                return yaml.safe_load(f)
        return {'resources': [], 'nodes': [], 'storage': [], 'network': {}}
    
    def _load_config(self) -> Dict:
        config_path = os.path.join(self.data_path, 'config.yaml')
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        return {}
    
    def generate_cursorrules(self) -> str:
        """
        Generate .cursorrules Markdown content.
        Uses the static template from core/templates/cursorrules_template.md.
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
        
        # Resolve template path
        # Assuming current file is in core/context/generator.py
        # Template is in core/templates/cursorrules_template.md
        current_dir = os.path.dirname(os.path.abspath(__file__))
        template_path = os.path.join(current_dir, '..', 'templates', 'cursorrules_template.md')
        
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Simple variable substitution
            content = content.replace('{timestamp}', timestamp)
            return content
            
        except FileNotFoundError:
            # Fallback if template is missing (fail-safe)
            return f"# NHI Rules (Fallback)\nGenerated: {timestamp}\n\nERROR: Template not found at {template_path}"

    def generate_system_map(self) -> Dict:
        config = self._load_config()
        
        system_map = {
            'version': '1.1',
            'generated': datetime.now().isoformat(),
            'proxmox': {
                'host': config.get('proxmox', {}).get('host', 'unknown'),
                'port': config.get('proxmox', {}).get('port', 8006)
            },
            'nodes': self.infrastructure.get('nodes', []),
            'resources': self.infrastructure.get('resources', []),
            'storage': self.infrastructure.get('storage', []),
            'network': self.infrastructure.get('network', {}),
            'port_standards': self.PORT_STANDARDS
        }
        return system_map
    
    def generate(self):
        """Generate all context files."""
        os.makedirs(self.context_path, exist_ok=True)
        
        # Generate .cursorrules
        cursorrules_content = self.generate_cursorrules()
        cursorrules_path = os.path.join(self.context_path, '.cursorrules')
        with open(cursorrules_path, 'w', encoding='utf-8') as f:
            f.write(cursorrules_content)
        
        # Generate system-map.json
        system_map = self.generate_system_map()
        system_map_path = os.path.join(self.context_path, 'system-map.json')
        with open(system_map_path, 'w', encoding='utf-8') as f:
            json.dump(system_map, f, indent=2, ensure_ascii=False)
        
        return {
            'cursorrules': cursorrules_path,
            'system_map': system_map_path
        }
