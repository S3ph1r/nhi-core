#!/usr/bin/env python3
"""
NHI-CORE Context Updater

Cron job script that:
1. Refreshes infrastructure scan from Proxmox
2. Regenerates AI context files
3. Commits and pushes to GitHub if changes detected
"""

import os
import sys
import subprocess
import logging
from datetime import datetime

# Add parent to path for imports
sys.path.insert(0, '/opt/nhi-core')

from core.scanner import ProxmoxScanner
from core.context import ContextGenerator


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/var/log/nhi/cron.log')
    ]
)
logger = logging.getLogger(__name__)


def run_update():
    """Perform infrastructure scan and context regeneration."""
    logger.info("Starting scheduled update...")
    
    try:
        # Step 1: Scan infrastructure
        logger.info("Scanning Proxmox infrastructure...")
        scanner = ProxmoxScanner()
        infrastructure = scanner.scan_all()
        scanner.save_infrastructure()
        logger.info(f"Found {len(infrastructure.get('resources', []))} resources")
        
        # Step 2: Generate context
        logger.info("Generating AI context files...")
        generator = ContextGenerator(infrastructure)
        paths = generator.generate()
        logger.info(f"Generated: {paths}")
        
        # Step 3: Git commit/push if changes
        push_changes()
        
        logger.info("Update complete")
        
    except Exception as e:
        logger.error(f"Update failed: {e}")
        raise


def push_changes():
    """Commit and push to GitHub if there are changes."""
    data_path = "/var/lib/nhi"
    
    # Check if git repo
    if not os.path.exists(os.path.join(data_path, '.git')):
        logger.info("No git repository in data path, skipping push")
        return
    
    try:
        # Check for changes
        result = subprocess.run(
            ['git', 'status', '--porcelain'],
            cwd=data_path,
            capture_output=True,
            text=True
        )
        
        if not result.stdout.strip():
            logger.info("No changes to commit")
            return
        
        # Add all changes
        subprocess.run(['git', 'add', '-A'], cwd=data_path, check=True)
        
        # Commit
        commit_msg = f"[NHI-CORE] Auto-update {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        subprocess.run(
            ['git', 'commit', '-m', commit_msg],
            cwd=data_path,
            check=True
        )
        
        # Push
        subprocess.run(['git', 'push'], cwd=data_path, check=True)
        
        logger.info("Changes pushed to GitHub")
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Git operation failed: {e}")


if __name__ == '__main__':
    run_update()
