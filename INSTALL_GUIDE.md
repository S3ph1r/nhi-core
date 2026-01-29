# NHI-CORE Installation Guide

## Complete Setup from Scratch to Antigravity Control

This guide walks you through setting up NHI-CORE on a virgin Proxmox environment, from zero to full AI agent control.

---

## Prerequisites

| What | Required |
|------|----------|
| Proxmox VE | 8.0+ installed on mini PC |
| Windows PC | With VS Code/Cursor + Antigravity |
| GitHub account | For repository access |
| Network | Both machines on same LAN |

---

## Phase 1: Proxmox Setup (Manual - 30 min)

### 1.1 Create API Token for NHI-CORE

1. Login to Proxmox WebUI: `https://<PROXMOX_IP>:8006`
2. Navigate: **Datacenter → Permissions → API Tokens**
3. Click **Add**:
   - User: `root@pam`
   - Token ID: `nhi-core`
   - ❌ Uncheck "Privilege Separation"
4. **COPY THE SECRET IMMEDIATELY** (shown only once)

### 1.2 Create LXC Container (ID: 110)

1. **Download Ubuntu template**: 
   - Local storage → CT Templates → Templates → Download
   - Select: `ubuntu-24.04-standard`

2. **Create Container**:
   - ID: `110`
   - Hostname: `nhi-brain`
   - Template: `ubuntu-24.04-standard`
   - Disk: `20GB`
   - CPU: `4 cores`
   - RAM: `4096 MB`
   - Network: `DHCP` or static `192.168.1.110/24`
   - **SSH Public Key**: Paste your Windows SSH public key (see 1.3)

3. **Start container**

### 1.3 Generate SSH Key on Windows (if not exists)

```powershell
# Check if key exists
Get-Content $env:USERPROFILE\.ssh\id_ed25519.pub

# If not, generate:
ssh-keygen -t ed25519 -C "antigravity@windows"
# Press Enter for all prompts (no passphrase)

# Copy public key for Proxmox:
Get-Content $env:USERPROFILE\.ssh\id_ed25519.pub | Set-Clipboard
```

### 1.4 Configure ai-agent User on LXC

```bash
# SSH as root first (using Proxmox console or key)
ssh root@192.168.1.110

# Create ai-agent user
useradd -m -s /bin/bash ai-agent
echo "ai-agent ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/ai-agent

# Setup SSH for ai-agent
mkdir -p /home/ai-agent/.ssh
chmod 700 /home/ai-agent/.ssh

# Paste your Windows public key here:
nano /home/ai-agent/.ssh/authorized_keys
# (Paste content of id_ed25519.pub, save with Ctrl+X, Y, Enter)

chmod 600 /home/ai-agent/.ssh/authorized_keys
chown -R ai-agent:ai-agent /home/ai-agent/.ssh
```

### 1.5 Test SSH Connection from Windows

```powershell
ssh ai-agent@192.168.1.110 "whoami && hostname"
# Expected: ai-agent \n nhi-brain
```

---

## Phase 2: Install NHI-CORE (Semi-Automated - 10 min)

### 2.1 Clone Repository

```bash
ssh ai-agent@192.168.1.110

# Install dependencies
sudo apt update && sudo apt install -y git python3 python3-pip python3-venv curl

# Create directories
sudo mkdir -p /opt/nhi-core /var/lib/nhi /var/log/nhi
sudo chown -R ai-agent:ai-agent /opt/nhi-core /var/lib/nhi /var/log/nhi

# Clone NHI-CORE
cd /opt/nhi-core
git clone https://github.com/S3ph1r/nhi-core.git .

# Setup Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2.2 Configure NHI-CORE

```bash
# Create configuration
mkdir -p /var/lib/nhi/{context,registry,secrets,templates}

cat > /var/lib/nhi/config.yaml << 'EOF'
proxmox:
  host: "192.168.1.2"      # Your Proxmox IP
  port: 8006
  token_id: "root@pam!nhi-core"
  verify_ssl: false

github:
  repo: "https://github.com/YOUR_USER/nhi-core.git"

network:
  domain_suffix: ".home"

