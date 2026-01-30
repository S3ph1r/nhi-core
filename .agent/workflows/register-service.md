---
description: How to register a service in the NHI service registry
---

# Register Service Workflow

This workflow guides you through registering a new service in the NHI service registry.

## Prerequisites

- [ ] Service is deployed and running
- [ ] Health endpoint responding
- [ ] Know the LXC ID, IP, and port

## Step 1: Gather Service Information

Collect the following:

| Field | Value | Example |
|-------|-------|---------|
| Service name | `<service-name>` | `invoice-tracker` |
| Description | `<description>` | `Invoice tracking and management API` |
| Version | `<version>` | `1.0.0` |
| LXC ID | `<lxc-id>` | `120` |
| IP Address | `<ip>` | `192.168.1.120` |
| Port(s) | `<ports>` | `8100` |
| Dependencies | `<deps>` | `postgresql, redis` |
| Health endpoint | `<health>` | `/health` |
| Owner | `<owner>` | `ai-agent` |

## Step 2: Create Service Manifest

Create manifest file in the registry:

```bash
# On NHI-CORE (LXC 117) or via SSH
mkdir -p /var/lib/nhi/registry/services/
cat > /var/lib/nhi/registry/services/<service-name>.yaml << 'EOF'
# NHI Service Manifest
# Generated: <date>

service:
  name: "<service-name>"
  description: "<description>"
  version: "<version>"

deployment:
  type: "docker"
  lxc_id: <lxc-id>
  ip: "<ip>"
  ports:
    - <port>

health:
  endpoint: "<health-endpoint>"
  interval: "30s"
  timeout: "10s"

dependencies:
  - <dependency-1>
  - <dependency-2>

owner: "<owner>"
status: "active"

metadata:
  created: "<date>"
  updated: "<date>"
  repository: "<git-repo-url-if-applicable>"
EOF
```

## Step 3: Validate Manifest

Check YAML syntax:
```bash
python3 -c "import yaml; yaml.safe_load(open('/var/lib/nhi/registry/services/<service-name>.yaml'))"
```

## Step 4: Verify Health Endpoint

```bash
curl -s http://<ip>:<port><health-endpoint>
```

Expected response:
```json
{
  "status": "healthy",
  "version": "<version>"
}
```

## Step 5: Trigger Context Regeneration

Option A: Wait for hourly cron job

Option B: Force immediate update
```bash
ssh ai-agent@192.168.1.117 "source /opt/nhi-core/venv/bin/activate && python3 /opt/nhi-core/core/context/updater.py"
```

## Step 6: Verify Registration

Check `.cursorrules` on M: drive:
```bash
cat /home/ai-agent/.cursorrules | grep "<service-name>"
```

The service should appear in the "Deployed Services Registry" section.

## Step 7: Update Project Manifest

In the project's `project_manifest.md`, add:

```markdown
## NHI Registration

- **Registered:** Yes
- **Manifest:** `/var/lib/nhi/registry/services/<service-name>.yaml`
- **Visible in:** `.cursorrules`
```

## Service Manifest Schema

For reference, the complete manifest schema:

```yaml
service:
  name: string          # Required: service identifier
  description: string   # Required: what the service does
  version: string       # Required: semver version

deployment:
  type: string          # Required: docker, systemd, or native
  lxc_id: integer       # Required: target LXC ID
  ip: string            # Required: service IP address
  ports:                # Required: list of exposed ports
    - integer

health:
  endpoint: string      # Required: health check path
  interval: string      # Optional: check frequency (default: 30s)
  timeout: string       # Optional: check timeout (default: 10s)

dependencies:           # Optional: list of required services
  - string

owner: string           # Required: responsible user
status: string          # Required: active, maintenance, deprecated

metadata:
  created: string       # Required: creation timestamp
  updated: string       # Required: last update timestamp
  repository: string    # Optional: git repository URL
  documentation: string # Optional: docs URL
```

## Completion Checklist

- [ ] Service manifest created
- [ ] YAML syntax valid
- [ ] Health endpoint verified
- [ ] Context regenerated
- [ ] Service appears in .cursorrules
- [ ] Project manifest updated

---

*Service is now registered and visible to all AI agents*
