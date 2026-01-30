---
description: How to deploy a service to its target LXC
---

# Deploy Service Workflow

This workflow guides you through deploying a containerized service to its target LXC.

## Prerequisites

- [ ] Project follows NHI structure (run `/new-project` first)
- [ ] Docker build works locally
- [ ] Health endpoint implemented
- [ ] Target LXC running and accessible

## Step 1: Verify Local Build

```bash
cd <project-directory>
docker-compose build
docker-compose up -d
curl http://localhost:<port>/health
```

Expected: `{"status": "healthy", ...}`

## Step 2: Prepare for Remote Deploy

### Get target info from project manifest
```yaml
# From project_manifest.md
LXC ID: <id>
IP: <ip>
Port: <port>
```

### Verify SSH access
```bash
ssh ai-agent@<ip> "hostname && whoami"
```

Expected: Shows hostname and `ai-agent`

## Step 3: Transfer Project to LXC

Option A: Git clone (if on GitHub)
```bash
ssh ai-agent@<ip> "git clone <repo-url> ~/projects/<project-name>"
```

Option B: SCP transfer
```bash
scp -r <project-directory> ai-agent@<ip>:~/projects/<project-name>
```

## Step 4: Build on Target LXC

```bash
ssh ai-agent@<ip> "cd ~/projects/<project-name> && docker-compose build"
```

## Step 5: Configure Environment

Create `.env` file with production values:
```bash
ssh ai-agent@<ip> "cat > ~/projects/<project-name>/.env << 'EOF'
LOG_LEVEL=info
PORT=<port>
# Add other env vars
EOF"
```

For secrets, use NHI vault:
```bash
# On LXC, the app should read from vault at runtime
# Don't put secrets in .env file!
```

## Step 6: Start Service

```bash
ssh ai-agent@<ip> "cd ~/projects/<project-name> && docker-compose up -d"
```

## Step 7: Verify Deployment

### Check container running
```bash
ssh ai-agent@<ip> "docker ps | grep <project-name>"
```

### Check health endpoint
```bash
curl http://<ip>:<port>/health
```

### Check logs
```bash
ssh ai-agent@<ip> "docker-compose -f ~/projects/<project-name>/docker-compose.yaml logs -f --tail=50"
```

## Step 8: Enable Auto-restart

Ensure container restarts on reboot:
```yaml
# In docker-compose.yaml
services:
  app:
    restart: unless-stopped
```

Or create systemd service (optional for critical services).

## Step 9: Register in NHI

If not already done, run `/register-service` workflow.

## Step 10: Verify NHI Integration

Wait for context regeneration (hourly) or force:
```bash
ssh ai-agent@192.168.1.117 "source /opt/nhi-core/venv/bin/activate && python3 /opt/nhi-core/core/context/updater.py"
```

Check `.cursorrules` includes the new service.

## Rollback Procedure

If deployment fails:

```bash
# Stop failing container
ssh ai-agent@<ip> "cd ~/projects/<project-name> && docker-compose down"

# If previous version exists
ssh ai-agent@<ip> "cd ~/projects/<project-name> && git checkout <previous-tag> && docker-compose up -d --build"
```

## Completion Checklist

- [ ] Container built successfully
- [ ] Service started on target LXC
- [ ] Health endpoint accessible
- [ ] Logs show no errors
- [ ] Auto-restart configured
- [ ] Registered in NHI
- [ ] Appears in .cursorrules

---

*Service is now deployed and integrated with NHI*
