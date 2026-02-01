# 🆘 NHI Emergency Recovery Guide

> **PRINT THIS DOCUMENT** and store it safely offline with your Age Keys!  
> This guide will help you recover your entire infrastructure if disaster strikes.

---

## 📋 Prerequisites - What You Need BEFORE Disaster

Keep these items accessible OFFLINE (printed or encrypted USB):

### Critical Credentials

| Item | Where to Find It | ✅ Saved? |
|------|------------------|----------|
| **Age Master Key** | `/var/lib/nhi/age/master.key` | ⬜ |
| **Age Host Key** | `/var/lib/nhi/age/host.key` | ⬜ |
| **Age Services Key** | `/var/lib/nhi/age/services.key` | ⬜ |
| **Proxmox Root Password** | Your memory | ⬜ |
| **ai-agent Password** | Your memory | ⬜ |
| **Restic Password** | If using cloud backup | ⬜ |

### Access Information

| Item | Value |
|------|-------|
| **Proxmox IP** | 192.168.1._____ |
| **NHI-CORE LXC IP** | 192.168.1._____ |
| **Backup Storage IP** | 192.168.1._____ |
| **GitHub Repo** | https://github.com/______/nhi-core |

---

## 🔴 Scenario A: Only NHI-CORE LXC is Dead

**Symptoms:** Other VMs/LXCs work, but NHI-CORE (LXC 117) is corrupted/deleted.

### Recovery Steps

```bash
# 1. Access Proxmox Web UI
#    https://192.168.1.2:8006

# 2. Navigate to Backups
#    Datacenter → Storage → [your backup storage] → Backups

# 3. Find latest nhi-core backup
#    Look for: vzdump-lxc-117-*.vma.zst

# 4. Restore
#    Right-click → Restore → Keep same VMID (117) → Start

# 5. Verify
ssh ai-agent@192.168.1.117 "hostname && cat /var/lib/nhi/config.yaml"
```

### Post-Recovery Checklist

- [ ] SSH access works
- [ ] `.cursorrules` exists in `/home/ai-agent/`
- [ ] Cron job running: `crontab -l`
- [ ] Other services reachable

---

## 🟠 Scenario B: Mini PC Dead, Local Backup OK

**Symptoms:** Mini PC hardware failure, but backup storage (PC Gaming, NAS) is intact.

### Recovery Steps

```bash
# 1. Install Proxmox on new hardware
#    Download: https://www.proxmox.com/downloads
#    Install on new mini PC
#    Configure same network (or update IPs)

# 2. Add backup storage
#    Datacenter → Storage → Add → NFS
#    Server: 192.168.1.139 (PC Gaming)
#    Export: /mnt/backup-proxmox
#    Content: VZDump backup files

# 3. Restore VMs/LXCs one by one
#    Priority order:
#    1. nhi-core (LXC 117) - Control plane
#    2. postgresql (LXC 105) - Data
#    3. Other services

# 4. For each restore:
#    Storage → [backup storage] → Backups
#    Select backup → Restore → Keep original VMID

# 5. Start LXCs
pct start 117
pct start 105
# etc.

# 6. Verify network
#    If IP range changed, update each LXC:
pct set 117 -net0 name=eth0,ip=NEW_IP/24,gw=GATEWAY
```

### Update NHI-CORE for new IPs (if changed)

```bash
# SSH into NHI-CORE
ssh ai-agent@NEW_IP

# Update Proxmox host IP in config
sudo nano /var/lib/nhi/config.yaml
# Change proxmox.host to new IP

# Force context regeneration
source /opt/nhi-core/venv/bin/activate
python3 /opt/nhi-core/core/context/updater.py

# Verify new .cursorrules
cat ~/.cursorrules
```

---

## 🔴 Scenario C: Everything Dead, Only Cloud Backup

**Symptoms:** Mini PC AND local backup storage both destroyed. Only cloud backup (Google Drive) survives.

### Requirements

- Any Linux machine with internet access
- Restic password (you saved it, right?)
- rclone configured for your cloud

### Recovery Steps

