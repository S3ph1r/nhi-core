# 🔄 NHI Git Workflow Guide

> **⚠️ CRITICAL**: Questo documento distingue tra **sviluppo framework** (NHI-CORE) e **sviluppo progetti** utente. Non sono la stessa cosa!

---

## 🎯 Contesti di Lavoro

### Tipo A: Sviluppo NHI-CORE (Framework System)
**⚡ Solo per modifiche al framework NHI-CORE stesso**
- **Path**: `/opt/nhi-core` 
- **Repository GitHub**: `https://github.com/S3ph1r/nhi-core`
- **Branch**: `main`
- **Token**: Pre-configurato in SOPS (`/var/lib/nhi/secrets/services/github.yaml`)
- **Workflow**: **AUTOMATICO** - ogni ora via cron (se ci sono modifiche)
- **Chi**: Sistema automatico + sviluppatori framework (raro)

### Tipo B: Sviluppo Progetti Utente (User Projects)
**🚀 Per tutti i progetti che usano NHI-CORE come framework**
- **Path**: `/home/ai-agent/projects/<nome-progetto>`
- **Repository GitHub**: **Repo separato e indipendente** per ogni progetto
- **Branch**: `main` (standard GitHub)
- **Token**: **Condividi lo stesso PAT** di NHI-CORE
- **Workflow**: **MANUALE su richiesta** 
- **Chi**: Tutti gli utenti che sviluppano con NHI-CORE

---

## 🔧 Setup Repository per Nuovo Progetto

