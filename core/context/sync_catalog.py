#!/usr/bin/env python3
"""
NHI Catalog Synchronizer
========================
Automated periodic task to:
1. Scan entire infrastructure (Proxmox + Runtime)
2. Detect new machines and create skeleton registries
3. Update dependency graph via runtime scanning
4. Refresh system catalog JSON

Run by systemd timer: nhi-sync.timer
"""

import sys
import os
import requests
import json
import time
from datetime import datetime

# Add core to path
sys.path.insert(0, "/home/ai-agent/nhi-core-code")

from core.registry import RegistryManager
from core.context.system_map_builder import SystemMapBuilder

API_URL = "http://localhost:8000"

def log(msg):
    print(f"[{datetime.now().isoformat()}] {msg}")

def sync_infrastructure():
    log("🔄 Starting Infrastructure Sync...")
    
    # 1. Trigger Runtime Scan (this updates cache)
    try:
        log("  → Scanning runtime dependencies (may take 60s)...")
        resp = requests.get(f"{API_URL}/services/scan/runtime", timeout=120)
        if resp.status_code == 200:
            stats = resp.json().get("summary", {})
            log(f"    ✅ Runtime scan complete: {stats.get('total_connections')} connections found")
        else:
            log(f"    ❌ Runtime scan failed: {resp.status_code}")
    except Exception as e:
        log(f"    ❌ Runtime scan error: {e}")

    # 2. Rebuild Catalog (System Map)
    try:
        log("  → Rebuilding System Catalog...")
        # We use the internal builder to ensure it runs even if API is down
        # but configured to use the fresh cache we just (hopefully) updated
        builder = SystemMapBuilder()
        catalog = builder.build_catalog() # This aggregates everything
        output_path = builder.save_catalog()
        
        # Check for new machines (skeletons needed?)
        rm = RegistryManager()
        missing = rm.check_missing_registries(catalog.get("machines", []))
        
        if missing:
            log(f"  ⚠️ Found {len(missing)} machines without registry. Creating skeletons...")
            for m in missing:
                # Auto-create skeleton
                path = rm.create_skeleton(m['name'], m.get('vmid'), m.get('ip'))
                log(f"    + Created skeleton for {m['name']} at {path}")
            
            # Rebuild catalog again to include new skeletons
            builder.save_catalog()
            
        stats = catalog.get("summary", {})
        log(f"    ✅ Catalog updated: {stats.get('total_machines')} machines, {stats.get('total_services')} services")
        log(f"    💾 Saved to: {output_path}")

    except Exception as e:
        log(f"    ❌ Catalog rebuild error: {e}")
        return False
        
    return True

if __name__ == "__main__":
    success = sync_infrastructure()
    sys.exit(0 if success else 1)
