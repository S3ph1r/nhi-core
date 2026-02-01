"""
Dependency Resolver

Resolves transitive dependencies between services for backup planning.
Reads service manifests from registry and builds dependency graph.
"""

import yaml
import logging
from pathlib import Path
from typing import Dict, List, Set, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class DependencyResolver:
    """
    Resolves service dependencies for backup planning.
    
    Uses manifest files in registry to build dependency graph.
    Supports caching for performance.
    """
    
    # Services considered "infrastructure" - always included in core+infra
    INFRASTRUCTURE_SERVICES = {
        'postgresql', 'postgres', 'redis', 'minio', 
        'chromadb', 'rabbitmq', 'mongodb'
    }
    
    def __init__(
        self, 
        registry_path: str = "/var/lib/nhi/registry/services",
        cache_path: str = "/var/lib/nhi/cache",
        cache_ttl_seconds: int = 3600
    ):
        self.registry_path = Path(registry_path)
        self.cache_path = Path(cache_path)
        self.cache_file = self.cache_path / "dependency_graph.yaml"
        self.cache_ttl = timedelta(seconds=cache_ttl_seconds)
        
        # Ensure cache directory exists
        self.cache_path.mkdir(parents=True, exist_ok=True)
    
    def get_graph(self, force_rebuild: bool = False) -> Dict:
        """
        Get dependency graph, using cache if valid.
        
        Args:
            force_rebuild: Force rebuild even if cache is valid
            
        Returns:
            Dict mapping service names to their info and dependencies
        """
        if not force_rebuild and self._is_cache_valid():
            logger.debug("Using cached dependency graph")
            return self._load_cache()
        
        logger.info("Building dependency graph from manifests")
        return self._build_graph()
    
    def _is_cache_valid(self) -> bool:
        """Check if cache exists and is still fresh."""
        if not self.cache_file.exists():
            return False
        
        cache_mtime = datetime.fromtimestamp(self.cache_file.stat().st_mtime)
        return datetime.now() - cache_mtime < self.cache_ttl
    
    def _load_cache(self) -> Dict:
        """Load graph from cache file."""
        try:
            with open(self.cache_file, 'r') as f:
                data = yaml.safe_load(f)
                return data.get('graph', {})
        except Exception as e:
            logger.warning(f"Failed to load cache: {e}")
            return self._build_graph()
    
    def _save_cache(self, graph: Dict) -> None:
        """Save graph to cache file."""
        try:
            cache_data = {
                'generated': datetime.now().isoformat(),
                'ttl_seconds': self.cache_ttl.total_seconds(),
                'service_count': len(graph),
                'graph': graph
            }
            with open(self.cache_file, 'w') as f:
                yaml.dump(cache_data, f, default_flow_style=False)
            logger.debug(f"Saved dependency graph cache: {len(graph)} services")
        except Exception as e:
            logger.warning(f"Failed to save cache: {e}")
    
    def _build_graph(self) -> Dict:
        """
        Build dependency graph from all manifests in registry.
        
        Returns:
            Dict with structure:
            {
                'service-name': {
                    'vmid': 106,
                    'ip': '192.168.1.106',
                    'status': 'active',
                    'type': 'lxc',
                    'requires': ['postgresql', 'redis'],
                    'optional': ['chromadb'],
                    'is_infrastructure': False
                }
            }
        """
        graph = {}
        
        if not self.registry_path.exists():
            logger.warning(f"Registry path does not exist: {self.registry_path}")
            return graph
        
        for manifest_file in self.registry_path.glob("*.yaml"):
            try:
                with open(manifest_file, 'r') as f:
                    data = yaml.safe_load(f)
                
                if not data or 'name' not in data:
                    continue
                
                name = data['name']
                deps = data.get('dependencies', {})
                
                # Handle both old format (list) and new format (dict)
                if isinstance(deps, list):
                    required = deps
                    optional = []
                else:
                    required = deps.get('required', [])
                    optional = deps.get('optional', [])
                
                graph[name] = {
                    'vmid': data.get('vmid'),
                    'ip': data.get('network', {}).get('ip'),
                    'status': data.get('status', 'unknown'),
                    'type': data.get('type', 'lxc'),
                    'requires': required,
                    'optional': optional,
                    'is_infrastructure': name.lower() in self.INFRASTRUCTURE_SERVICES
                }
                
            except Exception as e:
                logger.error(f"Failed to parse manifest {manifest_file}: {e}")
                continue
        
        # Save to cache
        self._save_cache(graph)
        
        return graph
    
    def resolve(self, service_name: str, include_optional: bool = False) -> Set[str]:
        """
        Resolve all dependencies for a service (including transitive).
        
        Args:
            service_name: Name of service to resolve
            include_optional: Include optional dependencies
            
        Returns:
            Set of all service names this service depends on
        """
        graph = self.get_graph()
        resolved = set()
        to_resolve = [service_name]
        
        while to_resolve:
            current = to_resolve.pop(0)
            
            if current in resolved:
                continue
            
            resolved.add(current)
            
            if current in graph:
                service_info = graph[current]
                
                # Add required dependencies
                for dep in service_info.get('requires', []):
                    if dep not in resolved:
                        to_resolve.append(dep)
                
                # Optionally add optional dependencies
                if include_optional:
                    for dep in service_info.get('optional', []):
                        if dep not in resolved:
                            to_resolve.append(dep)
        
        return resolved
    
    def get_backup_targets(
        self,
        policy: str,
        include: Optional[List[str]] = None,
        exclude: Optional[List[str]] = None,
        include_status: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        Get list of services to backup based on policy.
        
        Args:
            policy: 'core' | 'core+infra' | 'selective' | 'all'
            include: Services to include (for 'selective' policy)
            exclude: Services to always exclude
            include_status: Only include services with these statuses
            
        Returns:
            List of dicts with service info and backup reason:
            [
                {'name': 'warroom', 'vmid': 106, 'ip': '...', 'reason': 'explicit'},
                {'name': 'postgresql', 'vmid': 105, 'ip': '...', 'reason': 'dependency of warroom'}
            ]
        """
        graph = self.get_graph()
        exclude = set(exclude or [])
        include_status = set(include_status or ['active', 'development', 'maintenance'])
        targets = {}
        
        # Always include nhi-core if it exists
        if 'nhi-core' in graph:
            targets['nhi-core'] = {
                **graph['nhi-core'],
                'name': 'nhi-core',
                'reason': 'core'
            }
        
        if policy == 'core':
            # Only NHI-CORE
            pass
        
        elif policy == 'core+infra':
            # Core + infrastructure services
            for name, info in graph.items():
                if info.get('is_infrastructure') and name not in exclude:
                    if info.get('status', 'active') in include_status:
                        targets[name] = {
                            **info,
                            'name': name,
                            'reason': 'infrastructure'
                        }
        
        elif policy == 'selective':
            # Specific services + their dependencies
            for service in (include or []):
                if service in exclude:
                    continue
                
                # Resolve all dependencies
                all_deps = self.resolve(service, include_optional=False)
                
                for dep in all_deps:
                    if dep in graph and dep not in exclude:
                        info = graph[dep]
                        if info.get('status', 'active') in include_status:
                            reason = 'explicit' if dep == service else f'dependency of {service}'
                            
                            # Don't override if already added with higher priority reason
                            if dep not in targets:
                                targets[dep] = {
                                    **info,
                                    'name': dep,
                                    'reason': reason
                                }
        
        elif policy == 'all':
            # Everything except excluded
            for name, info in graph.items():
                if name not in exclude:
                    if info.get('status', 'active') in include_status:
                        targets[name] = {
                            **info,
                            'name': name,
                            'reason': 'all'
                        }
        
        return list(targets.values())
    
    def invalidate_cache(self) -> None:
        """
        Invalidate the dependency graph cache.
        Call this after registering/updating services.
        """
        if self.cache_file.exists():
            self.cache_file.unlink()
            logger.info("Dependency graph cache invalidated")
    
    def get_infrastructure_services(self) -> List[str]:
        """Get list of registered infrastructure services."""
        graph = self.get_graph()
        return [name for name, info in graph.items() if info.get('is_infrastructure')]
    
    def print_graph(self) -> None:
        """Print dependency graph in human-readable format."""
        graph = self.get_graph()
        
        print(f"\n{'='*60}")
        print(f"NHI Dependency Graph - {len(graph)} services")
        print(f"{'='*60}\n")
        
        for name, info in sorted(graph.items()):
            status_icon = {
                'active': '✅',
                'development': '🔨',
                'maintenance': '🔧',
                'deprecated': '⚠️'
            }.get(info.get('status', ''), '❓')
            
            infra_tag = ' [INFRA]' if info.get('is_infrastructure') else ''
            
            print(f"{status_icon} {name}{infra_tag}")
            print(f"   VMID: {info.get('vmid')} | IP: {info.get('ip')}")
            
            if info.get('requires'):
                print(f"   Requires: {', '.join(info['requires'])}")
            if info.get('optional'):
                print(f"   Optional: {', '.join(info['optional'])}")
            print()


if __name__ == "__main__":
    # Test/demo
    resolver = DependencyResolver()
    resolver.print_graph()
