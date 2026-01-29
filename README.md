# NHI-CORE

**Neural Home Infrastructure - Control Plane**

Transforms a vanilla Ubuntu VM into a documented, self-aware Control Plane for Proxmox homelab.

## Quick Start

```bash
# On a fresh Ubuntu 22.04/24.04 VM
curl -sL https://raw.githubusercontent.com/S3ph1r/nhi-core/main/genesis.sh | sudo bash
```

## Features

- 🔍 **Auto-Discovery** - Scans Proxmox infrastructure via API
- 📝 **AI Context Generation** - Creates `.cursorrules` and `system-map.json` for AI assistants
- 🔐 **Secrets Management** - SOPS/GPG encrypted credentials
- 📁 **SMB Share** - Access from Windows via RaiDrive
- ⏰ **Hourly Updates** - Cron job keeps context fresh

## Architecture

```
/opt/nhi-core/           # Application code
├── genesis.sh           # Bootstrap script
├── core/
│   ├── scanner/         # Proxmox API client
│   ├── context/         # AI context generator
│   ├── security/        # SOPS integration
│   └── templates/       # LXC/VM blueprints

/var/lib/nhi/            # Persistent data (bind-mount to Proxmox host)
├── config.yaml          # Configuration
├── context/
│   ├── .cursorrules     # AI rules (Markdown)
│   └── system-map.json  # Machine-readable map
├── registry/            # Infrastructure inventory
├── secrets/             # Encrypted credentials
└── templates/           # User templates

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
