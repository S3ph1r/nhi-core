# NHI-CORE Implementation Guide v1.1

> **Versione:** 1.1 (Adattata per rete 192.168.1.x)
> **Data:** 2026-01-29
> **Stato:** APPROVATO - Pronto per implementazione

---

## Indice Componenti

| # | Componente | Priorità | Stato |
|---|------------|----------|-------|
| 1 | Age Key Management | P1 | ⬜ Da fare |
| 2 | CoreDNS Service Discovery | P1 | ⬜ Da fare |
| 3 | Dependency Graph | P2 | ⬜ Da fare |
| 4 | IP Allocation Registry | P1 | ⬜ Da fare |
| 5 | Schema Validation | P2 | ⬜ Da fare |
| 6 | OpenTofu Templates | P1 | ⬜ Da fare |
| 7 | Reconciliation | P3 | ⬜ Da fare |
| 8 | Disaster Recovery | P2 | ⬜ Da fare |

---

## 1. Age Key Management - Strategia Gerarchica

### 1.1 Architettura a 3 Livelli

| Chiave | Scopo | Gestione |
|--------|-------|----------|
| **Master Key** | Disaster recovery, può decifrare TUTTO | Backup manuale obbligatorio (USB) |
| **Host Key** | Infrastructure secrets (Proxmox API, SSH) | Auto-generata, backup via Master |
| **Services Key** | Application secrets (DB passwords, API tokens) | Auto-generata, backup via Master |

### 1.2 Struttura Filesystem

```
/var/lib/nhi/age/
├── master.key           # BACKUP OBBLIGATORIO
├── master.key.pub
├── host.key             # Auto-generated
├── host.key.pub
├── services.key         # Auto-generated
└── services.key.pub
```

### 1.3 Configurazione SOPS

File `/var/lib/nhi/.sops.yaml`:

```yaml
creation_rules:
  # Infrastructure secrets (Proxmox, SSH)
  - path_regex: secrets/infrastructure/.*.yaml$
    age: >-
      age1master...,
      age1host...

  # Application secrets (DB, APIs)
  - path_regex: secrets/services/.*.yaml$
    age: >-
      age1master...,
      age1services...
```

### 1.4 Workflow Genesis - Backup Obbligatorio

Durante `genesis.sh`, l'installazione si BLOCCA richiedendo all'utente di salvare la Master Key.
L'utente deve digitare esattamente `I HAVE SAVED THE KEY` per continuare.

---

## 2. CoreDNS - Service Discovery

### 2.1 IP Statico

- **IP:** `192.168.1.53` (porta DNS standard = mnemonica)
- **Questo è l'UNICO servizio con IP hardcoded** per evitare il bootstrap paradox

### 2.2 Configurazione CoreDNS

```
# Corefile
. {
    forward . 8.8.8.8 1.1.1.1
    cache 30
    log
}

home {
    file /etc/coredns/db.home
    log
}
```

### 2.3 Zone File `/etc/coredns/db.home`

```
$ORIGIN home.
@       IN  SOA dns.home. admin.home. (
            2026012901 ; serial
            3600       ; refresh
            1800       ; retry
            604800     ; expire
            86400 )    ; minimum

        IN  NS  dns.home.

dns         IN  A   192.168.1.53
nhi-brain   IN  A   192.168.1.110
jellyfin    IN  A   192.168.1.114
postgres    IN  A   192.168.1.105
```

---

## 3. IP Allocation Registry

### 3.1 Struttura File

`/var/lib/nhi/network/ip-allocations.yaml`:

```yaml
reserved:
  192.168.1.1:
    description: Router/Gateway
    type: infrastructure
  192.168.1.2:
    description: Proxmox Host
    type: infrastructure
  192.168.1.53:
    description: CoreDNS
    type: service
    service_name: coredns
  192.168.1.110:
    description: NHI-CORE Brain
    type: infrastructure

allocated:
  192.168.1.105:
    service: db-shared
    type: lxc
    manifest: registry/services/db-shared.yaml
  192.168.1.114:
    service: jellyfin
    type: lxc
    manifest: registry/services/jellyfin.yaml

pool:
  start: 192.168.1.120
  end: 192.168.1.199
  next_available: 192.168.1.120
```

