---
description: How to create a new NHI-compliant project from scratch
---

# New Project Workflow

This workflow guides you through creating a new project that follows NHI standards.

## Prerequisites

- [ ] Read `nhi-data/docs/NHI_METHODOLOGY.md`
- [ ] Know the project purpose and requirements
- [ ] Have target LXC ID and IP allocated

## Step 1: Gather Requirements

Ask the user:
1. **Project name** (lowercase, hyphenated): e.g., `invoice-tracker`
2. **Purpose**: One sentence description
3. **Tech stack**: See `nhi-data/docs/TECH_STACK.md` for options
4. **Target LXC**: ID and IP address
5. **Port number**: Check registry for available ports (8100-8199 range)

## Step 2: Create Project Structure

```bash
# Create directories
mkdir -p <project-name>/{src,tests,docs,docker}
mkdir -p <project-name>/.agent/workflows

# Copy templates
cp nhi-data/templates/project/* <project-name>/
cp nhi-data/templates/service-manifest.yaml <project-name>/service-manifest.yaml
```

## Step 3: Initialize Project Manifest

Edit `project_manifest.md` with gathered information:

```markdown
# <Project Name>

## Overview
<One sentence description>

## Technical Details
- **LXC ID:** <ID>
- **IP:** <IP>
- **Port:** <Port>
- **Stack:** <Python/FastAPI | Node/Express | etc.>

## Dependencies
- <List centralized services used>

## Status
- Created: <Date>
- Last Updated: <Date>
- Status: Development
```

## Step 4: Configure Docker

Edit `docker/Dockerfile` for the chosen stack.
Edit `docker/docker-compose.yaml` with correct ports and labels.

## Step 5: Create Basic Application

For **Python/FastAPI**:
```python
# src/main.py
from fastapi import FastAPI

app = FastAPI(title="<Project Name>")

@app.get("/health")
async def health():
    return {"status": "healthy", "version": "0.1.0"}
```

For **Node/Express**:
```javascript
// src/index.js
const express = require('express');
const app = express();

app.get('/health', (req, res) => {
    res.json({ status: 'healthy', version: '0.1.0' });
});

app.listen(process.env.PORT || 3000);
```

## Step 6: Initialize Git

```bash
cd <project-name>
git init
echo ".env
*.pyc
__pycache__/
node_modules/
.venv/
" > .gitignore
git add .
git commit -m "Initial project setup"
```

## Step 7: Local Test

```bash
docker-compose up --build
curl http://localhost:<port>/health
```

Verify health endpoint returns `{"status": "healthy"}`.

## Step 8: Register in NHI

Run workflow: `/register-service`

## Completion Checklist

- [ ] Project structure created
- [ ] project_manifest.md filled
- [ ] Dockerfile working
- [ ] Health endpoint responds
- [ ] Git initialized
- [ ] Service registered in NHI

---

*Continue with deploy-service workflow when ready for deployment*
