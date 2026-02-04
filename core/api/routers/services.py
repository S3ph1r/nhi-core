from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict
import os
import yaml
from pathlib import Path
from core.scanner import ProxmoxScanner

router = APIRouter()

PROJECTS_ROOT = Path("/home/ai-agent/projects")
SYSTEM_MAP_PATH = "/var/lib/nhi/context/system-map.json"

class ServiceActionResponse(BaseModel):
    status: str
    message: str
    vmid: int

def get_project_linkages() -> Dict:
    """
    Scan projects and build linkage maps:
    - hosting: vmid -> project (project runs ON this service)
    - consuming: vmid -> [projects] (projects that DEPEND on this service)
    """
    hosting = {}      # vmid -> project_name
    consuming = {}    # service_name -> [project_names]
    
    if not PROJECTS_ROOT.exists():
        return {'hosting': hosting, 'consuming': consuming}
    
    for item in PROJECTS_ROOT.iterdir():
        if not item.is_dir() or item.name.startswith('.'):
            continue
            
        manifest_path = item / "project_manifest.yaml"
        if not manifest_path.exists():
            continue
            
        try:
            with open(manifest_path, 'r') as f:
                manifest = yaml.safe_load(f) or {}
            
            project_name = manifest.get('name', item.name)
            
            # Hosting: project declares it runs on vmid X
            reg = manifest.get('registration', {})
            if reg and reg.get('vmid'):
                hosting[reg['vmid']] = project_name
            
            # Consuming: project depends on services
            deps = manifest.get('dependencies', {})
            for svc in deps.get('services', []):
                if svc not in consuming:
                    consuming[svc] = []
                consuming[svc].append(project_name)
                
        except Exception:
            pass
    
    return {'hosting': hosting, 'consuming': consuming}

@router.get("/")
async def list_services():
    """Get all services with project linkage info."""
    import json
    
    # Load resources from SSOT
    resources = []
    if os.path.exists(SYSTEM_MAP_PATH):
        try:
            with open(SYSTEM_MAP_PATH, 'r') as f:
                data = json.load(f)
                resources = data.get('resources', [])
        except Exception:
            pass
    
    # Get project linkages
    linkages = get_project_linkages()
    
    # Enrich resources with linkage info
    enriched = []
    for r in resources:
        item = dict(r)
        vmid = r.get('vmid')
        name = r.get('name', '')
        
        # Hosting relationship
        if vmid in linkages['hosting']:
            item['hosts_project'] = linkages['hosting'][vmid]
        
        # Consuming relationship (by name match)
        if name in linkages['consuming']:
            item['used_by'] = linkages['consuming'][name]
        
        enriched.append(item)
    
    return {'services': enriched}

