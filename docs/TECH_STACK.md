# NHI Technology Stack

> **Purpose:** Approved technologies and recommended alternatives  
> **Philosophy:** Standard choices reduce complexity, exceptions require justification

---

## 🎯 Primary Stack (Default Choices)

These are the **default recommendations**. Use these unless there's a specific reason not to.

### Backend

| Category | Primary Choice | Why |
|----------|---------------|-----|
| **Language** | Python 3.11+ | ML/AI ecosystem, rapid development |
| **Web Framework** | FastAPI | Modern, async, auto-docs, type hints |
| **Task Queue** | Celery + Redis | Proven, scalable background jobs |
| **ORM** | SQLAlchemy 2.0 | Async support, mature ecosystem |

### Frontend

| Category | Primary Choice | Why |
|----------|---------------|-----|
| **Framework** | React 18+ | Component model, large ecosystem |
| **Build Tool** | Vite | Fast HMR, modern bundling |
| **Styling** | Tailwind CSS 3 | Utility-first, consistent design |
| **State** | Zustand or Context | Simple, lightweight state |

### Data

| Category | Primary Choice | Why |
|----------|---------------|-----|
| **Relational DB** | PostgreSQL 16 | Centralized on LXC 105 |
| **Cache/Queue** | Redis | Centralized, versatile |
| **Vector DB** | ChromaDB | On LXC 101, for embeddings |
| **Object Storage** | MinIO | S3-compatible, on LXC 104 |

### Infrastructure

| Category | Primary Choice | Why |
|----------|---------------|-----|
| **Container** | Docker + docker-compose | Standard, reproducible |
| **Reverse Proxy** | Traefik or Nginx | TLS termination, routing |
| **Monitoring** | Prometheus + Grafana | On LXC 103 (observability) |
| **Secrets** | Age + SOPS | NHI native encryption |

---

## 🔄 Approved Alternatives

Use these when primary choice doesn't fit the use case.

### Backend Alternatives

| Instead of | Use | When |
|------------|-----|------|
| Python | **Node.js 20+** | Real-time, WebSocket heavy |
| Python | **Go** | High-performance, low-level |
| FastAPI | **Flask** | Simple APIs, minimal async needs |
| FastAPI | **Express.js** | Node.js preferred |
| Celery | **Dramatiq** | Simpler task queue needs |
| SQLAlchemy | **Prisma** | Node.js with strong types |

### Frontend Alternatives

| Instead of | Use | When |
|------------|-----|------|
| React | **Vue 3** | Simpler learning curve |
| React | **Svelte** | Minimal bundle size |
| React | **Vanilla JS** | Very simple UI needs |
| Tailwind | **CSS Modules** | Component-scoped styles |
| Tailwind | **styled-components** | CSS-in-JS preference |

### Data Alternatives

| Instead of | Use | When |
|------------|-----|------|
| PostgreSQL | **SQLite** | Embedded, single-user apps |
| Redis | **Memcached** | Pure caching, no persistence |
| ChromaDB | **Milvus** | Larger scale vector search |
| MinIO | **Local filesystem** | Simple file storage needs |

---

## ❌ Not Recommended

These technologies should be **avoided** unless there's a compelling reason.

| Technology | Reason | Alternative |
|------------|--------|-------------|
| MySQL/MariaDB | PostgreSQL already available | Use centralized PostgreSQL |
| MongoDB | Schema-less complexity | PostgreSQL with JSONB |
| Kubernetes | Over-engineering for homelab | Docker Compose |
| PHP | Legacy, different paradigm | Python or Node.js |
| jQuery | Outdated for modern UIs | Vanilla JS or React |
| Webpack (new projects) | Slower than alternatives | Vite |

---

## 📦 Centralized Services

These services are already deployed. **Use them, don't duplicate.**

| Service | IP | Port | Purpose | Use Case |
|---------|-----|------|---------|----------|
| PostgreSQL | 192.168.1.105 | 5432 | Relational DB | All SQL data |
| Redis | (TBD) | 6379 | Cache/Queue | Sessions, tasks |
| ChromaDB | 192.168.1.101 | 8000 | Vector DB | Embeddings, search |
| MinIO | 192.168.1.104 | 9000 | Object storage | Files, backups |
| Prometheus | 192.168.1.103 | 9090 | Metrics | Monitoring |
| Grafana | 192.168.1.103 | 3000 | Dashboards | Visualization |

---

## 🐳 Container Standards

### Python Dockerfile Template

```dockerfile
# Build stage
FROM python:3.11-slim as builder
WORKDIR /app
RUN pip install --no-cache-dir poetry
COPY pyproject.toml poetry.lock ./
RUN poetry export -f requirements.txt --output requirements.txt
RUN pip wheel --no-deps --wheel-dir /wheels -r requirements.txt

# Runtime stage
FROM python:3.11-slim
WORKDIR /app
RUN useradd -m -u 1000 appuser
COPY --from=builder /wheels /wheels
RUN pip install --no-cache /wheels/*
COPY --chown=appuser:appuser . .
USER appuser
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Node.js Dockerfile Template

```dockerfile
# Build stage
FROM node:20-alpine as builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Runtime stage
FROM node:20-alpine
WORKDIR /app
RUN adduser -D -u 1000 appuser
COPY --from=builder --chown=appuser:appuser /app/dist ./dist
COPY --from=builder --chown=appuser:appuser /app/node_modules ./node_modules
USER appuser
EXPOSE 3000
CMD ["node", "dist/index.js"]
```

---

## 📊 Evaluation Criteria

When choosing technology, consider:

| Factor | Weight | Questions |
|--------|--------|-----------|
| **Familiarity** | High | Do I/user know this? |
| **Ecosystem** | High | Are there good libraries? |
| **Maintenance** | Medium | Is it actively maintained? |
| **Performance** | Medium | Does it meet requirements? |
| **Complexity** | Medium | Is it over-engineered? |
| **Integration** | High | Does it work with NHI stack? |

---

## 🆕 Proposing New Technology

To add a new technology to the approved stack:

1. **Justify** - Why can't existing choices work?
2. **Evaluate** - How does it compare on the criteria above?
3. **Prototype** - Build a small proof of concept
4. **Document** - Add to this file with use case
5. **Review** - Discuss with user before adoption

---

*NHI Tech Stack v1.0 - Consistency through standardization*
