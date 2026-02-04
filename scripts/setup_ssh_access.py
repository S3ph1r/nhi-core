#!/usr/bin/env python3
"""
Setup SSH Access for All Existing Containers

This script:
1. Gets list of all running containers from system-map
2. Tests SSH connectivity to each
3. For those failing, attempts to setup via pct exec

Usage:
    python3 setup_ssh_access.py
    python3 setup_ssh_access.py --vmid 101  # Single container
"""

import sys
import json
import subprocess
import argparse
from pathlib import Path

sys.path.insert(0, "/home/ai-agent/nhi-core-code")

SYSTEM_MAP_PATH = Path("/var/lib/nhi/context/system-map.json")
SSH_PUB_KEY_PATH = Path("/home/ai-agent/.ssh/id_ed25519.pub")
PROXMOX_NODE = "192.168.1.2"  # IP is safer than hostname



def test_ssh(ip: str) -> bool:
    """Test if SSH works to this IP."""
    try:
        result = subprocess.run(
            ["ssh", "-o", "ConnectTimeout=3", "-o", "StrictHostKeyChecking=no",
             "-o", "BatchMode=yes", f"ai-agent@{ip}", "echo OK"],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode == 0
    except:
        return False



def setup_via_pct(vmid: int, pub_key: str, password: str = None) -> bool:
    """Setup ai-agent user and SSH via pct exec."""
    commands = [
        "id ai-agent || useradd -m -s /bin/bash ai-agent",
        "mkdir -p /home/ai-agent/.ssh",
        f"echo '{pub_key}' > /home/ai-agent/.ssh/authorized_keys",
        "chown -R ai-agent:ai-agent /home/ai-agent/.ssh",
        "chmod 700 /home/ai-agent/.ssh",
        "chmod 600 /home/ai-agent/.ssh/authorized_keys",
        # Also allow sudo without password for ai-agent
        "echo 'ai-agent ALL=(ALL) NOPASSWD:ALL' > /etc/sudoers.d/ai-agent && chmod 440 /etc/sudoers.d/ai-agent"
    ]
    
    for cmd in commands:
        try:
            if password:
                # Use sshpass with password
                # Note: requires sshpass installed (sudo apt install sshpass)
                full_cmd = f"sshpass -p '{password}' ssh -o StrictHostKeyChecking=no root@{PROXMOX_NODE} 'pct exec {vmid} -- bash -c \"{cmd}\"'"
            else:
                # Use key-based auth
                full_cmd = f"ssh root@{PROXMOX_NODE} 'pct exec {vmid} -- bash -c \"{cmd}\"'"
                
            result = subprocess.run(
                full_cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=15
            )
            if result.returncode != 0:
                print(f"      Warning: {cmd[:40]}... returned {result.returncode}")
                # Don't fail immediately, some commands might fail harmlessly (e.g. user exists)
        except Exception as e:
            print(f"      Error: {e}")
            return False
    
    return True


def main(target_vmid: int = None, password: str = None):
    print("=" * 60)
    print("NHI SSH Access Setup")
    print("=" * 60)
    
    # Load system map
    if not SYSTEM_MAP_PATH.exists():
        print("ERROR: system-map.json not found!")
        return
    
    with open(SYSTEM_MAP_PATH) as f:
        data = json.load(f)
    
    resources = data.get("resources", [])
    
    # Load SSH public key
    if not SSH_PUB_KEY_PATH.exists():
        print("ERROR: SSH public key not found!")
        print(f"Run: ssh-keygen -t ed25519")
        return
    
    pub_key = SSH_PUB_KEY_PATH.read_text().strip()
    print(f"SSH Key: {pub_key[:50]}...")
    
    if password:
        print("Using provided password for Proxmox root access")
        # Check if sshpass is installed
        if subprocess.run("which sshpass", shell=True).returncode != 0:
            print("Installing sshpass...")
            subprocess.run("sudo apt update && sudo apt install -y sshpass", shell=True)
    
    # Process each container
    results = {"ok": [], "fixed": [], "failed": [], "skipped": []}
    
    for res in resources:
        vmid = res.get("vmid")
        name = res.get("name")
        ip = res.get("ip")
        status = res.get("status")
        res_type = res.get("type")
        
        # Filter if specific VMID requested
        if target_vmid and vmid != target_vmid:
            continue
        
        print(f"\n[{vmid}] {name} ({ip})")
        
        # Skip VMs (only LXC via pct)
        if res_type == "qemu":
            print("  → Skipping (VM, not LXC)")
            results["skipped"].append(name)
            continue
        
        # Skip stopped containers
        if status != "running":
            print("  → Skipping (not running)")
            results["skipped"].append(name)
            continue
        
        # Skip if no IP
        if not ip:
            print("  → Skipping (no IP)")
            results["skipped"].append(name)
            continue
        
        # Test SSH
        print("  → Testing SSH...", end=" ")
        if test_ssh(ip):
            print("✅ Working")
            results["ok"].append(name)
            continue
        
        print("❌ Failed")
        
        # Try to fix via pct
        print("  → Attempting fix via pct exec...", end=" ")
        if setup_via_pct(vmid, pub_key, password):
            # Verify
            if test_ssh(ip):
                print("✅ Fixed!")
                results["fixed"].append(name)
            else:
                print("⚠️ Still not working")
                results["failed"].append(name)
        else:
            print("❌ Setup failed")
            results["failed"].append(name)
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Already OK:  {len(results['ok'])} - {results['ok']}")
    print(f"  Fixed:       {len(results['fixed'])} - {results['fixed']}")
    print(f"  Failed:      {len(results['failed'])} - {results['failed']}")
    print(f"  Skipped:     {len(results['skipped'])} - {results['skipped']}")
    print("=" * 60)
    
    if results["failed"]:
        print("\n⚠️ Manual fix needed for failed containers:")
        print("   1. SSH to Proxmox: ssh root@homelab")
        print("   2. Enter container: pct enter <VMID>")
        print("   3. Create user: useradd -m -s /bin/bash ai-agent")
        print("   4. Setup SSH manually")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Setup SSH access to containers")
    parser.add_argument("--vmid", type=int, help="Specific VMID to setup")
    parser.add_argument("--password", help="Proxmox root password")
    args = parser.parse_args()
    
    main(target_vmid=args.vmid, password=args.password)
