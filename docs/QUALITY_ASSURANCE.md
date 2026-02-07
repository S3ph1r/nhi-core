# ✅ Quality Assurance (QA)

> **Scope:** project-agnostic linting & type-checking rules for NHI-CORE ecosystem  
> **Path:** `/opt/nhi-core/quality-template/` (deployed via Ansible)

## 1. Quick Start

Inside any project folder:
```bash
# If you don't have QA files yet
cp -r /opt/nhi-core/quality-template/* .

# Check only
make qa

# Auto-fix + check
make fix
```

Exit code **0** = compliant; anything else = stop & fix.

## 2. Tools & Rules (Step 0 – Base)

| Language | Tool    | Rule-set               | Config file        |
|----------|---------|------------------------|--------------------|
| Python   | ruff    | E, F, I                | pyproject.toml     |
| Python   | mypy    | non-strict             | pyproject.toml     |
| JS/TS    | eslint  | eslint:recommended     | .eslintrc.json      |
| CSS/SCSS | prettier| default                | .prettierrc         |

Strict mode is commented-out; enable later by uncommenting `strict = true` in `pyproject.toml`.

## 3. CI / Local Parity

The same Makefile is used by:
- Local developers (`make qa`)
- GitHub Actions (`.github/workflows/qa.yml`)
- Genesys deployment (Ansible playbook `nhi-quality`)

## 4. Evolving the Rules

1. Edit templates in `nhi-core-code/quality/templates/`
2. Bump version in `Makefile`
3. Deploy: `ansible-playbook deploy/site.yml -t nhi-quality`
4. All projects receive the update on next `make qa`

## 5. Links

- Template source: [`/quality/templates/`](https://github.com/nhi-core/nhi-core/tree/main/quality/templates)  
- Ansible role: [`/deploy/roles/nhi-quality/`](https://github.com/nhi-core/nhi-core/tree/main/deploy/roles/nhi-quality)
- Standards checklist: [`NHI_STANDARDS_CHECKLIST.md`](NHI_STANDARDS_CHECKLIST.md)