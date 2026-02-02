#!/usr/bin/env python3
"""
NHI-CORE Install Script

Post-genesis installation orchestrator.
Called by genesis.sh after dependencies are installed.
"""

import os
import sys
import shutil
import argparse
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


def run_install(skip_scan: bool = False):
    """
    Run post-genesis installation.
    
    Args:
        skip_scan: Skip Proxmox scan (for testing)
    """
    from core.scanner import ProxmoxScanner
    from core.context import ContextGenerator
    
    logger.info("Starting NHI-CORE installation...")
    
    # Step 1: Infrastructure scan
    if not skip_scan:
        logger.info("Scanning Proxmox infrastructure...")
        try:
            scanner = ProxmoxScanner()
            infrastructure = scanner.scan_all()
            scanner.save_infrastructure()
            logger.info(f"Discovered {len(infrastructure.get('resources', []))} resources")
        except Exception as e:
            logger.error(f"Scan failed: {e}")
            logger.warning("Proceeding with empty infrastructure...")
            infrastructure = {'resources': [], 'nodes': [], 'storage': [], 'network': {}}
    else:
        logger.info("Skipping Proxmox scan (--skip-scan)")
        infrastructure = {'resources': [], 'nodes': [], 'storage': [], 'network': {}}
    
    # Step 2: Generate context files
    logger.info("Generating AI context files...")
    generator = ContextGenerator(infrastructure)
    paths = generator.generate()
    logger.info(f"Created: {paths['cursorrules']}")
    logger.info(f"Created: {paths['system_map']}")
    
    logger.info(f"Created: {paths['system_map']}")

    # Step 3: Deploy Design System (New in v1.1)
    logger.info("Deploying NHI Design System (v1.1)...")
    ds_src = os.path.join(os.path.dirname(__file__), 'templates', 'design-system')
    ds_dest = '/var/lib/nhi/design-system'
    
    if os.path.exists(ds_src):
        if os.path.exists(ds_dest):
            shutil.rmtree(ds_dest)
        shutil.copytree(ds_src, ds_dest)
        logger.info(f"Deployed Design System to {ds_dest}")
    else:
        logger.warning(f"Design System templates not found at {ds_src}")
    
    # Step 3: Deploy Design System (New in v1.1)
    logger.info("Deploying NHI Design System (v1.1)...")
    ds_src = os.path.join(os.path.dirname(__file__), 'templates', 'design-system')
    ds_dest = '/var/lib/nhi/design-system'
    
    if os.path.exists(ds_src):
        if os.path.exists(ds_dest):
            shutil.rmtree(ds_dest)
        shutil.copytree(ds_src, ds_dest)
        logger.info(f"Deployed Design System to {ds_dest}")
    else:
        logger.warning(f"Design System templates not found at {ds_src}")
    
    # Step 4: Expose Documentation (New in v1.1)
    logger.info("Exposing documentation to users...")
    docs_src = os.path.join(os.path.dirname(__file__), 'docs')
    
    # Locate AI Agent home (fallback to /home/ai-agent if not found in environment)
    # We should get this from config, but here we assume standard path or check genesis
    # A safer bet is checking where we are running. 
    # But usually ai-agent home is /home/ai-agent.
    ai_home = '/home/ai-agent' 
    docs_dest = os.path.join(ai_home, '_NHI')
    
    if os.path.exists(docs_src):
        if not os.path.exists(docs_dest):
             # check if ai_home exists
             if os.path.exists(ai_home):
                try:
                    os.symlink(docs_src, docs_dest)
                    logger.info(f"Created symlink: {docs_dest} -> {docs_src}")
                    # Ensure agent owns the symlink (if running as root)
                    shutil.chown(docs_dest, user='ai-agent', group='ai-agent')
                except Exception as e:
                    logger.error(f"Failed to create docs symlink: {e}")
             else:
                 logger.warning(f"AI Agent home not found at {ai_home}")
        else:
             logger.info(f"Documentation link already exists at {docs_dest}")
    else:
        logger.warning(f"Documentation source not found at {docs_src}")

    # Step 5: Summary
    logger.info("")
    logger.info("=" * 50)
    logger.info("Installation complete!")
    logger.info("=" * 50)
    logger.info("")
    logger.info("Files created:")
    logger.info(f"  - /var/lib/nhi/infrastructure.yaml")
    logger.info(f"  - /var/lib/nhi/context/.cursorrules")
    logger.info(f"  - /var/lib/nhi/context/system-map.json")
    logger.info("")


def main():
    parser = argparse.ArgumentParser(description='NHI-CORE Installer')
    parser.add_argument(
        '--skip-scan',
        action='store_true',
        help='Skip Proxmox infrastructure scan'
    )
    args = parser.parse_args()
    
    try:
        run_install(skip_scan=args.skip_scan)
    except Exception as e:
        logger.error(f"Installation failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
