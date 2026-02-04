"""
System Map Builder - Comprehensive System Catalog

Aggregates all NHI data sources into a single catalog showing:
- All machines/services
- Associated files (registry, manifest, docs)
- Standard compliance status
- Dependencies
"""

import os
import json
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class SystemMapBuilder:
    """Builds comprehensive NHI system catalog."""
    
    def __init__(self):
        self.data_path = Path("/var/lib/nhi")
        self.projects_root = Path("/home/ai-agent/projects")
        self.nhi_core_path = Path("/home/ai-agent/nhi-core-code")  # Dev path
        
    def _load_infrastructure(self) -> Dict:
        """Load infrastructure from scanner output."""
        infra_path = self.data_path / "infrastructure.yaml"
        if infra_path.exists():
            with open(infra_path, 'r') as f:
                return yaml.safe_load(f) or {}
        return {}
    
    def _load_registry_services(self) -> Dict[str, Dict]:
        """Load all registry service entries."""
        registry_path = self.data_path / "registry" / "services"
        services = {}
        if registry_path.exists():
            for yaml_file in registry_path.glob("*.yaml"):
                with open(yaml_file, 'r') as f:
                    data = yaml.safe_load(f) or {}
                    name = data.get('name') or data.get('service', {}).get('name') or yaml_file.stem
                    services[name] = {
                        "data": data,
                        "file": str(yaml_file),
                        "is_skeleton": data.get('_status') == 'skeleton'
                    }
        return services
    
    def _load_projects(self) -> Dict[str, Dict]:
        """Load all project manifests."""
        projects = {}
        
        # Add NHI-CORE as system project
        nhi_core_manifest = self.nhi_core_path / "project_manifest.yaml"
        if nhi_core_manifest.exists():
            with open(nhi_core_manifest, 'r') as f:
                data = yaml.safe_load(f) or {}
            projects["nhi-core"] = {
                "data": data,
                "path": str(self.nhi_core_path),
                "manifest_file": str(nhi_core_manifest),
                "docs_path": str(self.nhi_core_path / "docs"),
                "is_system": True
            }
        
        # Add user projects
        if self.projects_root.exists():
            for item in self.projects_root.iterdir():
                if item.is_dir() and not item.name.startswith('.'):
                    manifest_path = item / "project_manifest.yaml"
                    docs_path = item / "docs"
                    
                    project_data = {
                        "path": str(item),
                        "has_manifest": manifest_path.exists(),
                        "has_docs": docs_path.exists(),
                        "manifest_file": str(manifest_path) if manifest_path.exists() else None,
                        "docs_path": str(docs_path) if docs_path.exists() else None,
                        "is_system": False
                    }
                    
                    if manifest_path.exists():
                        with open(manifest_path, 'r') as f:
                            project_data["data"] = yaml.safe_load(f) or {}
                    else:
                        project_data["data"] = {}
                    
                    projects[item.name] = project_data
        
        return projects
    
    def _check_compliance(self, entity_type: str, data: Dict) -> Dict:
        """Check if an entity complies with NHI standards."""
        result = {
            "compliant": True,
            "issues": [],
            "warnings": []
        }
        
        if entity_type == "service":
            # Check required fields
            if not data.get("name"):
                result["compliant"] = False
                result["issues"].append("Missing 'name'")
            if not data.get("vmid"):
                result["compliant"] = False
                result["issues"].append("Missing 'vmid'")
            if not data.get("description") or "skeleton" in str(data.get("description", "")):
                result["warnings"].append("Description needs review")
            if not data.get("dependencies"):
                result["warnings"].append("No dependencies declared")
                
        elif entity_type == "project":
            if not data.get("name"):
                result["compliant"] = False
                result["issues"].append("Missing 'name'")
            if not data.get("version"):
                result["warnings"].append("Missing 'version'")
            if not data.get("dependencies", {}).get("services"):
                result["warnings"].append("No service dependencies declared")
        
        return result
    
    def build_catalog(self) -> Dict:
        """
        Build comprehensive system catalog.
        
        Returns:
            Dict with machines, services, projects, and their associations
        """
        infrastructure = self._load_infrastructure()
        registry_services = self._load_registry_services()
        projects = self._load_projects()
        
        catalog = {
            "version": "1.0",
            "generated": datetime.now().isoformat(),
            "summary": {
                "total_machines": 0,
                "total_services": 0,
                "total_projects": 0,
                "compliance_issues": 0,
                "skeletons_pending": 0
            },
            "machines": [],
            "orphan_registry": [],  # Registry entries without matching machine
            "orphan_projects": []   # Projects without registry linkage
        }
        
        # Build machine entries from infrastructure
        resources = infrastructure.get("resources", [])
        machines_by_vmid = {}
        
        for resource in resources:
            vmid = resource.get("vmid")
            name = resource.get("name")
            
            machine = {
                "vmid": vmid,
                "name": name,
                "type": resource.get("type"),
                "status": resource.get("status"),
                "ip": resource.get("ip"),
                "resources": {
                    "cpu": resource.get("cpu"),
                    "memory_bytes": resource.get("mem")
                },
                "files": {
                    "registry": None,
                    "manifest": None,
                    "docs": None
                },
                "dependencies": {
                    "required": [],
                    "optional": [],
                    "consumers": []  # Who depends on this
                },
                "compliance": None,
                "linked_projects": []
            }
            
            # Try to find matching registry entry
            for svc_name, svc_data in registry_services.items():
                svc_vmid = svc_data["data"].get("vmid")
                if svc_vmid == vmid or svc_name.lower() in name.lower():
                    machine["files"]["registry"] = svc_data["file"]
                    machine["dependencies"]["required"] = svc_data["data"].get("dependencies", {}).get("required", [])
                    machine["dependencies"]["optional"] = svc_data["data"].get("dependencies", {}).get("optional", [])
                    machine["compliance"] = self._check_compliance("service", svc_data["data"])
                    if svc_data["is_skeleton"]:
                        catalog["summary"]["skeletons_pending"] += 1
                    registry_services[svc_name]["matched"] = True
                    break
            
            # Check if any project is hosted on this machine
            for proj_name, proj_data in projects.items():
                reg = proj_data.get("data", {}).get("registration", {})
                if reg.get("vmid") == vmid:
                    machine["linked_projects"].append(proj_name)
                    machine["files"]["manifest"] = proj_data.get("manifest_file")
                    machine["files"]["docs"] = proj_data.get("docs_path")
            
            machines_by_vmid[vmid] = machine
            catalog["machines"].append(machine)
        
        # Find orphan registry entries (not matched to any machine)
        for svc_name, svc_data in registry_services.items():
            if not svc_data.get("matched"):
                catalog["orphan_registry"].append({
                    "name": svc_name,
                    "file": svc_data["file"],
                    "declared_vmid": svc_data["data"].get("vmid")
                })
        
        # Find projects that consume services and update consumer lists
        for proj_name, proj_data in projects.items():
            deps = proj_data.get("data", {}).get("dependencies", {}).get("services", [])
            for dep in deps:
                # Find which machine provides this service
                for machine in catalog["machines"]:
                    if dep.lower() in machine["name"].lower():
                        machine["dependencies"]["consumers"].append(proj_name)
        
        # Calculate summary
        catalog["summary"]["total_machines"] = len(catalog["machines"])
        catalog["summary"]["total_services"] = len(registry_services)
        catalog["summary"]["total_projects"] = len(projects)
        catalog["summary"]["orphan_registry"] = len(catalog["orphan_registry"])
        
        for machine in catalog["machines"]:
            if machine.get("compliance") and not machine["compliance"]["compliant"]:
                catalog["summary"]["compliance_issues"] += 1
        
        return catalog
    
    def save_catalog(self, output_path: str = None) -> str:
        """Build and save the system catalog."""
        catalog = self.build_catalog()
        
        output_path = output_path or str(self.data_path / "context" / "system-catalog.json")
        
        with open(output_path, 'w') as f:
            json.dump(catalog, f, indent=2, ensure_ascii=False)
        
        return output_path
    
    def get_machine_summary(self, vmid: int) -> Optional[Dict]:
        """Get a summary of a specific machine and all its associations."""
        catalog = self.build_catalog()
        for machine in catalog["machines"]:
            if machine["vmid"] == vmid:
                return machine
        return None
