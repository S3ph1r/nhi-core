# 📚 NHI-CORE System Catalog & Architecture

This document serves as the **official map** of the NHI-CORE codebase and deployment ecosystem.

## 🏗️ Codebase Structure (`nhi-core-code`)

The repository follows a modular architecture centered around `core/`.

```
nhi-core-code/
├── core/                       # 🧠 MAIN LOGIC MODULES
│   ├── api/                    # FastAPI application & Routers
│   ├── context/                # System Map Builder & Sync logic
│   ├── inference/              # Runtime dependency scanner (SSH-based)
│   ├── project/                # Project Scaffolding engine
│   ├── registry/               # Service Registry Manager (YAML handling)
│   ├── scanner/                # Legacy scanner components
│   └── templates/              # Jinja2 & YAML templates for scaffolding
│
├── scripts/                    # 🛠️ OPERATIONAL SCRIPTS (Use these!)
│   ├── deploy_complete.py      # Automates Service Deployment (LXC+User+SSH)
│   ├── setup_ssh_access.py     # Fixes SSH keys on existing containers
│   └── sync_catalog.py         # Hourly task to refresh system map
│
├── schemas/                    # 📐 JSON SCHEMAS
│   ├── service-manifest.json   # Validation for Service Registry
│   └── project-manifest.json   # Validation for Project Manifests
│
├── docs/                       # 📘 DOCUMENTATION
│   └── scripts/                # Detailed guides (specs, how-tos)
│
├── templates/                  # 📄 STATIC ASSETS templates
├── genesis.sh                  # 🚀 BOOTSTRAP SCRIPT (Installer)
└── requirements.txt            # Python dependencies
```

## 🧩 Components Description

### 1. Genesis (`genesis.sh`)
The master installer. It handles:
- OS preparation (dependencies, users)
- Security setup (Age keys, SOPS config)
- Repository cloning
- Service installation (systemd services, timers)
- **Do not edit manually** unless changing installation logic.

### 2. Context Engine (`core/context/`)
Aggregates truth from multiple sources:
- **Proxmox**: List of running LXCs via `pct list`.
- **Registry**: Static YAML definitions.
- **Runtime**: Dynamic connection data from `inference`.
- **Output**: Generates `/var/lib/nhi/context/system-catalog.json`.

### 3. Inference Engine (`core/inference/`)
Performs "Active Discovery":
- SSHs into containers.
- Runs `ss -tn` to see TCP connections.
- Infers dependencies based on open ports.
- **Key Method**: `scan_service_runtime()`.

### 4. Registry Manager (`core/registry/`)
The interface to the static truth:
- Reads/Writes YAML files in `/var/lib/nhi/registry/`.
- Validates against JSON Schemas.

### 5. Project Scaffolder (`core/project/`)
Standardizes development:
- Creates new folders with `pyproject.toml` / `package.json`.
- Initializes Git.
- Creates `project_manifest.yaml`.

---

## 💾 Data Governance (Filesystem)

On the deployed machine, data lives in standard paths:

| Path | Purpose | Format |
|------|---------|--------|
| `/var/lib/nhi/registry/services/` | **Service Definitions**. The strict "What should be". | YAML |
| `/var/lib/nhi/context/` | **System State**. The computed "What is". | JSON |
| `/var/lib/nhi/secrets/` | **Encrypted Secrets**. Passwords/Tokens. | SOPS/Age |
| `/var/lib/nhi/age/` | **Encryption Keys**. (Protect closely). | Binary |
| `/var/log/nhi/` | **Logs**. | Text |

## 🤖 Operational Workflows

### How to Deploy a New Service
**DO NOT** create LXCs manually. Use the standard script:
```bash
python3 scripts/deploy_complete.py --name <name> --vmid <id> --ip <ip>
```
*See `.agent/workflows/deploy_service.md` for full procedure.*

### How to Update the System
The system updates itself hourly via `nhi-sync.timer`, but you can force it:
```bash
python3 scripts/sync_catalog.py
```

### How to Fix Broken SSH
If runtime scanning fails:
```bash
python3 scripts/setup_ssh_access.py --password <root-password>
```
