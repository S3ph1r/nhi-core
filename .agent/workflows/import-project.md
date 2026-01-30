---
description: How to import and adapt an external project design to NHI standards
---

# Import Project Workflow

This workflow guides you through validating and adapting a project designed externally (e.g., by ChatGPT, Claude, or user documentation).

## Prerequisites

- [ ] Have the external project design/document
- [ ] Read `nhi-data/docs/NHI_STANDARDS_CHECKLIST.md`

## Step 1: Receive External Design

Ask user to provide:
- Project design document (md, txt, or paste)
- Any existing code (if applicable)
- Target deployment info (LXC, port)

## Step 2: Analyze Against Standards

Run through `NHI_STANDARDS_CHECKLIST.md`:

### Security Analysis
```bash
# If code exists, check for:
grep -rn "password\|secret\|api_key" --include="*.py" --include="*.js"
grep -rnE "192\.168\.[0-9]+\.[0-9]+" --include="*.py" --include="*.yaml"
```

### Structure Analysis
- [ ] Does it have a manifest equivalent?
- [ ] Is there a health endpoint planned?
- [ ] Is deployment containerized?

### Tech Stack Analysis
- [ ] Are technologies on approved list?
- [ ] Are there unnecessary dependencies?
- [ ] Is it over-engineered for the use case?

## Step 3: Generate Compliance Report

Create a report for the user:

```markdown
# Compliance Report: <Project Name>

**Analyzed:** <Date>
**Source:** <External LLM / User Design>

## ✅ Compliant
- Item 1
- Item 2

## ⚠️ Requires Adaptation

| Issue | Current Design | NHI Standard | Proposed Change |
|-------|---------------|--------------|-----------------|
| Example | Uses MySQL | PostgreSQL centralized | Connect to 192.168.1.105:5432 |

## ❌ Blocking Issues

| Issue | Problem | Required Action |
|-------|---------|-----------------|
| Example | API keys in code | Move to NHI vault before proceeding |

## Recommendation
<PROCEED / REQUIRES CHANGES / BLOCKED>
```

## Step 4: Discuss with User

Present the compliance report and explain:
1. **Why** each change is needed
2. **What** the NHI equivalent is
3. **How** it will be implemented

Get explicit approval before proceeding.

## Step 5: Apply Adaptations

For each required adaptation:

### Hardcoded Credentials → Vault
```python
# Before (bad)
DB_PASSWORD = "secret123"

# After (good)
import subprocess
DB_PASSWORD = subprocess.run(
    ["nhi", "vault", "get", "db/password"],
    capture_output=True
).stdout.decode().strip()
```

### Hardcoded IPs → Registry
```python
# Before (bad)
POSTGRES_HOST = "192.168.1.105"

# After (good)
import yaml
with open("/var/lib/nhi/config.yaml") as f:
    config = yaml.safe_load(f)
POSTGRES_HOST = config.get("services", {}).get("postgresql", {}).get("ip")
```

### Missing Health Endpoint → Add
Add `/health` endpoint returning service status.

### Non-standard Port → Allocate
Assign port from 8100-8199 range and document in manifest.

## Step 6: Create NHI Structure

Once adaptations are approved:

1. Create project following `/new-project` workflow
2. Import adapted code into structure
3. Create manifests
4. Test locally

## Step 7: Final Validation

Re-run checklist to confirm all issues resolved:

```bash
# Quick validation
test -f project_manifest.md && echo "✅ Manifest"
test -f docker/Dockerfile && echo "✅ Dockerfile"
grep -q ".env" .gitignore && echo "✅ Secrets protected"
```

## Completion Checklist

- [ ] Compliance report generated
- [ ] User approved adaptations
- [ ] All MUST requirements met
- [ ] All blocking issues resolved
- [ ] Project structure matches NHI standard
- [ ] Ready for deploy-service workflow

---

*Proceed with deploy-service workflow when ready*
