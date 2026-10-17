# Analisi Agno per l'agent CRM AiChain

**Data:** 2026-10-14  
**Stato:** valutazione tecnica — nessuna implementazione  
**Fonti:** GitHub `agno-agi/agno`, docs.agno.com, PyPI `agno` (accesso 2026-10-14)

---

## 1. Executive summary

| Domanda | Risposta |
|---|---|
| Cos'è Agno? | Framework + runtime Python (Apache-2.0) per costruire e servire agent AI (SDK + AgentOS + UI) |
| Conviene usarlo al posto dell'agent custom? | **No, non ora** |
| Quanto costa integrarlo? | **~3–4 giorni** (solo SDK) · **1–2 settimane** (AgentOS completo) |
| Cosa fare invece? | Stabilizzare l'agent custom (LLM + parser) · rivalutare Agno se servono multi-agent / RAG / HITL |

L'agent CRM attuale (`crm_agent_service.py`) copre già 17 tool operativi, un parser deterministico italiano e un fallback offline. Il problema reale emerso in sviluppo è l'**affidabilità del LLM locale** (Bionic / Nemotron: `No models loaded`), non la mancanza di un framework. Agno risolve altri problemi (memory multi-turn, team, observability) e ne aggiunge di nuovi (dipendenze, migrazione major 3.x, complessità ops).

---

## 2. Panoramica Agno

### 2.1 Identità del progetto

| Voce | Valore |
|---|---|
| Repository | https://github.com/agno-agi/agno |
| Documentazione | https://docs.agno.com |
| License | **Apache-2.0** (compatibile con uso commerciale) |
| Stars / fork | ~42.7k / ~6.1k |
| Ultima release | **3.1.3** (12 ott 2026) |
| Python | >= 3.9, < 4 |
| Pacchetto PyPI | `agno` — wheel ~4.3 MB (core) |
| Maturità | Classifier `Development Status :: 5 - Production/Stable` |
| Telemetry | Attiva di default (solo metriche run, no prompt) — disabilitabile con `AGNO_TELEMETRY=false` |

### 2.2 Architettura a tre livelli

```
┌─────────────────────────────────────────────┐
│  Control Plane / AgentOS UI                 │  monitor, sessioni, audit
├─────────────────────────────────────────────┤
│  AgentOS (runtime)                          │  REST 50+ endpoint, SSE, MCP,
│                                             │  JWT RBAC, storage, scheduling
├─────────────────────────────────────────────┤
│  SDK (Agno / Claude / Codex)                │  Agent · Team · Workflow
└─────────────────────────────────────────────┘
```

- **SDK** (`agno`): primitive `Agent`, `Team`, `Workflow` + tool, memory, session, knowledge, guardrails, HITL, evals.
- **AgentOS**: servizio FastAPI che espone agent come API/MCP, con storage, auth, tracing.
- **Control Plane**: UI per gestire la piattaforma.

Per un CRM già FastAPI + MongoDB, l'unica opzione sensata è il **solo SDK** embedded; AgentOS è una piattaforma a sé.

### 2.3 Capacità rilevanti

| Capacità | Utile per AiChain CRM? |
|---|---|
| Tool-calling su modello OpenAI-compat | Sì — già fatto con litellm |
| 100+ toolkit (GitHub, Slack, Postgres…) | Poco — i tool CRM sono custom |
| Memory / session multi-turn | Sì, se il chat agent deve ricordare il contesto |
| Knowledge / RAG | Utile in futuro (documenti cliente, ZenTratto) |
| Guardrails + HITL | Utile se agent può inviare email / modificare deal |
| OTEL / audit | Utile in produzione enterprise |
| Scheduling | Già coperto da Cloud Tasks |
| MCP server | Non necessario ora |
| Interfacce Slack/WhatsApp | WhatsApp già implementato custom |

---

## 3. Stato agent attuale AiChain

**File principali**
- `backend/app/services/crm_agent_service.py` (~1800 righe)
- `backend/app/routers/crm_agent.py` (`/api/v1/agent/run`, `/tools`)
- `frontend/app/[locale]/crm/agent/page.tsx` (chat UI)

**Pattern**
1. **Parser deterministico italiano** — comandi tipo «crea lead…», «dammi il settore di…», «riepilogo CRM» (senza LLM)
2. **Tool-calling litellm** — 17 tool (create_lead, update_lead, find_lead, create_task, deal, email, report, book_demo, …)
3. **Fallback** — retry LLM + estrazione nome → `find_lead` + help

**Punti di forza**
- Funziona offline / con LLM rotto per i comandi strutturati
- Tool allineati ai servizi CRM esistenti (Mongo, Resend, activity log)
- Suite test 324 casi backend
- Nessuna dipendenza agent framework

**Punti deboli**
- LLM locale (Bionic `:1235`, model `nvidia/nemotron-3-nano-4b`) instabile: `No models loaded`
- Il modello 4B ignora spesso i `tool_calls` e «inventa» risposte
- Parser da estendere a mano per ogni nuovo intent
- No memoria conversazionale multi-turn
- No tracing strutturato delle run

---

## 4. Confronto