@router.post("/{vmid}/start", response_model=ServiceActionResponse)
async def start_service(vmid: int):
    """Start an LXC container or VM."""
    try:
        scanner = ProxmoxScanner()
        result = scanner.perform_action(vmid, 'start')
        
        if result['status'] == 'error':
            raise HTTPException(status_code=500, detail=result['message'])
        
        return {
            "status": result['status'],
            "message": result['message'],
            "vmid": vmid
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{vmid}/stop", response_model=ServiceActionResponse)
async def stop_service(vmid: int):
    """Stop an LXC container or VM."""
    try:
        scanner = ProxmoxScanner()
        result = scanner.perform_action(vmid, 'stop')
        
        if result['status'] == 'error':
            raise HTTPException(status_code=500, detail=result['message'])
        
        return {
            "status": result['status'],
            "message": result['message'],
            "vmid": vmid
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{vmid}/reboot", response_model=ServiceActionResponse)
async def reboot_service(vmid: int):
    """Reboot an LXC container or VM."""
    try:
        scanner = ProxmoxScanner()
        result = scanner.perform_action(vmid, 'reboot')
        
        if result['status'] == 'error':
            raise HTTPException(status_code=500, detail=result['message'])
        
        return {
            "status": result['status'],
            "message": result['message'],
            "vmid": vmid
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


REGISTRY_PATH = Path("/var/lib/nhi/registry/services")

@router.get("/dependencies")
async def get_dependencies():
    """
    Get dependency graph in Cytoscape.js format.
    Returns nodes (services + projects) and edges (dependencies).
    """
    import json
    
    nodes = []
    edges = []
    node_ids = set()
    
    # 1. Load services from system-map (Proxmox)
    services = []
    if os.path.exists(SYSTEM_MAP_PATH):
        try:
            with open(SYSTEM_MAP_PATH, 'r') as f:
                data = json.load(f)
                services = data.get('resources', [])
        except Exception:
            pass
    
    # Add service nodes
    for svc in services:
        node_id = svc.get('name', f"vmid-{svc.get('vmid')}")
        status = svc.get('status', 'unknown')
        node_type = svc.get('type', 'lxc')
        
        nodes.append({
            "data": {
                "id": node_id,
                "label": node_id,
                "type": "service",
                "subtype": node_type,
                "status": status,
                "vmid": svc.get('vmid')
            }
        })
        node_ids.add(node_id)
    
    # 2. Load dependencies from Registry
    if REGISTRY_PATH.exists():
        for yaml_file in REGISTRY_PATH.glob("*.yaml"):
            try:
                with open(yaml_file, 'r') as f:
                    reg = yaml.safe_load(f) or {}
                
                svc_name = reg.get('name')
                if not svc_name:
                    continue
                
                deps = reg.get('dependencies', {})
                for dep in deps.get('required', []):
                    edges.append({
                        "data": {
                            "source": svc_name,
                            "target": dep,
                            "type": "required"
                        }
                    })
                    # Ensure target node exists
                    if dep not in node_ids:
                        nodes.append({
                            "data": {
                                "id": dep,
                                "label": dep,
                                "type": "service",
                                "status": "unknown"
                            }
                        })
                        node_ids.add(dep)
                        
                for dep in deps.get('optional', []):
                    edges.append({
                        "data": {
                            "source": svc_name,
                            "target": dep,
                            "type": "optional"
                        }
                    })
                    if dep not in node_ids:
                        nodes.append({
                            "data": {
                                "id": dep,
                                "label": dep,
                                "type": "service",
                                "status": "unknown"
                            }
                        })
                        node_ids.add(dep)
                        
            except Exception:
                pass
    
    # 3. Load project dependencies (Project → Service)
    if PROJECTS_ROOT.exists():
        for item in PROJECTS_ROOT.iterdir():
            if not item.is_dir() or item.name.startswith('.'):
                continue
            
            manifest_path = item / "project_manifest.yaml"
            if not manifest_path.exists():
                continue
            
            try:
                with open(manifest_path, 'r') as f:
                    manifest = yaml.safe_load(f) or {}
                
                project_name = manifest.get('name', item.name)
                
                # Add project as node
                if project_name not in node_ids:
                    nodes.append({
                        "data": {
                            "id": project_name,
                            "label": project_name,
                            "type": "project",
                            "status": "active"
                        }
                    })
                    node_ids.add(project_name)
                
                # Project depends on services
                deps = manifest.get('dependencies', {})
                for svc in deps.get('services', []):
                    edges.append({
                        "data": {
                            "source": project_name,
                            "target": svc,
                            "type": "uses"
                        }
                    })
                    # Ensure service node exists
                    if svc not in node_ids:
                        nodes.append({
                            "data": {
                                "id": svc,
                                "label": svc,
                                "type": "service",
                                "status": "unknown"
                            }
                        })
                        node_ids.add(svc)
                        
            except Exception:
                pass
    
    return {
        "nodes": nodes,
        "edges": edges,
        "stats": {
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "services": len([n for n in nodes if n['data']['type'] == 'service']),
            "projects": len([n for n in nodes if n['data']['type'] == 'project'])
        }
    }


@router.get("/infer/{project_name}")
async def infer_project_dependencies(project_name: str):
    """
    Infer dependencies for a specific project by analyzing config files.
    """
    from core.inference import DependencyInferrer
    
    inferrer = DependencyInferrer()
    result = inferrer.infer_for_project(project_name)
    
    return result


@router.get("/infer")
async def infer_all_dependencies():
    """
    Run dependency inference on all projects.
    """
    from core.inference import DependencyInferrer
    
    inferrer = DependencyInferrer()
    results = inferrer.infer_all_projects()
    
    # Summary
    total_inferred = 0
    projects_with_missing = []
    for r in results:
        if r.get("recommendations"):
            projects_with_missing.append(r["project"])
        total_inferred += len(r.get("all_inferred", []))
    
    return {
        "projects_analyzed": len(results),
        "total_dependencies_inferred": total_inferred,
        "projects_with_missing_declarations": projects_with_missing,
        "details": results
    }


@router.get("/scan/runtime/{service_name}")
async def scan_service_runtime(service_name: str):
    """
    Scan a specific service's runtime connections via SSH.
    
    Returns real-time outbound connections and inferred dependencies.
    This provides HIGH confidence dependency data.
    """
    from core.inference import DependencyInferrer
    
    inferrer = DependencyInferrer()
    result = inferrer.scan_service_runtime(service_name)
    
    return result


@router.get("/scan/runtime")
async def scan_all_runtime():
    """
    Scan ALL services for runtime dependencies.
    
    SSH into each running service and discover real connections.
    Returns a complete dependency matrix based on actual network traffic.
    
    NOTE: This may take 30-60 seconds for the full infrastructure.
    """
    from core.inference import DependencyInferrer
    
    inferrer = DependencyInferrer()
    result = inferrer.scan_all_services_runtime()
    
    return result
