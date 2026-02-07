# NHI Standards Checklist

> **Purpose:** Quick validation reference for new and imported projects  
> **Usage:** AI agents use this to validate external project designs before implementation

---

## ✅ MUST (Non-Negotiable)

These are **mandatory** requirements. Projects failing these CANNOT be deployed.

### Security

| Requirement | Check | Why |
|-------------|-------|-----|
| No hardcoded credentials | `grep -r "password\|secret\|token" --include="*.py" --include="*.js"` should be empty | Credentials must be in vault |
| No hardcoded IPs | `grep -rE "192\.168\.[0-9]+\.[0-9]+" --include="*.py" --include="*.yaml"` allowed only in config | Use registry/DNS |
| Environment-based config | `.env.example` exists, `.env` in `.gitignore` | Secrets never committed |
| Vault integration | Uses `nhi vault get` or reads from `/var/lib/nhi/secrets/` | Centralized secret management |

### Structure

| Requirement | Check | Why |
|-------------|-------|-----|
| Project manifest exists | `project_manifest.md` in root | NHI integration metadata |
| Service manifest ready | YAML file for registry | Enables auto-discovery |
| README present | `README.md` with setup instructions | Documentation requirement |
| Health endpoint | `GET /health` returns status | Monitoring and orchestration |

### Deployment

| Requirement | Check | Why |
|-------------|-------|-----|
| Dockerfile present | Production-ready container | Consistent deployment |
| Non-root execution | Container runs as non-root user | Security best practice |

### Quality Assurance

| Requirement | Check | Why |
|-------------|-------|-----|
| QA tools configured | `make qa` exits 0 | Prevents regressions, enforces style |
| QA templates present | `/opt/nhi-core/quality-template` copied | Standardized lint/type-check rules |
| Port documented | Port number in manifest | Avoid conflicts |

---

## ⚠️ SHOULD (Strongly Recommended)

Deviations require justification and user approval.

### Architecture

| Requirement | Alternative | Why |
|-------------|-------------|-----|
| Use approved tech stack | Must justify deviation | Maintainability |
| Centralized database | Embedded DB for small projects | Resource efficiency |
| Structured logging (JSON) | Plain text with clear format | Log aggregation |
| Prometheus metrics | Custom metrics endpoint | Standard monitoring |

### Code Quality

| Requirement | Alternative | Why |
|-------------|-------------|-----|
| Type hints (Python) | Docstrings with types | IDE support |
| TypeScript (Node) | JSDoc annotations | Type safety |
| Unit tests | Integration tests minimum | Regression prevention |
| Linting configured | Manual review | Consistent style |

### Operations

| Requirement | Alternative | Why |
|-------------|-------------|-----|
| docker-compose for local dev | Makefile with commands | Easy onboarding |
| Multi-stage Docker build | Simple Dockerfile for dev | Smaller images |
| Graceful shutdown handling | Basic signal handling | Clean termination |

---

## 💡 MAY (Optional but Recommended)

Nice-to-have features that improve project quality.

| Feature | Benefit |
|---------|---------|
| CI/CD pipeline configuration | Automated testing and deployment |
| OpenAPI/Swagger documentation | Interactive API docs |
| Architecture Decision Records (ADRs) | Track design decisions |
| Performance benchmarks | Baseline metrics |
| Backup/restore procedures | Disaster recovery |
| Rate limiting | API protection |
| Retry logic with backoff | Resilience |

---

## 🔄 Import Project Validation

When analyzing an external project design, generate a report:

### Compliance Report Template

```markdown
# Compliance Report: [Project Name]

**Analyzed:** [Date]
**Source:** [External LLM / User document]

## ✅ Compliant

- [x] Uses Docker for deployment
- [x] Has README documentation
- [x] API design follows REST conventions

## ⚠️ Requires Adaptation

| Issue | Current | NHI Standard | Proposed Change |
|-------|---------|--------------|-----------------|
| Database config | Hardcoded connection string | Vault secret | Read from `nhi vault get db/connection` |
| Port number | 3000 | Must be in 8100-8199 range | Change to 8100 |
| Logging | Plain text | JSON structured | Add structlog |

## ❌ Blocking Issues

| Issue | Problem | Required Action |
|-------|---------|-----------------|
| Embedded secrets | API keys in source code | MUST be removed before proceeding |

## Recommendation

[PROCEED with adaptation / BLOCK until fixed / REVIEW with user]
```

---

## 🎯 Quick Validation Commands

```bash
# Check for hardcoded secrets
grep -rn "password\|secret\|api_key" --include="*.py" --include="*.js" --include="*.yaml"

# Check for hardcoded IPs (should only be in config files)
grep -rnE "192\.168\.[0-9]+\.[0-9]+" --include="*.py" --include="*.yaml"

# Verify project manifest
test -f project_manifest.md && echo "✅ Manifest exists" || echo "❌ Missing manifest"

# Verify README
test -f README.md && echo "✅ README exists" || echo "❌ Missing README"

# Verify Dockerfile
test -f Dockerfile -o -f docker/Dockerfile && echo "✅ Dockerfile exists" || echo "❌ Missing Dockerfile"

# Check for .env in gitignore
grep -q ".env" .gitignore && echo "✅ .env in gitignore" || echo "⚠️ .env not in gitignore"
```

---

## 📋 Pre-Deployment Final Check

Before deploying any service, verify:

```markdown
## Deployment Readiness Checklist

### Required
- [ ] Project manifest created
- [ ] Service manifest ready for registry
- [ ] Health endpoint implemented and tested
- [ ] No secrets in codebase
- [ ] Port allocated and documented
- [ ] README with setup instructions

### Verified
- [ ] Builds successfully (docker build .)
- [ ] Starts without errors (docker-compose up)
- [ ] Health check passes (curl /health)
- [ ] Logs are readable and structured

### Registered
- [ ] Service manifest added to NHI registry
- [ ] Await context regeneration (or force: `python3 /opt/nhi-core/core/context/updater.py`)
- [ ] Verify service appears in .cursorrules
```

---

*NHI Standards Checklist v1.0 - Ensuring quality and compliance*
