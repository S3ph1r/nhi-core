#!/usr/bin/env python3
"""
NHI Sync Catalog - Automated Registry & Context Synchronization

This script:
1. Scans Proxmox for current infrastructure
2. Identifies missing registry entries
3. Creates skeleton registries for new services
4. Updates system-catalog.json
5. Regenerates .cursorrules

Designed to run via cron hourly.
"""

import os
import sys

# Add core to path
sys.path.insert(0, '/opt/nhi-core')

from datetime import datetime
from pathlib import Path


def sync_catalog():
    """Run full catalog synchronization."""
    from core.scanner import ProxmoxScanner
    from core.context import ContextGenerator
    from core.registry import RegistryManager
    from core.context.system_map_builder import SystemMapBuilder
    
    print(f"[{datetime.now().isoformat()}] Starting NHI Catalog Sync...")
    
    # 1. Scan Proxmox infrastructure
    print("  → Scanning Proxmox...")
    scanner = ProxmoxScanner()
    scanner.save_infrastructure()
    
    # 2. Regenerate context files
    print("  → Regenerating context files...")
    generator = ContextGenerator()
    paths = generator.generate()
    print(f"    - Generated: {paths['cursorrules']}")
    print(f"    - Generated: {paths['system_map']}")
    
    # 3. Check for missing registry entries
    print("  → Checking registry completeness...")
    registry = RegistryManager()
    builder = SystemMapBuilder()
    catalog = builder.build_catalog()
    
    # Find machines without registry
    new_skeletons = []
    for machine in catalog['machines']:
        if machine['files']['registry'] is None:
            name = machine['name'].lower().replace(' ', '-')
            vmid = machine['vmid']
            ip = machine.get('ip')
            
            print(f"    - Creating skeleton for: {name} (VMID {vmid})")
            path = registry.create_skeleton(name, vmid, ip)
            new_skeletons.append(str(path))
    
    # 4. Save updated catalog
    print("  → Saving system catalog...")
    catalog_path = builder.save_catalog()
    print(f"    - Saved: {catalog_path}")
    
    # 5. Copy .cursorrules to home
    print("  → Deploying .cursorrules...")
    context_cursorrules = Path("/var/lib/nhi/context/.cursorrules")
    home_cursorrules = Path("/home/ai-agent/.cursorrules")
    if context_cursorrules.exists():
        import shutil
        shutil.copy(context_cursorrules, home_cursorrules)
        print(f"    - Copied to: {home_cursorrules}")
    
    # Summary
    final_catalog = builder.build_catalog()
    print("\n" + "="*50)
    print("SYNC COMPLETE")
    print("="*50)
    print(f"  Machines: {final_catalog['summary']['total_machines']}")
    print(f"  Services: {final_catalog['summary']['total_services']}")
    print(f"  Projects: {final_catalog['summary']['total_projects']}")
    print(f"  Compliance Issues: {final_catalog['summary']['compliance_issues']}")
    print(f"  Skeletons Pending: {final_catalog['summary']['skeletons_pending']}")
    if new_skeletons:
        print(f"  New Skeletons Created: {len(new_skeletons)}")
        for s in new_skeletons:
            print(f"    - {s}")
    print("="*50)
    
    return {
        "success": True,
        "catalog_path": catalog_path,
        "new_skeletons": new_skeletons,
        "summary": final_catalog['summary']
    }


if __name__ == "__main__":
    try:
        result = sync_catalog()
        sys.exit(0)
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
