"""
Dependency Inference Module

Automatically discovers service dependencies by:
1. Scanning network connections (which ports services connect to)
2. Parsing config files for connection strings
3. Matching ports to known services
"""

import os
import re
import socket
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Set
import yaml


class DependencyInferrer:
    """Infers service dependencies from runtime and config analysis."""
    
    # Known service ports mapping
    KNOWN_PORTS = {
        5432: "postgres-lxc",
        3306: "mysql",
        6379: "redis",
        27017: "mongodb",
        8000: "chromadb-lxc",  # ChromaDB API
        9000: "minio-lxc",     # MinIO API
        9090: "observability", # Prometheus
        3000: "observability", # Grafana
        8080: "nhi-core",      # Generic API
    }
    
    # Config file patterns to search
    CONFIG_PATTERNS = [
        "*.yaml",
        "*.yml", 
        "*.json",
        "*.env",
        ".env*",
        "config.*",
        "docker-compose*.yml"
    ]
    
    # Regex patterns for connection strings
    CONNECTION_PATTERNS = [
        # PostgreSQL
        r'postgres(?:ql)?://[^@]+@([^:/]+):?(\d+)?',
        r'POSTGRES_HOST\s*[=:]\s*["\']?([^"\'\s]+)',
        r'DATABASE_URL.*@([^:/]+):(\d+)',
        # Redis
        r'redis://([^:/]+):?(\d+)?',
        r'REDIS_HOST\s*[=:]\s*["\']?([^"\'\s]+)',
        # Generic host:port
        r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(\d+)',
    ]
    
    def __init__(self):
        self.system_map = self._load_system_map()
        self.ip_to_service = self._build_ip_mapping()
        self._local_ip = None
    
    def _get_local_ip(self) -> str:
        """Get this machine's IP address."""
        if self._local_ip:
            return self._local_ip
        try:
            # Get the IP used for outbound connections
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            self._local_ip = s.getsockname()[0]
            s.close()
        except:
            self._local_ip = "127.0.0.1"
        return self._local_ip
    
    def _load_system_map(self) -> Dict:
        """Load system map for IP→service mapping."""
        path = Path("/var/lib/nhi/context/system-map.json")
        if path.exists():
            import json
            with open(path) as f:
                return json.load(f)
        return {"resources": []}
    
    def _build_ip_mapping(self) -> Dict[str, str]:
        """Build IP → service name mapping."""
        mapping = {}
        for resource in self.system_map.get("resources", []):
            ip = resource.get("ip")
            name = resource.get("name", "").lower()
            if ip:
                mapping[ip] = name
        return mapping
    
    def infer_from_config(self, project_path: str) -> Dict[str, List[str]]:
        """
        Scan project config files for connection strings.
        
        Returns:
            Dict with 'found_hosts', 'found_ports', 'inferred_services'
        """
        project = Path(project_path)
        if not project.exists():
            return {"error": f"Path {project_path} does not exist"}
        
        found_hosts: Set[str] = set()
        found_ports: Set[int] = set()
        inferred: Set[str] = set()
        
        # Search config files
        for pattern in self.CONFIG_PATTERNS:
            for config_file in project.rglob(pattern):
                # Skip node_modules, .git, etc.
                if any(skip in str(config_file) for skip in [
                    'node_modules', '.git', '__pycache__', 'venv'
                ]):
                    continue
                
                try:
                    content = config_file.read_text(errors='ignore')
                    
                    # Apply regex patterns
                    for pattern_re in self.CONNECTION_PATTERNS:
                        matches = re.findall(pattern_re, content, re.IGNORECASE)
                        for match in matches:
                            if isinstance(match, tuple):
                                host = match[0] if match[0] else None
                                port = int(match[1]) if len(match) > 1 and match[1] else None
                            else:
                                host = match
                                port = None
                            
                            if host:
                                found_hosts.add(host)
                                # Check if IP maps to known service
                                if host in self.ip_to_service:
                                    inferred.add(self.ip_to_service[host])
                            
                            if port:
                                found_ports.add(port)
                                # Check if port maps to known service
                                if port in self.KNOWN_PORTS:
                                    inferred.add(self.KNOWN_PORTS[port])
                                    
                except Exception:
                    pass
        
        return {
            "found_hosts": list(found_hosts),
            "found_ports": list(found_ports),
            "inferred_services": list(inferred),
            "confidence": "medium" if inferred else "low"
        }
    
    def infer_from_ports(self, service_ip: str) -> Dict[str, List[str]]:
        """
        Check which ports a service is connecting TO (outbound).
        
        Requires SSH access to the target machine.
        """
        connections: Set[str] = set()
        
        try:
            # Use ss to get established connections
            result = subprocess.run(
                ["ssh", f"ai-agent@{service_ip}", "ss -tn state established"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    # Parse ss output: State Recv-Q Send-Q Local Peer
                    parts = line.split()
                    if len(parts) >= 5:
                        peer = parts[4]  # Peer address:port
                        if ':' in peer:
                            ip, port = peer.rsplit(':', 1)
                            try:
                                port = int(port)
                                if port in self.KNOWN_PORTS:
                                    connections.add(self.KNOWN_PORTS[port])
                                elif ip in self.ip_to_service:
                                    connections.add(self.ip_to_service[ip])
                            except ValueError:
                                pass
        except Exception as e:
            return {"error": str(e)}
        
        return {
            "outbound_connections": list(connections),
            "confidence": "high" if connections else "none"
        }
    
    def infer_for_project(self, project_name: str) -> Dict:
        """
        Full inference for a project.
        
        Combines config parsing with runtime analysis.
        """
        projects_root = Path("/home/ai-agent/projects")
        project_path = projects_root / project_name
        
        result = {
            "project": project_name,
            "from_config": {},
            "from_runtime": {},
            "all_inferred": [],
            "recommendations": []
        }
        
        # Config-based inference
        if project_path.exists():
            result["from_config"] = self.infer_from_config(str(project_path))
        
        # Load project manifest to check current declarations
        manifest_path = project_path / "project_manifest.yaml"
        declared_deps = []
        if manifest_path.exists():
            with open(manifest_path) as f:
                manifest = yaml.safe_load(f) or {}
            declared_deps = manifest.get("dependencies", {}).get("services", [])
        
        # Combine all inferred
        all_inferred = set(result["from_config"].get("inferred_services", []))
        result["all_inferred"] = list(all_inferred)
        
        # Find undeclared dependencies
        undeclared = all_inferred - set(declared_deps)
        if undeclared:
            result["recommendations"].append({
                "type": "missing_declaration",
                "message": f"Found {len(undeclared)} undeclared dependencies",
                "services": list(undeclared),
                "action": "Add to project_manifest.yaml dependencies.services"
            })
        
        return result
    
    def infer_all_projects(self) -> List[Dict]:
        """Run inference on all projects."""
        results = []
        projects_root = Path("/home/ai-agent/projects")
        
        for project_dir in projects_root.iterdir():
            if project_dir.is_dir() and not project_dir.name.startswith('.'):
                result = self.infer_for_project(project_dir.name)
                results.append(result)
        
        return results
    
    def scan_service_runtime(self, service_name: str) -> Dict:
        """
        Scan a specific service's runtime connections via SSH.
        
        Returns detailed connection info including:
        - Outbound connections (what this service connects TO)
        - Listening ports (what ports this service exposes)
        - Inferred dependencies
        """
        # Find service IP from system map
        service_ip = None
        for resource in self.system_map.get("resources", []):
            name = resource.get("name", "").lower()
            if service_name.lower() in name or name in service_name.lower():
                service_ip = resource.get("ip")
                break
        
        if not service_ip:
            return {
                "service": service_name,
                "error": f"Could not find IP for service '{service_name}'",
                "status": "failed"
            }
        
        # Check if this is the local machine
        local_ip = self._get_local_ip()
        is_local = (service_ip == local_ip) or service_name.lower() in ["nhi-core", "nhi-core-v1.1"]
        
        result = {
            "service": service_name,
            "ip": service_ip,
            "status": "scanned",
            "scan_type": "local" if is_local else "ssh",
            "outbound": [],
            "listening": [],
            "inferred_dependencies": [],
            "raw_connections": []
        }
        
        try:
            # Command to get connections (ss -tn shows all TCP connections)
            cmd_str = "ss -tn 2>/dev/null; echo '---'; ss -tln 2>/dev/null"
            
            if is_local:
                # Run locally via shell
                proc = subprocess.run(
                    ["bash", "-c", cmd_str],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
            else:
                # Run via SSH
                proc = subprocess.run(
                    ["ssh", "-o", "ConnectTimeout=5", "-o", "StrictHostKeyChecking=no",
                     "-o", "BatchMode=yes", f"ai-agent@{service_ip}", cmd_str],
                    capture_output=True,
                    text=True,
                    timeout=15
                )
            
            if proc.returncode != 0 and not is_local:
                result["error"] = f"SSH failed: {proc.stderr[:100]}"
                result["status"] = "ssh_failed"
                return result
            
            # Parse output
            output = proc.stdout
            parts = output.split('---')
            established_output = parts[0] if len(parts) > 0 else ""
            listening_output = parts[1] if len(parts) > 1 else ""
            
            # Parse established connections (outbound to external services)
            for line in established_output.strip().split('\n'):
                # Look for ESTAB lines, skip header
                if 'State' in line or 'ESTAB' not in line:
                    continue
                cols = line.split()
                if len(cols) >= 5:
                    local = cols[3]
                    peer = cols[4]
                    
                    # Extract peer info
                    if ':' in peer:
                        peer_ip, peer_port = peer.rsplit(':', 1)
                        try:
                            peer_port = int(peer_port)
                            
                            # Skip localhost connections
                            if peer_ip.startswith("127.") or peer_ip == "::1":
                                continue
                            # Skip connections to self
                            if peer_ip == service_ip:
                                continue
                            
                            connection = {
                                "peer_ip": peer_ip,
                                "peer_port": peer_port,
                                "service": None
                            }
                            
                            # Identify the service
                            if peer_port in self.KNOWN_PORTS:
                                connection["service"] = self.KNOWN_PORTS[peer_port]
                            elif peer_ip in self.ip_to_service:
                                connection["service"] = self.ip_to_service[peer_ip]
                            
                            result["outbound"].append(connection)
                            result["raw_connections"].append(f"{peer_ip}:{peer_port}")
                            
                            if connection["service"]:
                                result["inferred_dependencies"].append(connection["service"])
                                
                        except ValueError:
                            pass
            
            # Parse listening ports
            for line in listening_output.strip().split('\n'):
                if not line or 'State' in line:
                    continue
                cols = line.split()
                if len(cols) >= 4:
                    local = cols[3]
                    if ':' in local:
                        _, port = local.rsplit(':', 1)
                        try:
                            port = int(port)
                            if port > 0 and port < 65536:
                                result["listening"].append(port)
                        except ValueError:
                            pass
            
            # Deduplicate
            result["inferred_dependencies"] = list(set(result["inferred_dependencies"]))
            result["listening"] = list(set(result["listening"]))
            
        except subprocess.TimeoutExpired:
            result["error"] = "SSH timeout"
            result["status"] = "timeout"
        except Exception as e:
            result["error"] = str(e)
            result["status"] = "error"
        
        return result
    
    def scan_all_services_runtime(self) -> Dict:
        """
        Scan all services in the infrastructure for runtime dependencies.
        
        Returns a comprehensive map of real-time connections.
        """
        results = {
            "scanned_at": subprocess.run(["date", "-Iseconds"], capture_output=True, text=True).stdout.strip(),
            "services": [],
            "dependency_matrix": {},
            "summary": {
                "total_services": 0,
                "scanned_successfully": 0,
                "total_connections": 0,
                "unique_dependencies": set()
            }
        }
        
        resources = self.system_map.get("resources", [])
        
        for resource in resources:
            name = resource.get("name", "unknown")
            ip = resource.get("ip")
            status = resource.get("status")
            
            # Skip VMs without IP or stopped services
            if not ip or status != "running":
                results["services"].append({
                    "service": name,
                    "status": "skipped",
                    "reason": "no IP or not running"
                })
                continue
            
            results["summary"]["total_services"] += 1
            
            # Scan this service
            scan_result = self.scan_service_runtime(name)
            results["services"].append(scan_result)
            
            if scan_result.get("status") == "scanned":
                results["summary"]["scanned_successfully"] += 1
                results["summary"]["total_connections"] += len(scan_result.get("outbound", []))
                
                deps = scan_result.get("inferred_dependencies", [])
                results["summary"]["unique_dependencies"].update(deps)
                
                # Build dependency matrix
                if deps:
                    results["dependency_matrix"][name] = deps
        
        # Convert set to list for JSON serialization
        results["summary"]["unique_dependencies"] = list(results["summary"]["unique_dependencies"])
        
        return results
