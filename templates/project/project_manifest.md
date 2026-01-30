# {{PROJECT_NAME}} - Project Manifest

> NHI-CORE Project Manifest v1.0

---

## Overview

**Name:** {{PROJECT_NAME}}  
**Description:** {{PROJECT_DESCRIPTION}}  
**Status:** Development | Active | Maintenance | Deprecated

---

## Technical Details

| Property | Value |
|----------|-------|
| **LXC ID** | {{LXC_ID}} |
| **IP Address** | {{IP}} |
| **Port** | {{PORT}} |
| **Stack** | {{TECH_STACK}} |
| **Repository** | {{REPO_URL}} |

---

## Dependencies

### Centralized Services

| Service | IP | Port | Usage |
|---------|-----|------|-------|
| PostgreSQL | 192.168.1.105 | 5432 | Primary database |
| Redis | TBD | 6379 | Cache/sessions |

### External APIs

| API | Purpose | Auth Method |
|-----|---------|-------------|
| - | - | - |

---

## Health & Monitoring

| Property | Value |
|----------|-------|
| **Health Endpoint** | `/health` |
| **Metrics Endpoint** | `/metrics` (Prometheus) |
| **Log Location** | `docker-compose logs` |

---

## Security

| Aspect | Implementation |
|--------|----------------|
| **Credentials** | NHI Vault (`/var/lib/nhi/secrets/`) |
| **Authentication** | JWT / API Key / None |
| **Authorization** | Role-based / None |

---

## Deployment

| Property | Value |
|----------|-------|
| **Method** | Docker Compose |
| **Image** | {{PROJECT_NAME}}:latest |
| **Auto-restart** | Yes (`unless-stopped`) |

---

## NHI Registration

| Property | Value |
|----------|-------|
| **Registered** | Yes / No |
| **Manifest Path** | `/var/lib/nhi/registry/services/{{PROJECT_NAME}}.yaml` |
| **In .cursorrules** | Yes / No |

---

## Changelog

| Date | Version | Changes |
|------|---------|---------|
| {{DATE}} | 0.1.0 | Initial creation |

---

## Contacts

| Role | User |
|------|------|
| **Owner** | ai-agent |
| **Maintainer** | {{USER}} |

---

*NHI-CORE Project Manifest - Auto-compliance with NHI standards*
