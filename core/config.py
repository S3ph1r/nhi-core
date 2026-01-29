"""
NHI-CORE Configuration Module

Handles loading and validation of configuration.
"""

import os
import yaml
from typing import Dict, Optional
from dataclasses import dataclass


@dataclass
class ProxmoxConfig:
    """Proxmox connection configuration."""
    host: str
    port: int = 8006
    token_id: str = ""
    verify_ssl: bool = False


@dataclass
class PathsConfig:
    """Path configuration."""
    data: str = "/var/lib/nhi"
    logs: str = "/var/log/nhi"
    home: str = "/opt/nhi-core"


@dataclass
class NHIConfig:
    """Main NHI configuration."""
    proxmox: ProxmoxConfig
    paths: PathsConfig
    github_repo: str = ""
    domain_suffix: str = ".home"


def load_config(config_path: str = "/var/lib/nhi/config.yaml") -> NHIConfig:
    """
    Load and validate NHI configuration.
    
    Args:
        config_path: Path to config.yaml
    
    Returns:
        NHIConfig object
    
    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If config is invalid
    """
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config not found: {config_path}")
    
    with open(config_path, 'r') as f:
        raw = yaml.safe_load(f)
    
    # Parse Proxmox config
    proxmox_raw = raw.get('proxmox', {})
    proxmox = ProxmoxConfig(
        host=proxmox_raw.get('host', 'localhost'),
        port=proxmox_raw.get('port', 8006),
        token_id=proxmox_raw.get('token_id', ''),
        verify_ssl=proxmox_raw.get('verify_ssl', False)
    )
    
    # Parse paths config
    paths_raw = raw.get('paths', {})
    paths = PathsConfig(
        data=paths_raw.get('data', '/var/lib/nhi'),
        logs=paths_raw.get('logs', '/var/log/nhi'),
        home=paths_raw.get('home', '/opt/nhi-core')
    )
    
    return NHIConfig(
        proxmox=proxmox,
        paths=paths,
        github_repo=raw.get('github', {}).get('repo', ''),
        domain_suffix=raw.get('network', {}).get('domain_suffix', '.home')
    )


def get_secret(name: str, secrets_path: str = "/var/lib/nhi/secrets") -> Optional[str]:
    """
    Get a secret value from file.
    
    Args:
        name: Secret name (without leading dot)
        secrets_path: Path to secrets directory
    
    Returns:
        Secret value or None
    """
    secret_file = os.path.join(secrets_path, f".{name}")
    
    if os.path.exists(secret_file):
        with open(secret_file, 'r') as f:
            return f.read().strip()
    
    return None
