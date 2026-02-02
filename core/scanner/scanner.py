"""
Proxmox Scanner - Infrastructure Discovery

Connects to Proxmox VE API to enumerate VMs, containers, storage, and network.
"""

import os
import yaml
from typing import Dict, List, Optional
from proxmoxer import ProxmoxAPI
from core.security.sops_manager import SOPSManager


class ProxmoxScanner:
    """Client for discovering Proxmox infrastructure."""
    
    def __init__(self, config_path: str = "/var/lib/nhi/config.yaml"):
        """
        Initialize scanner with configuration.
        
        Args:
            config_path: Path to NHI config.yaml
        """
        self.config = self._load_config(config_path)
        self.proxmox = self._connect()
    
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML file."""
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Config not found: {config_path}")
        
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def _get_token_secret(self) -> str:
        """Read Proxmox token secret from secure storage."""
        data_path = self.config['paths']['data']
        
        # Try new v1.1 path first (YAML format)
        yaml_path = os.path.join(data_path, 'secrets', 'infrastructure', 'proxmox.yaml')
        if os.path.exists(yaml_path):
            try:
                sops = SOPSManager(data_path=data_path)
                secrets = sops.decrypt_file(yaml_path)
                if secrets and 'proxmox_token' in secrets:
                    return secrets['proxmox_token'].strip()
            except Exception:
                # Fallback if decryption fails (e.g. sops not installed)
                with open(yaml_path, 'r') as f:
                    secrets = yaml.safe_load(f)
                    if secrets and 'proxmox_token' in secrets:
                        return secrets['proxmox_token'].strip()
        
        # Fallback to legacy path (plain text)
        legacy_path = os.path.join(data_path, 'secrets', '.proxmox_token')
        if os.path.exists(legacy_path):
            with open(legacy_path, 'r') as f:
                return f.read().strip()
        
        raise FileNotFoundError(
            f"Proxmox token not found. Expected at:\n"
            f"  - {yaml_path} (v1.1 format)\n"
            f"  - {legacy_path} (legacy format)"
        )
    
    def _connect(self) -> ProxmoxAPI:
        """Establish connection to Proxmox API."""
        proxmox_config = self.config['proxmox']
        
        return ProxmoxAPI(
            host=proxmox_config['host'],
            port=proxmox_config.get('port', 8006),
            user=proxmox_config['token_id'].split('!')[0],
            token_name=proxmox_config['token_id'].split('!')[1],
            token_value=self._get_token_secret(),
            verify_ssl=proxmox_config.get('verify_ssl', False)
        )
    
    def get_nodes(self) -> List[Dict]:
        """
        Get all nodes in the Proxmox cluster.
        
        Returns:
            List of node dictionaries with status info
        """
        nodes = []
        for node in self.proxmox.nodes.get():
            node_info = {
                'name': node['node'],
                'status': node['status'],
                'cpu': node.get('cpu', 0),
                'maxcpu': node.get('maxcpu', 0),
                'mem': node.get('mem', 0),
                'maxmem': node.get('maxmem', 0),
                'uptime': node.get('uptime', 0)
            }
            nodes.append(node_info)
        return nodes
    
    def get_vms_and_containers(self) -> List[Dict]:
        """
        Get all VMs and LXC containers across all nodes.
        
        Returns:
            List of VM/container dictionaries
        """
        resources = []
        
        for node in self.proxmox.nodes.get():
            node_name = node['node']
            
            # Get QEMUs (VMs)
            try:
                for vm in self.proxmox.nodes(node_name).qemu.get():
                    config = {}
                    try:
                        config = self.proxmox.nodes(node_name).qemu(vm['vmid']).config.get()
                    except Exception:
                        pass
                    
                    resources.append({
                        'type': 'vm',
                        'vmid': vm['vmid'],
                        'name': vm.get('name', f"VM-{vm['vmid']}"),
                        'node': node_name,
                        'status': vm['status'],
                        'cpu': vm.get('cpus', config.get('cores', 0)),
                        'mem': vm.get('maxmem', 0),
                        'ip': self._extract_ip(config.get('net0', ''))
                    })
            except Exception:
                pass
            
            # Get LXCs (Containers)
            try:
                for lxc in self.proxmox.nodes(node_name).lxc.get():
                    config = {}
                    try:
                        config = self.proxmox.nodes(node_name).lxc(lxc['vmid']).config.get()
                    except Exception:
                        pass
                    
                    resources.append({
                        'type': 'lxc',
                        'vmid': lxc['vmid'],
                        'name': lxc.get('name', f"CT-{lxc['vmid']}"),
                        'node': node_name,
                        'status': lxc['status'],
                        'cpu': lxc.get('cpus', config.get('cores', 0)),
                        'mem': lxc.get('maxmem', 0),
                        'ip': self._extract_ip(config.get('net0', ''))
                    })
            except Exception:
                pass
        
        return resources
    
    def _extract_ip(self, net_config: str) -> Optional[str]:
        """Extract IP address from Proxmox network config string."""
        if not net_config:
            return None
        
        # Format: "name=eth0,bridge=vmbr0,ip=192.168.1.100/24,..."
        for part in net_config.split(','):
            if part.startswith('ip='):
                ip = part.split('=')[1]
                # Remove CIDR notation
                return ip.split('/')[0] if '/' in ip else ip
        return None
    
    def get_storage(self) -> List[Dict]:
        """
        Get all storage pools.
        
        Returns:
            List of storage dictionaries
        """
        storage = []
        
        for store in self.proxmox.storage.get():
            storage.append({
                'name': store['storage'],
                'type': store['type'],
                'content': store.get('content', ''),
                'shared': store.get('shared', 0) == 1
            })
        
        return storage
    
    def scan_network(self) -> Dict:
        """
        Scan network configuration.
        
        Returns:
            Dictionary with network info
        """
        network = {
            'bridges': [],
            'bonds': []
        }
        
        for node in self.proxmox.nodes.get():
            node_name = node['node']
            
            try:
                for iface in self.proxmox.nodes(node_name).network.get():
                    if iface['type'] == 'bridge':
                        network['bridges'].append({
                            'name': iface['iface'],
                            'node': node_name,
                            'address': iface.get('address'),
                            'gateway': iface.get('gateway')
                        })
                    elif iface['type'] == 'bond':
                        network['bonds'].append({
                            'name': iface['iface'],
                            'node': node_name,
                            'slaves': iface.get('slaves', '')
                        })
            except Exception:
                pass
        
        return network
    
    def scan_all(self) -> Dict:
        """
        Perform complete infrastructure scan.
        
        Returns:
            Dictionary with all infrastructure data
        """
        return {
            'timestamp': __import__('datetime').datetime.now().isoformat(),
            'nodes': self.get_nodes(),
            'resources': self.get_vms_and_containers(),
            'storage': self.get_storage(),
            'network': self.scan_network()
        }
    
    def save_infrastructure(self, output_path: str = "/var/lib/nhi/infrastructure.yaml"):
        """
        Scan and save infrastructure to YAML file.
        
        Args:
            output_path: Where to save the infrastructure data
        """
        data = self.scan_all()
        
        with open(output_path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
        
        return output_path
