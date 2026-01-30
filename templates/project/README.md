# {{PROJECT_NAME}}

> {{PROJECT_DESCRIPTION}}

## Quick Start

```bash
# Clone and setup
git clone {{REPO_URL}}
cd {{PROJECT_NAME}}
cp .env.example .env

# Start with Docker
docker-compose up -d

# Verify
curl http://localhost:{{PORT}}/health
```

## Architecture

- **Stack:** {{TECH_STACK}}
- **Port:** {{PORT}}
- **LXC:** {{LXC_ID}} ({{IP}})

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/api/v1/...` | ... |

## Configuration

Environment variables (see `.env.example`):

| Variable | Description | Default |
|----------|-------------|---------|
| `PORT` | Server port | {{PORT}} |
| `LOG_LEVEL` | Logging level | `info` |

## Development

```bash
# Install dependencies
pip install -r requirements.txt  # Python
# or
npm install                       # Node.js

# Run locally
uvicorn main:app --reload        # Python/FastAPI
# or
npm run dev                      # Node.js
```

## Deployment

See `/deploy-service` workflow in `.agent/workflows/`.

## NHI Integration

- **Manifest:** `/var/lib/nhi/registry/services/{{PROJECT_NAME}}.yaml`
- **Health:** Monitored every 30s
- **Logs:** `docker-compose logs -f`

---

*Part of NHI-CORE ecosystem - Created {{DATE}}*