paths:
  data: "/var/lib/nhi"
  logs: "/var/log/nhi"
  home: "/opt/nhi-core"
EOF

# Save Proxmox token secret
echo "YOUR_PROXMOX_TOKEN_SECRET" > /var/lib/nhi/secrets/.proxmox_token
chmod 600 /var/lib/nhi/secrets/.proxmox_token
```

### 2.3 Run Initial Scan

```bash
cd /opt/nhi-core
source venv/bin/activate
python install.py
```

**Expected output:**
- `infrastructure.yaml` created in `/var/lib/nhi/`
- `.cursorrules` created in `/var/lib/nhi/context/`

---

## Phase 3: Prepare for Antigravity (5 min)

### 3.1 Create Symlinks for AI Access

```bash
ssh ai-agent@192.168.1.110

# Create symlinks in home directory
ln -s /var/lib/nhi ~/nhi-data
ln -s /var/lib/nhi/context/.cursorrules ~/.cursorrules

# Create projects directory
mkdir -p ~/projects

# Create .agent directory for workflows
mkdir -p ~/.agent/workflows
```

### 3.2 Setup Cron for Auto-Updates

```bash
# Add hourly update job
echo "0 * * * * /opt/nhi-core/venv/bin/python /opt/nhi-core/core/context/updater.py >> /var/log/nhi/cron.log 2>&1" | sudo tee /etc/cron.d/nhi-core
sudo chmod 644 /etc/cron.d/nhi-core
```

---

## Phase 4: Map Drive on Windows (5 min)

### 4.1 RaiDrive Configuration

| Field | Value |
|-------|-------|
| Storage | NAS → SFTP |
| Drive Letter | `N:` |
| Address | `192.168.1.110` |
| Port | `22` |
| Path | `/home/ai-agent` |
| Account | `ai-agent` |
| Auth | Key File |
| Key File | `C:\Users\<YOU>\.ssh\id_ed25519` |

> **Note:** If you used `root` user, change Path to `/root` and Account to `root`.
> For security, prefer `ai-agent` user.

### 4.2 Verify Connection

After connecting, you should see in `N:\`:
```
N:\
├── .cursorrules          ← AI rules (symlink)
├── nhi-data/             ← NHI context (symlink)
├── projects/             ← Your projects go here
└── .agent/               ← Antigravity workflows
```

---

## Phase 5: Open Antigravity on N: Workspace

1. **Close VS Code/Cursor completely**
2. **Reopen with workspace:** `N:\`
3. **Verify:** Antigravity should now read `.cursorrules` automatically

---

## Credential Summary

| Credential | Where Stored | Who Uses |
|------------|--------------|----------|
| SSH Private Key | `C:\Users\<YOU>\.ssh\id_ed25519` | Windows/RaiDrive |
| SSH Public Key | `/home/ai-agent/.ssh/authorized_keys` | LXC 110 |
| Proxmox API Token | `/var/lib/nhi/secrets/.proxmox_token` | NHI-CORE scanner |
| GitHub Token | (optional) | For auto-push |

---

## What Happens Automatically After Setup

| What | When | Result |
|------|------|--------|
| Infrastructure scan | Every hour (cron) | `infrastructure.yaml` updated |
| Context regeneration | Every hour (cron) | `.cursorrules` updated |
| Git push (optional) | After changes | Registry synced to GitHub |

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| SSH "Permission denied" | Check key permissions: `chmod 600 ~/.ssh/*` |
| RaiDrive won't connect | Verify SSH works first: `ssh ai-agent@192.168.1.110` |
| Scanner fails | Check Proxmox token and network connectivity |
| No .cursorrules | Run `python install.py` manually |

---

## Future: What genesis.sh Will Automate

When genesis.sh is run in unattended mode with a config file, it will:
1. ✅ Install all dependencies
2. ✅ Create directories
3. ✅ Generate GPG key for SOPS
4. ✅ Configure SMB share
5. ✅ Setup cron job
6. ✅ Run initial scan
7. ⬜ Deploy SSH keys (future)
8. ⬜ Configure RaiDrive (not possible - Windows GUI)

---

*NHI-CORE v1.0 - January 2026*
