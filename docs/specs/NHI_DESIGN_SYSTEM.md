# NHI Design System Architecture (NHIDS)

## Documento di Governance Tecnica

**Versione:** 1.0  
**Stato:** Architetturale  
**Dipendenza:** NHI-CORE v1.0+  
**Percorso:** `/var/lib/nhi/docs/NHI_DESIGN_SYSTEM.md`

> 🧭 **System-wide Bible**:  
> Per architettura, moduli e processi vedi [`NHI-CORE_Implementation_Guide_v1.1.md`](NHI-CORE_Implementation_Guide_v1.1.md)

---

## 1. Filosofia: "The Inherited Canvas"

NHIDS non è una libreria CSS, ma un **protocollo di ereditarietà stilistica**. Ogni progetto generato da un agente NHI non "possiede" il proprio design, ma **noleggia uno stile** dal Core Centrale.