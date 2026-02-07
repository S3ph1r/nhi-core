"""
Backup Manager

Orchestrates backup operations using Proxmox API.
Supports local (NFS) and cloud storage backends.
"""

import os
import yaml
import json
import logging
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import urllib.request
import urllib.parse
import ssl

from .dependency_resolver import DependencyResolver

logger = logging.getLogger(__name__)


@dataclass
class BackupResult:
    """Result of a backup operation."""
    success: bool
    vmid: int
    name: str
    message: str
    backup_file: Optional[str] = None
    size_bytes: Optional[int] = None
    duration_seconds: Optional[float] = None


class ProxmoxAPI:
    """
    Simple Proxmox API client.
    Uses existing token from NHI config.
    """
    
    def __init__(self, config_path: str = "/var/lib/nhi/config.yaml"):
        self.config = self._load_config(config_path)
        self.host = self.config.get('proxmox', {}).get('host', '192.168.1.2')
        self.token_id = self.config.get('proxmox', {}).get('token_id')
        self.token_secret = self.config.get('proxmox', {}).get('token_secret')
        self.node = self.config.get('proxmox', {}).get('node', 'pve')
        
        # SSL context (ignore self-signed certs)
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE
    
    def _load_config(self, path: str) -> Dict:
        """Load NHI config."""
        try:
            with open(path, 'r') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return {}
    
    def _request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """Make API request to Proxmox."""
        url = f"https://{self.host}:8006/api2/json{endpoint}"
        
        headers = {
            'Authorization': f'PVEAPIToken={self.token_id}={self.token_secret}'
        }
        
        if data:
            data = urllib.parse.urlencode(data).encode('utf-8')
        
        request = urllib.request.Request(url, data=data, headers=headers, method=method)
        
        try:
            with urllib.request.urlopen(request, context=self.ssl_context, timeout=300) as response:
                return json.loads(response.read().decode('utf-8'))
        except Exception as e:
            logger.error(f"Proxmox API error: {e}")
            raise
    
    def get(self, endpoint: str) -> Dict:
        """GET request."""
        return self._request('GET', endpoint)
    
    def post(self, endpoint: str, data: Dict) -> Dict:
        """POST request."""
        return self._request('POST', endpoint, data)
    
    def backup_vm(self, vmid: int, storage: str, mode: str = 'snapshot', 
                  compress: str = 'zstd') -> Dict:
        """
        Trigger backup of VM/LXC.
        
        Args:
            vmid: VM/Container ID
            storage: Storage ID for backup destination
            mode: 'snapshot', 'suspend', or 'stop'
            compress: 'zstd', 'lzo', 'gzip', or '0'
        """
        endpoint = f"/nodes/{self.node}/vzdump"
        data = {
            'vmid': str(vmid),
            'storage': storage,
            'mode': mode,
            'compress': compress,
            'notes-template': f'NHI Backup - {{{{guestname}}}} - {datetime.now().isoformat()}'
        }
        
        return self.post(endpoint, data)
    
    def list_backups(self, storage: str) -> List[Dict]:
        """List backups on storage."""
        endpoint = f"/nodes/{self.node}/storage/{storage}/content"
        result = self.get(endpoint)
        
        backups = []
        for item in result.get('data', []):
            if item.get('content') == 'backup':
                backups.append(item)
        
        return backups
    
    def restore_backup(self, vmid: int, backup_volid: str, 
                       target_vmid: Optional[int] = None) -> Dict:
        """
        Restore a backup.
        
        Args:
            vmid: Original VMID (for LXC detection)
            backup_volid: Volume ID of backup (e.g., 'local:backup/vzdump-lxc-117-...')
            target_vmid: Optional different VMID for restore (for testing)
        """
        target = target_vmid or vmid
        
        # Determine if LXC or VM from backup filename
        if 'lxc' in backup_volid.lower():
            endpoint = f"/nodes/{self.node}/lxc"
        else:
            endpoint = f"/nodes/{self.node}/qemu"
        
        data = {
            'vmid': str(target),
            'ostemplate' if 'lxc' in backup_volid.lower() else 'archive': backup_volid,
            'restore': '1',
            'force': '1'  # Overwrite if exists
        }
        
        return self.post(endpoint, data)
    
    def get_vm_status(self, vmid: int, vm_type: str = 'lxc') -> Dict:
        """Get VM/LXC status."""
        endpoint = f"/nodes/{self.node}/{vm_type}/{vmid}/status/current"
        return self.get(endpoint)