```bash
# 1. Install tools on recovery machine
sudo apt update
sudo apt install -y restic rclone

# 2. Configure rclone for Google Drive
rclone config
# Follow prompts to add 'gdrive' remote

# 3. Download encrypted backup
mkdir -p /tmp/nhi-restore
rclone copy gdrive:NHI-Backup /tmp/nhi-restore --progress

# 4. Decrypt with Restic
export RESTIC_PASSWORD="YOUR_SAVED_PASSWORD"
restic -r /tmp/nhi-restore restore latest --target /tmp/proxmox-backups

# 5. Transfer to new Proxmox
#    Option A: USB drive
#    Option B: scp to Proxmox
scp /tmp/proxmox-backups/*.vma.zst root@NEW_PROXMOX_IP:/var/lib/vz/dump/

# 6. On Proxmox, restore each backup
#    Web UI → Storage → local → Backups → Restore
```

### Reinstall NHI-CORE from Scratch

If backup is too old or missing:

```bash
# 1. Create new LXC on Proxmox
pct create 117 local:vztmpl/ubuntu-24.04-standard_24.04-2_amd64.tar.zst \
  --hostname nhi-brain \
  --memory 4096 \
  --cores 4 \
  --rootfs local-lvm:20 \
  --net0 name=eth0,ip=192.168.1.117/24,gw=192.168.1.1,bridge=vmbr0 \
  --password YOUR_PASSWORD \
  --start true

# 2. Wait for LXC to start
sleep 10

# 3. Install NHI-CORE
pct exec 117 -- bash -c '
  apt update && apt install -y git curl
  git clone https://github.com/YOUR_USER/nhi-core.git /opt/nhi-core
  cd /opt/nhi-core
  bash genesis.sh
'

# 4. Restore Age Keys from your saved copies
# SSH into LXC and paste your saved keys:
ssh root@192.168.1.117

cat > /var/lib/nhi/age/master.key << 'EOF'
# created: 2026-01-30T00:50:01Z
# public key: age1ptg72fg4czjd37fd5fqw34athqwp0mfvt3x5x99nymtvn7npkfusjpa7w7
AGE-SECRET-KEY-YOUR-SAVED-KEY-HERE
EOF

# Repeat for host.key and services.key
```

---

## ✅ Post-Recovery Verification Checklist

After any recovery, verify these:

### NHI-CORE Health

```bash
# SSH access
ssh ai-agent@192.168.1.117 "whoami"

# Config exists
ssh ai-agent@192.168.1.117 "cat /var/lib/nhi/config.yaml | head -10"

# Cron job active
ssh ai-agent@192.168.1.117 "crontab -l | grep updater"

# Context generator works
ssh ai-agent@192.168.1.117 "source /opt/nhi-core/venv/bin/activate && python3 /opt/nhi-core/core/context/updater.py"

# .cursorrules generated
ssh ai-agent@192.168.1.117 "head -20 ~/.cursorrules"
```

### Services Reachable

```bash
# PostgreSQL
nc -zv 192.168.1.105 5432

# Other services...
```

### Backup Re-enabled

```bash
# Check backup status
ssh ai-agent@192.168.1.117 "cd /opt/nhi-core && python3 cli/nhi.py backup status"

# Re-enable if needed
ssh ai-agent@192.168.1.117 "cd /opt/nhi-core && python3 cli/nhi.py backup enable"
```

---

## 📞 Emergency Contacts

| Service | Contact |
|---------|---------|
| **Proxmox Support** | https://www.proxmox.com/en/proxmox-ve/support |
| **NHI-CORE GitHub** | https://github.com/YOUR_USER/nhi-core/issues |

---

## 🔑 Your Saved Keys (FILL IN AND SECURE!)

```
=== MASTER KEY ===
# public key: age1...
AGE-SECRET-KEY-...

=== HOST KEY ===
# public key: age1...
AGE-SECRET-KEY-...

=== SERVICES KEY ===
# public key: age1...
AGE-SECRET-KEY-...

=== RESTIC PASSWORD ===
...

=== PROXMOX ROOT PASSWORD ===
...

=== AI-AGENT PASSWORD ===
...
```

⚠️ **KEEP THIS PAGE SECURE!** Store in:
- 🔒 Password manager (Bitwarden, 1Password)
- 💾 Encrypted USB drive
- 📄 Printed and locked in safe

---

*NHI Emergency Recovery Guide v1.0 - Last updated: 2026-02-01*
