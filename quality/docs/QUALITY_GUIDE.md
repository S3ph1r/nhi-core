# NHI Quality Assurance – Guida rapida

## Obiettivo
Ogni commit deve passare i controlli base senza errori; l'agente lo eseguirà per te.

## Comandi
```bash
make qa     # verifica solo
make fix    # auto-fix + prettier
make clean  # pulisci cache
```

## Regole attive (step 0 – base)
- Python: ruff (E,F,I) + mypy (non-strict)
- JS/CSS: prettier (default) + eslint raccomandato

## Prossimi step (step 1 – strict)
- Aggiungere type hints → mypy strict
- Aggiungere ruff rules: UP, ANN, B

## Dove cambiare le regole
Edita `pyproject.toml` o `.eslintrc.json` nel template, poi riesegui il playbook.