---

## 4. Service Manifest Schema

### 4.1 Esempio Manifest

`/var/lib/nhi/registry/services/jellyfin.yaml`:

```yaml
name: jellyfin
type: lxc
vmid: 114

resources:
  cpu: 2
  memory_mb: 2048
  disk_gb: 10

network:
  ip: 192.168.1.114
  ports:
    - port: 8096
      protocol: tcp
      description: "Web UI"

mounts:
  - source: "//192.168.1.139/VIDEO"
    target: "/mnt/media-pc"
    type: smb
    credentials: "vault:smb.jellyfin"

dependencies:
  required: []
  optional: []

healthcheck:
  type: http
  endpoint: "http://192.168.1.114:8096/health"
  interval: 60

checklist:
  lxc_created: true
  service_installed: true
  ports_configured: true
  manifest_created: true
  healthcheck_defined: true
  docs_updated: false

created: "2026-01-29T20:00:00"
updated: "2026-01-29T20:00:00"
```

---

## 5. Repository Structure

```
nhi-core/
├── genesis.sh              # Bootstrap entry point
├── install.py              # Python orchestrator
├── requirements.txt
├── README.md
│
├── core/
│   ├── __init__.py
│   ├── config.py
│   │
│   ├── bootstrap/
│   │   ├── system_prep.py  # Apt packages install
│   │   ├── storage_setup.py # Bind mount config
│   │   └── git_setup.py    # Git repo init
│   │
│   ├── scanner/
│   │   └── proxmox_client.py # API wrapper
│   │
│   ├── context/
│   │   ├── generator.py    # .cursorrules gen
│   │   ├── standards.py    # Port allocation rules
│   │   └── updater.py      # Cron update script
│   │
│   ├── registry/           # NEW
│   │   ├── manifest_generator.py
│   │   ├── scanner.py
│   │   └── checklist.py
│   │
│   ├── templates/
│   │   ├── lxc/
│   │   │   └── main.tf     # OpenTofu template
│   │   └── docker/
│   │       ├── fastapi/
│   │       ├── nodejs/
│   │       └── postgres/
│   │
│   └── security/
│       ├── age_manager.py  # Age key ops
│       └── vault.py        # SOPS wrapper
│
├── scripts/
│   ├── allocate_ip.sh
│   ├── deps_graph.py
│   ├── reconcile.py
│   └── validate_manifest.py
│
└── schemas/
    └── service-manifest.json
```

---

## 6. Versioning Roadmap

### v1.0 Foundation (CURRENT)
- [x] genesis.sh bootstrap
- [ ] Age key management gerarchico
- [ ] CoreDNS service discovery
- [ ] IP allocation registry
- [ ] Service manifest + JSON Schema validation
- [ ] OpenTofu templates (LXC)
- [ ] Reconciliation approval workflow
- [ ] Context statico (.cursorrules)

### v2.0 Dynamic Context (FUTURE)
- [ ] Context API REST
- [ ] Dashboard Web
- [ ] Reconciliation hybrid mode
- [ ] Vector DB per semantic search

### v3.0+ Intelligence (VISION)
- [ ] Distributed agents
- [ ] Auto-healing avanzato
- [ ] Predictive resource scaling

---

## Prossimi Passi Implementazione

1. **Step 1:** Implementare Age Key Management in `genesis.sh`
2. **Step 2:** Creare modulo `core/registry/` per manifest
3. **Step 3:** Aggiornare `context/generator.py` per includere servizi
4. **Step 4:** Creare IP Allocation Registry
5. **Step 5:** Deployare CoreDNS (LXC 53)
6. **Step 6:** Testare workflow completo con nuovo servizio

---

*Documento pronto per implementazione passo-passo*