class BackupManager:
    """
    Manages backup operations for NHI services.
    """
    
    def __init__(self, config_path: str = "/var/lib/nhi/config.yaml"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.resolver = DependencyResolver()
        self.api = ProxmoxAPI(str(config_path))
    
    def _load_config(self) -> Dict:
        """Load backup configuration."""
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f) or {}
                return config.get('backup', {})
        except Exception as e:
            logger.warning(f"Failed to load config: {e}")
            return {}
    
    def _save_config(self, backup_config: Dict) -> None:
        """Save backup configuration back to config.yaml."""
        try:
            with open(self.config_path, 'r') as f:
                full_config = yaml.safe_load(f) or {}
            
            full_config['backup'] = backup_config
            
            with open(self.config_path, 'w') as f:
                yaml.dump(full_config, f, default_flow_style=False)
            
            self.config = backup_config
            logger.info("Backup configuration saved")
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            raise
    
    def is_enabled(self) -> bool:
        """Check if backup is enabled."""
        return self.config.get('enabled', False)
    
    def enable(self, storage_type: str = None, storage_path: str = None) -> bool:
        """
        Enable backup functionality.
        
        Args:
            storage_type: 'nfs', 'local', 's3', etc (can be set later)
            storage_path: Path/URL for storage (can be set later)
        """
        backup_config = self.config.copy()
        backup_config['enabled'] = True
        
        if storage_type:
            backup_config.setdefault('storage', {})
            backup_config['storage']['primary'] = {
                'type': storage_type,
                'path': storage_path
            }
        
        self._save_config(backup_config)
        return True
    
    def disable(self) -> bool:
        """Disable backup functionality."""
        backup_config = self.config.copy()
        backup_config['enabled'] = False
        self._save_config(backup_config)
        return True
    
    def get_targets(self) -> List[Dict]:
        """Get list of backup targets based on current policy."""
        policy = self.config.get('policy', {}).get('mode', 'core+infra')
        include = self.config.get('policy', {}).get('include', [])
        exclude = self.config.get('policy', {}).get('exclude', [])
        include_status = self.config.get('policy', {}).get('include_status', 
                                                            ['active', 'development', 'maintenance'])
        
        return self.resolver.get_backup_targets(
            policy=policy,
            include=include,
            exclude=exclude,
            include_status=include_status
        )
    
    def add_service(self, service_name: str) -> Dict:
        """
        Add a service to backup policy (selective mode).
        Returns info about what will be backed up (including dependencies).
        """
        # Get all dependencies
        all_deps = self.resolver.resolve(service_name, include_optional=False)
        
        # Update config
        backup_config = self.config.copy()
        backup_config.setdefault('policy', {})
        backup_config['policy']['mode'] = 'selective'
        
        include = set(backup_config['policy'].get('include', []))
        include.add(service_name)
        backup_config['policy']['include'] = list(include)
        
        self._save_config(backup_config)
        
        return {
            'service': service_name,
            'dependencies': list(all_deps - {service_name}),
            'total_targets': len(all_deps)
        }
    
    def remove_service(self, service_name: str) -> bool:
        """Remove a service from backup policy."""
        backup_config = self.config.copy()
        include = backup_config.get('policy', {}).get('include', [])
        
        if service_name in include:
            include.remove(service_name)
            backup_config['policy']['include'] = include
            self._save_config(backup_config)
            return True
        
        return False
    
    def backup_now(self, storage: str = None) -> List[BackupResult]:
        """
        Execute backup immediately.
        
        Args:
            storage: Proxmox storage ID (uses config default if not specified)
        """
        if not self.is_enabled():
            raise RuntimeError("Backup is not enabled. Run 'nhi backup enable' first.")
        
        storage = storage or self.config.get('storage', {}).get('primary', {}).get('proxmox_storage')
        
        if not storage:
            raise RuntimeError("No storage configured. Set backup.storage.primary.proxmox_storage in config.yaml")
        
        targets = self.get_targets()
        
        if not targets:
            logger.warning("No backup targets found")
            return []
        
        results = []
        
        for target in targets:
            vmid = target.get('vmid')
            name = target.get('name')
            
            if not vmid:
                logger.warning(f"Skipping {name}: no VMID")
                continue
            
            logger.info(f"Backing up {name} (VMID {vmid})...")
            start_time = datetime.now()
            
            try:
                response = self.api.backup_vm(vmid, storage)
                
                duration = (datetime.now() - start_time).total_seconds()
                
                results.append(BackupResult(
                    success=True,
                    vmid=vmid,
                    name=name,
                    message=f"Backup queued: {response.get('data', '')}",
                    duration_seconds=duration
                ))
                
                logger.info(f"Backup queued for {name}")
                
            except Exception as e:
                results.append(BackupResult(
                    success=False,
                    vmid=vmid,
                    name=name,
                    message=str(e)
                ))
                logger.error(f"Backup failed for {name}: {e}")
        
        return results
    
    def list_backups(self, storage: str = None) -> List[Dict]:
        """List available backups."""
        storage = storage or self.config.get('storage', {}).get('primary', {}).get('proxmox_storage')
        
        if not storage:
            return []
        
        return self.api.list_backups(storage)
    
    def status(self) -> Dict:
        """Get backup status summary."""
        targets = self.get_targets() if self.is_enabled() else []
        storage = self.config.get('storage', {}).get('primary', {})
        
        return {
            'enabled': self.is_enabled(),
            'policy': self.config.get('policy', {}).get('mode', 'core+infra'),
            'targets': [{'name': t['name'], 'vmid': t.get('vmid'), 'reason': t.get('reason')} 
                       for t in targets],
            'target_count': len(targets),
            'storage': {
                'type': storage.get('type'),
                'configured': bool(storage.get('type'))
            },
            'schedule': self.config.get('schedule', {}),
            'last_backup': self.config.get('last_backup'),
            'retention': self.config.get('retention', {})
        }

    def get_policy_matrix(self) -> List[Dict]:
        """
        Returns the full matrix of services and their backup capabilities.
        Used by the Dashboard frontend.
        """
        graph = self.resolver.get_graph()
        matrix = []
        
        for name, info in graph.items():
            backup_meta = info.get('backup', {})
            svc_type = info.get('type', 'lxc')
            
            # Use appropriate prefix for ID
            prefix = 'prj' if svc_type == 'project' else 'svc'
            target_id = f"{prefix}_{name}"
            
            # Policy from config (if any)
            # We look in 'services' or 'projects' section of config
            config_section = 'projects' if svc_type == 'project' else 'services'
            policy = self.config.get(config_section, {}).get(target_id, {})
            
            item = {
                'id': target_id,
                'name': name,
                'type': svc_type,
                'has_persistence': bool(backup_meta.get('persistence')),
                'backup': {
                    'target': policy.get('target', 'none'),
                    'scope': policy.get('scope', 'full' if not backup_meta.get('persistence') else 'hybrid'),
                    'frequency': policy.get('frequency', 'daily' if svc_type == 'lxc' else 'weekly'),
                    'last_run': policy.get('last_run', 'N/A'),
                    'size': policy.get('size', 'N/A')
                }
            }
            
            # Projects have paths, LXCs have VMIDs
            if svc_type == 'project':
                item['path'] = info.get('path')
            else:
                item['vmid'] = info.get('vmid')
                
            matrix.append(item)
            
        return matrix

    def run_phoenix_backup(self, target_id: str) -> BackupResult:
        """
        Execute a Data Only (Phoenix) backup.
        Extracts only persistence paths defined in manifest.
        """
        # Identify target
        matrix = self.get_policy_matrix()
        target = next((item for item in matrix if item['id'] == target_id), None)
        
        if not target:
            raise ValueError(f"Target {target_id} not found")
            
        name = target['name']
        vmid = target.get('vmid')
        is_project = target['type'] == 'project'
        
        # Get persistence paths from manifest
        persistence = []
        if is_project:
            manifest_path = Path(target['path']) / "project_manifest.yaml"
        else:
            manifest_path = Path(f"/var/lib/nhi/registry/services/{name}.yaml")
            
        try:
            with open(manifest_path, 'r') as f:
                data = yaml.safe_load(f) or {}
                persistence = data.get('backup', {}).get('persistence', [])
                exclude = data.get('backup', {}).get('exclude', [])
        except Exception as e:
            return BackupResult(False, vmid or 0, name, f"Failed to read manifest: {e}")
            
        if not persistence:
            return BackupResult(False, vmid or 0, name, "No persistence paths defined for Phoenix backup")
            
        # Target archive
        temp_dir = Path("/tmp/nhi_backups")
        temp_dir.mkdir(exist_ok=True)
        archive_name = f"phoenix_{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.tar.gz"
        archive_path = temp_dir / archive_name
        
        try:
            if is_project:
                # Local project on host
                cmd = ["tar", "-czf", str(archive_path)]
                for ex in exclude:
                    cmd.extend(["--exclude", ex])
                cmd.extend(persistence)
                
                logger.info(f"Creating project backup: {' '.join(cmd)}")
                subprocess.run(cmd, check=True, cwd=target['path'])
            else:
                # LXC - Need to pull data
                # This is more complex if not on host. Assuming we can use pct pull
                # First tar inside LXC
                remote_tmp = f"/tmp/{archive_name}"
                tar_cmd = ["tar", "-czf", remote_tmp]
                for ex in exclude:
                    tar_cmd.extend(["--exclude", ex])
                tar_cmd.extend(persistence)
                
                # Execute in LXC via Proxmox node (requires SSH or API)
                # For MVP, assuming we can reach proxmox node via SSH or API.
                # Let's use a placeholder for the actual extraction logic if not on-node.
                # If we are on 160 (container) and target is 105, we need the node 192.168.1.2.
                
                return BackupResult(False, vmid, name, "LXC Data Extraction requires Proxmox Node Access (SSH/API implementation pending)")
                
            # TODO: Transport to real storage (SMB/Rclone)
            
            return BackupResult(
                success=True,
                vmid=vmid or 0,
                name=name,
                message=f"Phoenix backup successful: {archive_name}",
                backup_file=str(archive_path),
                size_bytes=archive_path.stat().st_size
            )
            
        except Exception as e:
            return BackupResult(False, vmid or 0, name, f"Phoenix backup failed: {e}")

    
    def restore(self, vmid: int, backup_id: str, target_vmid: Optional[int] = None) -> bool:
        """
        Restore a backup.
        
        Args:
            vmid: Original VMID
            backup_id: Backup volume ID
            target_vmid: Optional different VMID for restore
        """
        try:
            self.api.restore_backup(vmid, backup_id, target_vmid)
            return True
        except Exception as e:
            logger.error(f"Restore failed: {e}")
            return False


if __name__ == "__main__":
    # Test/demo
    manager = BackupManager()
    print(json.dumps(manager.status(), indent=2))