### 1. Crea Repository GitHub (Web Interface)
1. Vai su [https://github.com/new](https://github.com/new)
2. **Repository name**: `nhi-<nome-progetto>` (es: `nhi-dashboard`)
3. **Description**: Descrivi il progetto
4. **Public/Private**: Scegli in base alle esigenze
5. **Initialize**: ☑️ Add a README.md ☑️ Add .gitignore (Python/Node)
6. Clicca **"Create repository"**

### 2. Recupera GitHub Token (da SOPS)
```bash
# Decrypt il token condiviso di NHI-CORE
cd /var/lib/nhi
sops --decrypt secrets/services/github.yaml
# Copia il valore: github_token: ghp_xxxxxxxxxxxxxxxxxxxx
```

### 3. Configura Repository Locale
```bash
cd /home/ai-agent/projects/<nome-progetto>

# Configura Git user (se non già fatto)
git config user.name "NHI Agent"
git config user.email "agent@nhi.core"

# Aggiungi remote con token
# Sostituisci GITHUB_TOKEN con il valore copiato
git remote add origin https://GITHUB_TOKEN@github.com/TUO_USERNAME/nhi-<nome-progetto>.git

# Verifica
 git remote -v
```

### 4. Push Iniziale
```bash
# Se il repo GitHub ha README (ha già commit)
git pull origin main --allow-unrelated-histories
git branch --set-upstream-to=origin/main main

# Se repo vuoto (nessun commit)
git push -u origin main
```

---

## ⚙️ Funzionamento Automatico NHI-CORE

Il framework `/opt/nhi-core` ha **sincronizzazione automatica** ogni ora:

### 🔁 Processo Automatico
- **Script**: `/opt/nhi-core/core/context/updater.py` (via cron)
- **Frequenza**: Ogni ora
- **Trigger**: Modifiche in `/var/lib/nhi/` (data directory)
- **Log**: `/var/log/nhi/cron.log`
- **Azione**: Auto-commit + push se ci sono modifiche

### 📊 Cosa viene sincronizzato automaticamente:
- `/var/lib/nhi/context/` (system-map, catalog, etc.)
- `/var/lib/nhi/registry/` (service manifests)
- Files generati da scanner Proxmox

### ⚠️ Cosa NON viene sincronizzato automaticamente:
- `/opt/nhi-core/` (codice framework) - **Richiede push manuale**
- Progetti utente in `/home/ai-agent/projects/` - **Sempre manuali**

---

## 🔄 Workflow Standard per Progetti

### 📋 Pre-Flight Check (Ogni modifica)
1. **Verifica contesto**: Sei in `/home/ai-agent/projects/<nome>`?
2. **Check status**: `git status`
3. **Pull latest**: `git pull origin main` (se collaborativo)
4. **Crea branch** per feature complesse: `git checkout -b feature/nome`

### 🔄 Ciclo di Sviluppo
```bash
# 1. Fai le tue modifiche...

# 2. Stage changes
git add -A

# 3. Commit con messaggio descrittivo
git commit -m "feat: aggiunto sistema di logging"
# Alternative: git commit -m "fix: corretto bug timezone" 
# Alternative: git commit -m "docs: aggiornata documentazione API"

# 4. Push quando sei pronto
git push origin main
# Se su branch feature: git push origin feature/nome
```

### 🎯 Messaggi Commit (Convenzione)
- `feat:` Nuova funzionalità
- `fix:` Correzione bug  
- `docs:` Documentazione
- `style:` Formattazione/CSS
- `refactor:` Ristrutturazione codice
- `test:` Test aggiunti/modificati

---

## ⚡ Quick Reference per Agent

### Comandi Git Essenziali
```bash
# Status check
git status

# Vedere ultimi commit
git log --oneline -5

# Vedere differenze
git diff

# Annulare modifiche non committate
git restore .

# Vedere remote configurati
git remote -v

# Cambiare branch
git checkout main
```

### Troubleshooting Comune
```bash
# Errore: "Your branch is behind 'origin/main' by X commits"
git pull origin main

# Errore: "Please tell me who you are"
git config user.name "NHI Agent"
git config user.email "agent@nhi.core"

# Errore: "Permission denied (publickey)"
# → Usa HTTPS con token, non SSH
```

---

## 🔄 Workflow NHI-CORE (Framework)

**⚠️ ATTENZIONE**: Il framework ha sincronizzazione AUTOMATICA! Vedi sezione sopra.

**Push manuale solo per modifiche dirette al codice** (raro, pericoloso):

```bash
cd /opt/nhi-core

# 1. Verifica modifiche
git status

# 2. Decrypt token (se necessario)
sops --decrypt /var/lib/nhi/secrets/services/github.yaml

# 3. Add e commit
git add -A
git commit -m "feat: descrizione modifica framework"

# 4. Push
git push origin main
```

---

## 📋 Checklist per Agent

### ✅ Prima di Iniziare
- [ ] So se sto lavorando su **framework** (`/opt/nhi-core`) o **progetto** (`/home/ai-agent/projects/`)
- [ ] Ho il GitHub token da SOPS (`/var/lib/nhi/secrets/services/github.yaml`)
- [ ] Il repository remoto è configurato (`git remote -v`)

### ✅ Durante Sviluppo  
- [ ] Frequnti commit con messaggi descrittivi
- [ ] Test locali prima di push
- [ ] Documentazione aggiornata (se necessario)

### ✅ Prima di Push
- [ ] `git status` pulito (nessun file untracked importante)
- [ ] `git pull origin main` fatto (se collaborativo)
- [ ] Messaggio commit è descrittivo

---

## 🎨 Personalizzazione per Progetti

### Project Manifest Git Integration
Aggiungi al `project_manifest.yaml`:
```yaml
repository:
  type: git
  url: "https://github.com/TUO_USERNAME/nhi-nomeprogetto"
  branch: main
  auto_push: false  # Manuale per controllo completo
```

### Pre-commit Hooks (Opzionale)
Crea `.git/hooks/pre-commit` per QA automatica:
```bash
#!/bin/bash
# Esempio: run tests before commit
make test
```

---

## 📞 Supporto

Se hai problemi:
1. **Verifica token**: `sops --decrypt /var/lib/nhi/secrets/services/github.yaml`
2. **Verifica remote**: `git remote -v`  
3. **Verifica branch**: `git branch -a`
4. **Controlla status**: `git status`

Per modifiche al **framework NHI-CORE**: usa `/opt/nhi-core` con estrema cautela!
Per **tutto il resto**: usa progetti separati in `/home/ai-agent/projects/`