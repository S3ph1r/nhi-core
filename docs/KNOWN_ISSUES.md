# NHI-CORE Known Issues & Workarounds

> **Version:** 1.1
> **Last Updated:** 2026-01-30

This document is part of NHI-CORE context for AI agents. It describes known issues and their solutions.

---

## 1. SSH Root Login on New Ubuntu LXC Containers

### Problem
When creating a new LXC container with Ubuntu 22.04/24.04, SSH access with root password fails even if the password is set correctly during container creation.

**Error message:**
```
Permission denied, please try again.
```

### Root Cause
Ubuntu's default SSH configuration blocks root password login for security:
```
PermitRootLogin prohibit-password
```

This setting allows root login ONLY via SSH keys, not passwords.

### Solution: Use `pct exec` from Proxmox Host

Since you cannot SSH into the container, use Proxmox's `pct exec` command to fix the SSH configuration from the host:

```bash
# From Proxmox host (192.168.1.2)
VMID=<container_id>
PASSWORD="your-password"

# Fix SSH config to allow root password login
pct exec $VMID -- sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config
pct exec $VMID -- sed -i 's/PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config
pct exec $VMID -- systemctl restart sshd

# Now SSH works
ssh root@<container_ip>
```

### Full Script (via LXC 110 Brain)
```bash
#!/bin/bash
# fix_ssh_new_lxc.sh - Run from LXC 110 (NHI Brain)

VMID=$1
HOST="192.168.1.2"
PASS="your-password"

if [ -z "$VMID" ]; then
    echo "Usage: $0 <VMID>"
    exit 1
fi

# Get container IP
IP=$(sshpass -p "$PASS" ssh -o StrictHostKeyChecking=no root@$HOST "pct exec $VMID -- hostname -I | awk '{print \$1}'")

echo "Fixing SSH for LXC $VMID (IP: $IP)..."

sshpass -p "$PASS" ssh -o StrictHostKeyChecking=no root@$HOST "pct exec $VMID -- sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config"
sshpass -p "$PASS" ssh -o StrictHostKeyChecking=no root@$HOST "pct exec $VMID -- sed -i 's/PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config"
sshpass -p "$PASS" ssh -o StrictHostKeyChecking=no root@$HOST "pct exec $VMID -- systemctl restart sshd"

echo "Testing SSH..."
sleep 2
sshpass -p "$PASS" ssh -o StrictHostKeyChecking=no root@$IP "hostname && echo 'SSH OK!'"
```

### Alternative: Inject SSH Key During Creation

If Proxmox API's SSH key injection worked (currently bugged with Error 500), this workaround would not be needed. Monitor Proxmox updates for a fix.

---

## 2. APT Interactive Prompts During Installation

### Problem
When running `apt install` with packages like `openssh-server`, dpkg may prompt interactively asking about modified configuration files.

### Solution
Use `DEBIAN_FRONTEND=noninteractive` to skip all prompts:

```bash
export DEBIAN_FRONTEND=noninteractive
apt-get install -y -qq openssh-server
```

Or for apt-get:
```bash
apt-get -o Dpkg::Options::="--force-confold" install -y openssh-server
```

---

## 3. Proxmox API SSH Key Injection Bug

### Problem
When creating an LXC via Proxmox API with `ssh-public-keys` parameter, it fails with Error 500.

### Workaround
1. Create container without SSH key
2. Use `pct exec` to add key manually:
   ```bash
   pct exec $VMID -- mkdir -p /root/.ssh
   pct exec $VMID -- chmod 700 /root/.ssh
   pct exec $VMID -- bash -c "echo 'ssh-ed25519 AAAA...' >> /root/.ssh/authorized_keys"
   pct exec $VMID -- chmod 600 /root/.ssh/authorized_keys
   ```

---

*This document should be updated when new issues are discovered.*
