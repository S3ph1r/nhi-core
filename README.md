# NHI-CORE

**Neural Home Infrastructure - Control Plane**

Transforms a vanilla Ubuntu VM into a documented, self-aware Control Plane for Proxmox homelab.

## Quick Start

### 👶 Humans (First Time Setup)
Start here if you have a fresh Proxmox server:
👉 **[Getting Started Guide](docs/GETTING_STARTED.md)**

### 🤖 AI Agents (Zero-Touch Bootstrap)
If you are an AI Agent, read this protocol:
👉 **[Agent Protocol](docs/AGENTS.md)**

---

### Manual Install (Legacy)
```bash
# On a fresh Ubuntu 22.04/24.04 VM
curl -sL https://raw.githubusercontent.com/S3ph1r/nhi-core/main/genesis.sh | sudo bash
```

## Features

- 🔍 **Auto-Discovery** - Scans Proxmox infrastructure via API
- 🕵️ **Runtime Scanning** - Deep inference of dependencies via SSH/TCP analysis
- 📝 **AI Context Generation** - Creates `.cursorrules` and `system-map.json` for AI assistants
- 🔐 **Secrets Management** - SOPS/Age encrypted credentials
- 🚀 **Automated Deploy** - One-command deployment of standardized AI-ready containers
- ⏰ **Self-Healing** - Hourly sync job keeps context fresh

## Documentation & Catalog

For a detailed map of the codebase and system architecture, see:
👉 **[System Catalog & Architecture](docs/CATALOG.md)**

Start here:
- 👶 **[Getting Started Guide](docs/GETTING_STARTED.md)** (Humans)
- 🤖 **[Agent Protocol](docs/AGENTS.md)** (AI Agents)

## Quick Architecture Overview

```
/opt/nhi-core/           # Application code
├── genesis.sh           # Bootstrap installer
├── core/
│   ├── api/             # FastAPI Backend
│   ├── context/         # System Map & Sync
│   ├── inference/       # Runtime Scanner (SSH)
│   ├── registry/        # YAML Registry Manager
│   └── project/         # Scaffolding Engine
└── scripts/             # Operational Tools (Deploy, Fix, Sync)

/var/lib/nhi/            # Data Governance
├── registry/            # Service Definitions (YAML)
├── context/             # System State (JSON)
├── secrets/             # Encrypted Credentials (SOPS)
└── age/                 # Encryption Keys
```
/var/log/nhi/            # Logs
├── install.log          # Installation log
└── cron.log             # Hourly update log
```

## Requirements

- Ubuntu 22.04 or 24.04
- Network access to Proxmox (port 8006)
- Proxmox API Token with appropriate permissions

## License

MIT