| Criterio | Agent custom | Agno SDK | Agno AgentOS |
|---|---|---|---|
| Tool CRM (17) | Già implementati | Riscrittura wrapper | Riscrittura + deploy |
| Parser IT deterministico | Solido | Da reimplementare | Da reimplementare |
| Fallback offline | Sì | Parziale | Parziale |
| Multi-turn / memory | No | Sì (built-in) | Sì |
| Observability | Log | OTEL optional | OTEL + UI |
| Nuove dipendenze | — | `agno[openai,mongodb]` | agno + Postgres + runtime |
| Vincolo dati UE | Pieno | OK (`AGNO_TELEMETRY=false`) | OK se self-host |
| Costo integrazione | 0 | **3–4 gg** | **1–2 settimane** |
| Costo infra | 0 | 0 | + Postgres / container |
| Lock-in | Nessuno | Basso (Apache-2) | Medio (platform) |
| Rischio principale | Manutenzione interna | API 3.x instabile | Complessità ops |

---

## 5. Costi di inclusione nel codice

### Opzione A — Solo SDK Agno nel backend (minima)

| Attività | Stima |
|---|---|
| `pip install "agno[openai,mongodb]"` + pin compatibili (`httpx`, `openai`) | 0.5 gg |
| Wrappare i 17 tool come tool Agno | 1–2 gg |
| Sostituire `_run_llm` con `Agent(model=OpenAILike(...), tools=[...])` | 0.5 gg |
| Conservare parser + fallback | 0.5 gg |
| Allineare suite test (324) | 1 gg |
| **Totale** | **~3–4 giorni** |

**Costi runtime:** +~5–10 MB dipendenze · nessun servizio in più  
**Rischi:** release 3.x con breaking frequenti (molti tag 3.0.x in agosto-ottobre 2026) · verificare compatibilità con `openai==2.54` e `httpx==0.27` già pinnati

### Opzione B — AgentOS separato

| Attività | Stima |
|---|---|
| Template `agentos-docker` / `agentos-gcp` | 1 gg |
| Postgres + migrazione sessioni | 2 gg |
| Integrazione auth Firebase JWT + RBAC | 2–3 gg |
| Collegamento tool CRM al runtime | 3 gg |
| Deploy, monitoring, hardening | 2–3 gg |
| **Totale** | **1–2 settimane** |

**Costi infra:** Postgres (o storage Agno) + container aggiuntivo · UI control plane  
**Verdetto:** sproporzionato rispetto al bisogno.

### Opzione C — Restare sull'agent custom *(raccomandata)*

| Attività | Stima |
|---|---|
| Prompt/tool_choice più aggressivi sul tool-calling | 0.5 gg |
| Retry + warmup modello LLM locale | 0.5 gg |
| Estendere parser agli intent mancanti | 0.5–1 gg |
| (Opzionale) memoria conversazionale leggera in Mongo | 1 gg |
| **Totale** | **~1–2 giorni** |

**Costi runtime:** 0 · **Dipendenze:** 0

---

## 6. Pro / contro di Agno per AiChain

### Pro
- Apache-2.0, community ampia, sviluppo attivo
- Memory, session, guardrails, HITL pronti all'uso
- Un solo SDK per agent/team/workflow se il prodotto cresce
- Storage MongoDB già supportato (extra `mongodb`)
- Dati restano self-host se non si usa la cloud Agno

### Contro
- Migrazione non banale di tool + parser + test
- Major 3.x giovane: API ancora in movimento
- Telemetry da disabilitare esplicitamente (compliance UE)
- Non risolve il vero pain point (LLM locale instabile / tool-call deboli)
- Aggiunge superficie di attacco e manutenzione di un framework esterno

---

## 7. Raccomandazione

### Non introdurre Agno in questa fase

1. Il valore del CRM agent è nei **tool sui dati** (lead, deal, task, email) e nel **parser italiano**: sono già implementati e testati.
2. I bug recenti («Non ho capito», «No models loaded») dipendono da **LLM + intent matching**, non dall'assenza di un framework.
3. AgentOS è una piattaforma completa: sproporzionata per un backend FastAPI monolitico già in produzione.
4. Anche il solo SDK costa 3–4 gg e introduce rischio di breaking change su Agno 3.x.

### Cosa fare invece (Opzione C)
1. Rendere più robusto il tool-calling (system prompt che forza l'uso dei tool per query CRM, `tool_choice`, max_tokens adeguati per modelli reasoning).
2. Tenere il parser come path primario per le azioni strutturate (deterministico, testabile, zero LLM).
3. Aggiungere memoria di conversazione leggera in Mongo se il chat deve ricordare turni precedenti.
4. Monitorare: se servono **Team multi-agente**, **RAG documenti**, **HITL su email/deal** → rivalutare Agno SDK.

### Trigger di rivalutazione
| Segnale | Azione |
|---|---|
| Marketing agent + CRM agent da coordinare | Agno `Team` / `Workflow` |
| RAG su contratti / documenti cliente | Agno `Knowledge` + vector store |
| Approvazione umana su azioni sensibili | Agno `Human-in-the-Loop` |
| Multi-tenant con audit UI | AgentOS + Control Plane |

---

## 8. Fonti

1. https://github.com/agno-agi/agno — README, license, feature list (accesso 2026-10-14)
2. https://docs.agno.com/introduction — architettura SDK / AgentOS / Control Plane
3. https://docs.agno.com/sdk/introduction — primitive Agent/Team/Workflow
4. https://pypi.org/project/agno/ — v3.1.3, Apache-2.0, extras, Python >=3.9
5. Codice interno: `backend/app/services/crm_agent_service.py`, `backend/app/routers/crm_agent.py`

---

*Documento prodotto per valutazione tecnica AiChain Solutions — non è un ADR finché non viene formalizzato in `docs/wiki/04_ADRs/`.*
