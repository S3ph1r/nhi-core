# Tutorial: Building the NHI Dashboard 🚀
> **Obiettivo:** Creare la "First Visual Interface" per l'ecosistema NHI, validando l'intero stack (Design System, API, Metodologia).

Questo tutorial ti guida passo-passo nella creazione della **NHI Dashboard** trattandola come un vero "Progetto Cliente". Non useremo scorciatoie privilegiate: useremo gli strumenti standard che NHI fornisce a tutti gli sviluppatori.

---

## 🧭 Mappa del Viaggio

1.  **Preparazione API**: Dare voce al Core (Backend).
2.  **Genesi Progetto**: Scaffolding del nuovo repo.
3.  **Design Injection**: Vestire l'app con la personalità "Flux".
4.  **Wiring**: Collegare Frontend e Backend.

---

## Fase 1: Dare voce al Cervello (The Core API)

Prima di visualizzare i dati, dobbiamo poterli leggere. NHI-CORE è una libreria Python; per parlarci dal web, serve un'API.

**Domanda Guida:** *Come esponiamo le funzioni sicure del Core al mondo esterno?*
**Risposta:** Creando un layer FastAPI dentro `nhi-core`.

### Passi Operativi:

1.  **Installa FastAPI nel Core:**
    Spostati nel repo `nhi-core` ed esegui:
    ```bash
    pip install fastapi uvicorn
    ```
    *(Nota: Questo deve essere aggiunto anche a `requirements.txt` o `setup_dependencies` nel seme)*.

2.  **Crea l'Entry Point:**
    In `core/api/main.py`:
    ```python
    from fastapi import FastAPI
    from core.backup import BackupManager
    
    app = FastAPI(title="NHI Brain API")
    
    @app.get("/system/status")
    def get_status():
        # ... logica scanner ...
    ```

3.  **Avvia il Server (Daemon):**
    Dobbiamo creare un servizio systemd o un container Docker per tenere l'API sempre accesa.
    *Suggerimento:* Per ora usiamo `systemd` sul layer LXC base.

---

## Fase 2: Il Primo Respiro (Project Genesis)

Ora lasciamo il Core e diventiamo "Sviluppatori Client". Creiamo il contenitore per la nostra Dashboard.

**Domanda Guida:** *Dove deve vivere questo progetto?*
**Risposta:** In una cartella/repo separata, es. `~/Projects/nhi-dashboard`.

### Passi Operativi:

1.  **Crea il Progetto:**
    ```bash
    mkdir -p ~/Projects/nhi-dashboard
    cd ~/Projects/nhi-dashboard
    npm create svelte@latest .
    ```
    *Seleziona: Skeleton project, TypeScript (opzionale ma consigliato), No ESLint/Prettier per ora.*

2.  **Self-Awareness (Il Manifesto):**
    Ogni progetto NHI deve sapere chi è. Crea `project_manifest.yaml`:
    ```yaml
    name: nhi-dashboard
    type: frontend-app
    purpose: "Visual control plane for NHI ecosystem"
    dependencies:
      - nhi-core-api
    ```

---

## Fase 3: Vestirsi per l'Occasione (Design System)

Qui avviene la magia. Non scriveremo CSS da zero.

**Domanda Guida:** *Che aspetto deve avere?*
**Risposta:** Produttivo, dark, neon. Personalità: **Flux**.

### Passi Operativi:

1.  **Installa Tailwind:**
    ```bash
    npx svelte-add@latest tailwindcss
    npm install
    ```

2.  **Inject Personality (Il tocco magico):**
    Usiamo la CLI di NHI per configurare lo stile.
    ```bash
    nhi design init --personality flux
    ```
    *Questo scaricherà `tailwind.config.js` pre-configurato con i token Flux.*

3.  **Verifica Visiva:**
    Nella pagina `+page.svelte`, prova a usare classi semantiche NHI:
    ```html
    <div class="bg-surface text-text-primary p-8 border border-border rounded-radius-md">
       <h1 class="text-accent-primary font-bold">Hello Flux</h1>
    </div>
    ```

---

## Fase 4: La connessione (Wiring)

Il Frontend è bello ma vuoto. Colleghiamolo al Backend.

### Passi Operativi:

1.  **Variabili d'Ambiente:**
    Crea `.env`:
    ```ini
    PUBLIC_API_URL=http://192.168.1.117:8000
    ```

2.  **Fetch Data:**
    In `src/routes/+page.svelte`:
    ```javascript
    onMount(async () => {
        const res = await fetch(`${env.PUBLIC_API_URL}/system/status`);
        const data = await res.json();
    });
    ```

---

## ✅ Checklist Finale

- [ ] L'API risponde su `:8000`?
- [ ] La Dashboard si apre su `:3000`?
- [ ] Lo stile è "Linear-dark" (Flux)?
- [ ] Vedo i dati reali del server?

Se hai risposto SÌ a tutto, hai creato il primo vero progetto dell'era NHI v1.1! 🎉
