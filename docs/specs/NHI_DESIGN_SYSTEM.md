\*\*Documento: NHI Design System Architecture (NHIDS)\*\*

Ecco il documento organico da inserire nel repository NHI-CORE. Definisce l'infrastruttura che permette ai tuoi agenti di generare frontend coerenti e di propagare automaticamente gli aggiornamenti stilistici a tutto l'ecosistema.

\---

\`\`\`markdown  
\# NHI Design System Architecture (NHIDS)  
\#\# Documento di Governance Tecnica

\*\*Versione:\*\* 1.0    
\*\*Stato:\*\* Architetturale    
\*\*Dipendenza:\*\* NHI-CORE v1.0+    
\*\*Percorso:\*\* \`/var/lib/nhi/docs/NHI\_DESIGN\_SYSTEM.md\`

\---

\#\# 1\. Filosofia: "The Inherited Canvas"

NHIDS non è una libreria CSS, ma un \*\*protocollo di ereditarietà stilistica\*\*. Ogni progetto generato da un agente NHI non "possiede" il proprio design, ma \*\*noleggia uno stile\*\* dal Core Centrale.

\*\*Principio fondamentale:\*\*  
\> "L'aspetto visivo è proprietà dell'infrastruttura, non del singolo progetto."

Questo significa che:  
\- Un progetto non può definire colori, font o spazi propri  
\- Un progetto dichiara solo quale "Personalità" eredita (Layout Pattern)  
\- Aggiornare lo stile nel Core aggiorna automaticamente tutti i progetti (cascata controllata)

\---

\#\# 2\. Architettura: Struttura del Registro

Il Design System risiede nel \`Service Registry\` di NHI-CORE come servizio meta-infrastrutturale.

\#\#\# 2.1 Alberatura File System

\`\`\`  
/var/lib/nhi/  
├── design-system/                  \# Directory dedicata NHIDS  
│   ├── core/                       \# INVARIANTE \- Solo Core Team/AI  
│   │   ├── tokens.yaml             \# Design tokens universali (colori, spazi, type)  
│   │   ├── primitives.css          \# CSS reset \+ utility atomiche  
│   │   ├── validation.schema.json  \# Schema per validare manifest progetti  
│   │   └── version.lock            \# Versione corrente del Core  
│   │  
│   ├── personalities/              \# ESTENSIBILE \- Pattern di layout  
│   │   ├── \_schema.yaml            \# Schema validazione nuove personalità  
│   │   ├── obsidian/  
│   │   │   ├── manifest.yaml       \# Metadati \+ constraints  
│   │   │   ├── layout.css          \# Grids, zones, responsive rules  
│   │   │   ├── components.json     \# Lista componenti disponibili  
│   │   │   └── examples/           \# Screenshot/HTML esempi per AI  
│   │   ├── glass/  
│   │   │   └── \[stessa struttura\]  
│   │   └── \[future-personality\]/  
│   │  
│   ├── overrides/                  \# Patch temporanee (hotfix stilistici)  
│   │   └── YYYY-MM-DD-patch.yaml  
│   │  
│   └── registry.index.yaml         \# Mappa personalità disponibili  
│  
└── templates/  
    └── frontend/                   \# Template scaffolding  
        ├── nhi-base/               \# Skeleton progetto (invariante)  
        └── adapters/               \# Script binding personalità  
\`\`\`

\#\#\# 2.2 Core vs. Personalities

| Livello | Proprietà | Modificabile da | Impatto |  
|---------|-----------|-----------------|---------|  
| \*\*Core\*\* (\`design-system/core/\`) | Universalità | Solo manutenzione NHI | Breaking changes globali |  
| \*\*Personalities\*\* (\`personalities/\*\`) | Specificità layout | Contributors/Agents | Nuovi pattern o varianti |  
| \*\*Overrides\*\* (\`overrides/\`) | Emergenze | Hotfix automatici | Temporaneo, rollback automatico |

\---

\#\# 3\. Protocollo di Ereditarietà

Quando un agente scaffolda un nuovo frontend, deve seguire la \*\*"Inheritance Chain"\*\* (Catena di Ereditarietà).

\#\#\# 3.1 Flusso di Generazione

\`\`\`  
Progetto Richiesto (es. "App Finanza")  
        ↓  
\[Classifier NHI\] → Determina Personalità: "obsidian"  
        ↓  
Scaffold Frontend:  
├── 1\. Copia /templates/frontend/nhi-base/ (struttura file base)  
├── 2\. Inject dependencies:  
│   ├── Core: \<link rel="stylesheet" href="/nhi/core/tokens.css"\>  
│   ├── Personality: \<link rel="stylesheet" href="/nhi/personalities/obsidian/layout.css"\>  
│   └── Project-specific: app.css (SOLO override funzionali, mai stilistici)  
└── 3\. Genera manifest.progetto.yaml (dichiara: personality: obsidian v1.2)  
\`\`\`

\#\#\# 3.2 Vincoli Inviolabili (Hard Constraints)

Ogni progetto generato \*\*DEVE\*\* includere nel proprio manifest:

\`\`\`yaml  
\# project\_manifest.yaml (generato automaticamente)  
frontend:  
  inherits:  
    core\_version: "1.0"           \# Blocca versione Core usata  
    personality: "obsidian"       \# Nome personalità  
    personality\_version: "1.2"    \# Versione specifica (per retrocompatibilità)  
    
  constraints:  
    custom\_css\_allowed: false     \# Vietato scrivere CSS arbitrario  
    theme\_modifications: \[\]       \# Lista vuota \= nessuna deviazione consentita  
    component\_overrides: \[\]       \# Se vuoto, usa componenti stock  
    
  validation:  
    last\_check: "2026-02-01T10:00:00Z"  
    status: "compliant"           \# "compliant" | "deprecated" | "invalid"  
\`\`\`

\*\*Regole per gli Agenti:\*\*  
1\. \*\*Mai hardcode colori\*\*: Se l'AI scrive \`color: \#ff0000\`, il validator lo rifiuta.  
2\. \*\*Mai definire nuovi spazi\*\*: Usare solo \`var(--nhi-space-\*)\`.  
3\. \*\*Mai includere framework UI esterni\*\*: (Bootstrap, Material, Tailwind arbitrario). Solo NHIDS \+ Tailwind configurato con i token NHI.  
4\. \*\*Mai modificare i file Core\*\*: Sono read-only anche per l'admin.

\---

\#\# 4\. Governance: Aggiungere o Modificare Personalità

NHIDS è \*\*estensibile\*\* ma \*\*controllato\*\*. Ecco le regole per evolverlo.

\#\#\# 4.1Aggiungere una Nuova Personalità

\*\*Workflow di Proposta (Personality Request):\*\*

1\. \*\*Analisi del Dominio\*\*: L'agente (o utente) verifica che il nuovo use case non rientri nelle 4 esistenti.  
   \- Caso limite: "Editor di testo collaborativo" → rientra in "Blueprint" (dev tools)  
   \- Caso nuovo: "Videogame retro-emulator interface" → necessita nuova personalità "Arcade"

2\. \*\*Creazione Schema\*\*: Creare \`/var/lib/nhi/design-system/personalities/\[nome\]/manifest.yaml\`:

\`\`\`yaml  
\# Esempio: personalities/arcade/manifest.yaml  
personality:  
  id: "arcade"  
  name: "Retro Interactive"  
  version: "1.0.0"  
  created: "2026-02-01"  
  status: "experimental"  \# experimental | stable | deprecated  
    
  use\_cases:  
    \- "gaming-interfaces"  
    \- "interactive-kiosks"  
    \- "simulation-controls"  
    
  inherits\_core: true      \# DEVE essere true (non bypassabile)  
    
  constraints:  
    max\_complexity: "high" \# low | medium | high  
    responsive\_mode: "adaptive" \# fixed | adaptive | fluid  
      
  components\_available:  
    \- "neon-button"  
    \- "scanline-panel"  
    \- "crt-canvas"  
    \# Ogni componente deve essere definito in components.json  
    
  validations:  
    \# Regole che il linter applicherà ai progetti che usano questa personalità  
    required\_meta\_tags:  
      \- "viewport-fit=cover"  
    forbidden\_properties:  
      \- "font-family"  \# Arcade usa sempre font monospace forzata da Core  
\`\`\`

3\. \*\*Validazione\*\*: Il sistema esegue:  
   \- Check duplicati (id univoco)  
   \- Check dipendenze (tutti i componenti referenziati esistono?)  
   \- Check contrasti (accessibility WCAG 2.1 AA automatica sui token ereditati)

4\. \*\*Registrazione\*\*: Aggiunta in \`registry.index.yaml\`:

\`\`\`yaml  
personalities:  
  \- id: "obsidian"  
    status: "stable"  
    version: "1.2.0"  
  \- id: "glass"   
    status: "stable"  
    version: "1.1.0"  
  \- id: "arcade"  
    status: "experimental"  
    version: "1.0.0"  
    available\_to\_agents: false  \# Solo utente umano può assegnarla finché experimental  
\`\`\`

\#\#\# 4.2 Modificare una Personalità Esistente

\*\*Regole di versioning (Semantic Versioning for UI):\*\*

| Cambiamento | Esempio | Azione su Progetti Esistenti |  
|-------------|---------|------------------------------|  
| \*\*Patch\*\* (1.0.0 → 1.0.1) | Fix z-index, correzione colore hover | Auto-update notturno, messaggio in log |  
| \*\*Minor\*\* (1.0.x → 1.1.0) | Nuovo componente aggiunto, nuova utility class | Notifica agente, update opzionale (flag \--update-ui) |  
| \*\*Major\*\* (1.x → 2.0.0) | Cambio grid system, rimozione componente, rename classi | \*\*Blocco\*\*: i progetti vecchi restano su v1.x, devi migrare manualmente |

\*\*Meccanismo di propagazione:\*\*

\`\`\`python  
\# Pseudo-codice del NHI Update Manager  
def propagate\_style\_update(personality\_id, old\_version, new\_version):  
    projects \= registry.get\_projects\_using(personality\_id, old\_version)  
      
    if is\_major\_update(old\_version, new\_version):  
        \# Non toccare i progetti esistenti  
        mark\_as\_deprecated(personality\_id, old\_version)  
        notify\_admins(f"Nuova major version di {personality\_id} disponibile. {len(projects)} progetti da migrare.")  
    else:  
        \# Auto-apply a tutti i compliant  
        for project in projects:  
            if project.manifest.validation.status \== "compliant":  
                update\_symlink(project, new\_version)  
                regenerate\_context(project)  
\`\`\`

\---

\#\# 5\. Meccanismo di Aggiornamento Automatico

Ogni progetto scaffoldato include un \*\*"NHI UI Agent"\*\* — un micro-servizio (o script cron) che mantiene il collegamento con il Core.

\#\#\# 5.1 Il file \`.nhi-ui-config\` (in ogni progetto)

\`\`\`json  
{  
  "core\_endpoint": "http://192.168.1.110:8080/design-system",  
  "update\_policy": "auto-minor",  // auto-all | auto-minor | manual-only  
  "current\_personality": "obsidian",  
  "lock\_version": false,  
  "last\_sync": "2026-02-01T00:00:00Z"  
}  
\`\`\`

\#\#\# 5.2 Flusso di Update

1\. \*\*Check\*\*: Ogni giorno (o su webhook dal Core), il progetto chiede: "C'è una nuova versione di Obsidian?"  
2\. \*\*Valutazione\*\*:   
   \- Se patch → download automatico, refresh CSS  
   \- Se minor → segnala all'agente AI nella prossima interazione: "Aggiornamento UI disponibile. Applicare? (Y/n)"  
   \- Se major → non fare nulla, ma blocca future auto-update finché non si crea un branch di migrazione  
3\. \*\*Rollback\*\*: Se un update rompe il layout, comando: \`nhi-ui rollback \--to=previous\` ripristina il symlink alla versione precedente.

\---

\#\# 6\. Interfaccia per gli Agenti AI

Per garantire che gli agenti rispettino NHIDS, il \`.cursorrules\` di ogni progetto include queste direttive aggiuntive:

\`\`\`markdown  
\#\# NHI Design System Protocol

\*\*QUANDO GENERI UI:\*\*  
1\. \*\*Identifica la Personalità\*\*: Usa il campo \`frontend.inherits.personality\` dal \`project\_manifest.yaml\`.  
   \- Se mancante, default: "obsidian" (per tool interni) o "nova" (per user-facing landing).

2\. \*\*Includi sempre\*\*:  
   \- \`\<link rel="stylesheet" href="/nhi/core/tokens.css"\>\` (primo nell'\<head\>)  
   \- \`\<link rel="stylesheet" href="/nhi/personalities/{personality}/layout.css"\>\` (secondo)

3\. \*\*VINCOLI CSS\*\*:  
   \- Vietato usare colori hex arbitrari. Solo \`var(--nhi-color-\*)\`.  
   \- Vietato definire \`@keyframes\` personalizzati. Usa quelli del Core.  
   \- Vietato media-query arbitrarie. Usa i breakpoint del Core (\`--nhi-breakpoint-sm\`, etc.).

4\. \*\*COMPONENTI\*\*:  
   \- Prima di creare un componente custom, verifica se esiste in \`/nhi/personalities/{personality}/components/\`.  
   \- Se serve un componente nuovo, definiscilo in \`local\_components/\` MA eredita dai primitives del Core.

5\. \*\*VALIDAZIONE\*\*:  
   \- Dopo ogni modifica frontend, esegui: \`nhi-ui validate\`  
   \- Se fallisce, fix immediato prima di commit.

\*\*COMANDI DISPONIBILI:\*\*  
\- \`nhi-ui switch-personality \[nome\]\` → Cambia personalità del progetto (richiede refactoring)  
\- \`nhi-ui check-updates\` → Verifica nuove versioni disponibili  
\- \`nhi-ui validate\` → Controlla conformità al Design System  
\`\`\`

\---

\#\# 7\. Casi d'Uso: Esempi Operativi

\#\#\# Esempio A: Nuovo Progetto Finance  
1\. Utente: "Crea app portafogli"  
2\. Agente: Classifica come "data-heavy" → assegna \`personality: obsidian\`  
3\. Agente: Crea symlink \`current-personality → /var/lib/nhi/design-system/personalities/obsidian/v1.2/\`  
4\. Risultato: Progetto parte con stile coerente

\#\#\# Esempio B: Evoluzione stilistica globale  
1\. Decidi che tutti i bottoni devono avere border-radius 4px invece di 6px (tutte le personalità)  
2\. Modifichi \`/design-system/core/tokens.css\` (variabile \`--nhi-radius-sm\`)  
3\. \*\*Propagazione\*\*:  
   \- Progetti con \`update\_policy: auto-minor\` → aggiornati stanotte  
   \- Progetti \`manual-only\` → flag "update disponibile" nel loro context AI  
4\. \*\*Rollback possibile\*\*: Se un progetto si rompe, \`nhi-ui pin-core-version 1.0\` lo blocca alla versione precedente

\#\#\# Esempio C: Aggiunta nuova Personalità "Medical"  
1\. Nuovo use case: interfaccia per monitoring salute (graph medici, precisione alta)  
2\. Crea \`personalities/medical/\` con varianti colori accessibili (alto contrasto per lettura dati clinici)  
3\. Registri come \`status: experimental\`  
4\. Solo progetti espliciti possono usarla: \`--personality=medical \--experimental\`

\---

\#\# 8\. Checklist Implementazione in NHI-CORE

Per rendere operativo questo sistema nel tuo scaffolding:

\- \[ \] Creare directory \`/var/lib/nhi/design-system/\` nelLXC Brain  
\- \[ \] Definire \`tokens.yaml\` iniziale (palette scura coordinata con Proxmox)  
\- \[ \] Scrivere \`validation.schema.json\` per linter automatico  
\- \[ \] Modificare \`manifest\_generator.py\` per includere sezione \`frontend.inherits\`  
\- \[ \] Aggiungere comando CLI: \`nhi design-system list\` (mostra personalità disponibili)  
\- \[ \] Aggiungere comando CLI: \`nhi design-system validate \[project-path\]\`  
\- \[ \] Integrare check nel cron NHI: "verifica che tutti i progetti frontend siano compliant"  
\- \[ \] Documentare nel \`.cursorrules\` globale i vincoli Design System

\---

\*\*Conclusione\*\*

NHIDS trasforma il design da "decisione estetica ad-hoc" a "infrastruttura versionata". Gli agenti non scelgono più come deve apparire un'app, ma \*\*dichiarano solo cosa deve fare\*\*; l'aspetto è determinato dal ruolo (personalità) scelta. Questo garantisce che tra 20 progetti, tutto sembri parte dello stesso ecosistema NHI, pur servendo domini completamente diversi.

\`\`\`

\---

Questo documento fornisce il telaio operativo. Gli agenti che leggeranno questo protocollo sapranno che non possono più "improvvisare" lo stile, ma devono attingere dal registro centrale. Vuoi che approfondisca qualche sezione specifica, come il meccanismo di validazione automatica o il sistema di versioning delle personalità?  
