# CRM Agent — Roadmap «vero agente» (ispirata ad Agno)

**Data:** 2026-10-14  
**Obiettivo:** un agente che gestisca **tutto il CRM** (lead, deal, task, email, fatture, report, inbox, …) in modo affidabile, multi-turno e sicuro.  
**Ispirazione:** pattern Agno (Agent/Team/Workflow, memory, hooks, HITL, guardrails, context) — **senza adottare il framework** (vedi `analisi-agno-agent.md`).

---

## 0. Gap analysis — oggi vs «tutto il CRM»

### Tool già presenti (18)
`create_lead` · `update_lead` · `find_lead` · `list_leads` · `create_task` · `reschedule_task` · `set_reminder` · `list_deadlines` · `create_deal` · `update_deal` · `list_deals` · `draft_email` · `send_email` · `notify` · `list_notifications` · `book_demo` · `crm_summary` · `generate_report` · `help`

### Moduli CRM **non** raggiungibili dall'agente

| Modulo | Router | Azioni mancanti |
|---|---|---|
| Task (completo) | `tasks.py`, `task_global.py` | list, complete, delete, assign |
| Attività | `activities.py` | list per lead, add note |
| Fatture | `invoices.py` | list, create, send, mark paid, PDF |
| Proposte | `proposals.py` | list, create, send, accept, reject |
| Prodotti / segmenti | `products.py` | list, price, segment |
| Content library | `content.py` | search, reuse, create |
| Template email | `email_templates.py` | list, render |
| Email sequence | `email_sequences.py` | enroll, status, pause |
| Competitors | `competitors.py` | scan, alerts |
| WhatsApp inbox | `whatsapp.py` | list conv, send reply |
| Calendar | `calendar.py` | eventi mese, bulk assign |
| Export | `export.py` | CSV lead/deal |
| Enrichment | `apollo.py` / enrichment | enrich lead, bulk |
| Marketing / Meta | `marketing_agent.py`, `meta_ads.py` | (separato, da coordinare) |
| GDPR | `gdpr.py` | export/erase (solo admin, con conferma) |
| Dashboard | `dashboard.py` | KPI dettagliati |
| Report | `reports.py` | list, delete, send email |

### Debolezze di comportamento (ispirate ad Agno)
| Aspetto | Stato | Pattern Agno di riferimento |
|---|---|---|
| Memoria multi-turno | Assente | `add_history_to_context`, sessions |
| Contesto utente/ruolo | Solo user_id | `dependencies` / context providers |
| Conferme azioni pericolose | Assente | Human-in-the-Loop |
| Validazione output | Minima | Guardrails |
| Audit delle run | Solo activity CRM | Tracing / observability |
| Tool organizzati per dominio | Lista piatta | Toolkits |
| Workflow multi-step | No | Workflows |
| Qualità risposte | Non misurata | Evals |

---

## 1. Task — Fase A · Fondamenta (affidabilità)

> **Priorità:** alta · **Stima:** 3–5 gg · **Goal:** l'agente risponde sempre, in modo tracciabile

| # | Task | Descrizione | Acceptance |
|---|---|---|---|
| A1 | **Session store Mongo** | Collezione `agent_sessions` con history turni (`userId`, `sessionId`, `messages[]`, `createdAt`) | Ultimi N turni iniettati nel prompt; TTL o max turni |
| A2 | **Context injection** | Prompt system con: ruolo utente, fuso orario, data odierna, ultima entità discussa («quel lead», «la fattura di ieri») | «Quel lead» risolve sull'ultimo nominato |
| A3 | **Run log** | Collezione `agent_runs`: messaggio, mode (parser/llm), tool eseguiti, latenza, errori | Dashboard/API `GET /agent/runs` (admin) |
| A4 | **LLM resilient** | Warmup modello, retry, timeout, metriche; se modello remoto usare provider da settings | Zero «Non ho capito» per domande su dati CRM |
| A5 | **Guardrail input/output** | Max lunghezza, blacklist PII in log, validazione email/numero prima dei tool | Input malevolo non scrive nel DB |
| A6 | **Modelli & prompt per tool-calling** | System prompt che *forza* l'uso dei tool per query su dati; `tool_choice` / funzioni native se supportate | «Email di X» → sempre `find_lead`, mai testo inventato |

**File tipici:** `crm_agent_service.py`, `agent_session_service.py` (nuovo), `models/agent.py`, `routers/crm_agent.py`

---

## 2. Task — Fase B · Copertura CRM (tutti i moduli)

> **Priorità:** alta · **Stima:** 5–8 gg · **Goal:** ogni entità CRM leggibile e scrivibile via agent

### B1 — Task & Attività
| Tool | Note |
|---|---|
| `list_tasks` | filtri: status, lead, scadenza |
| `complete_task` | chiudi / riapri |
| `delete_task` | soft delete + conferma |
| `add_activity` | nota/chiamata su lead |

### B2 — Lead (completamento)
| Tool | Note |
|---|---|
| `delete_lead` | soft delete, **HITL** |
| `import_leads_csv` | riferimento a file già caricato o pasted rows |
| `enrich_lead` | wrap Apollo/enrichment |
| `search_leads` | filtri status, score, settore, assegnatario |

### B3 — Deal & Pipeline
| Tool | Note |
|---|---|
| `delete_deal` | HITL |
| `move_deal_stage` | «sposta X in proposta» (già parziale) |
| `deal_pipeline` | valore per stage |

### B4 — Commerciale (proposte & fatture)
| Tool | Note |
|---|---|
| `list_proposals` / `create_proposal` | da prodotti + lead |
| `send_proposal` | HITL (invio email esterna) |
| `accept_proposal` / `reject_proposal` | |
| `list_invoices` / `create_invoice` | da proposta accettata |
| `send_invoice` / `mark_invoice_paid` | HITL su send |
| `get_document_pdf` | proposta/fattura |

### B5 — Marketing & contenuti
| Tool | Note |
|---|---|
| `list_products` / `list_segments` | |
| `search_content` / `create_content` | content library |
| `list_email_templates` / `render_template` | |
| `enroll_sequence` | iscrivi lead a sequenza |

### B6 — Comunicazioni
| Tool | Note |
|---|---|
| `list_whatsapp_conversations` | |
| `send_whatsapp` | HITL |
| `list_calendar_events` | mese / periodo |
| `schedule_event` | crea task/evento |

### B7 — Operazioni & knowledge
| Tool | Note |
|---|---|
| `export_csv` | lead/deal (return URL o attachment id) |
| `list_reports` / `send_report` | report già generati |
| `crm_kpi` | dashboard metrics dettagliate |
| `competitor_status` | ultimo scan + alert |

**Struttura consigliata (pattern Agno toolkit):**

```
backend/app/agent_tools/
  lead_tools.py      # 8–10 tool
  task_tools.py
  deal_tools.py
  billing_tools.py   # proposals + invoices
  comms_tools.py     # email, whatsapp, notify
  content_tools.py
  ops_tools.py       # report, export, kpi
  registry.py        # TOOLS + TOOL_HANDLERS aggregati
```

Ogni tool: docstring IT/EN, schema JSON, validazione argomenti, ritorna `{ok, message, data}`.

---

## 3. Task — Fase C · Comportamento da agente (spunti Agno)

> **Priorità:** media · **Stima:** 4–6 gg · **Goal:** comportamento «intelligente», non solo tool dispatch

| # | Task | Pattern Agno | Deliverable |
|---|---|---|---|
| C1 | **Planner / decomposizione** | Workflow | Domande composte («trova i lead caldi e mandami un riepilogo») → piano a step |
| C2 | **Human-in-the-loop** | HITL | Tool `requires_approval`: send_email, send_invoice, delete_*, export GDPR. UI: pannello «in attesa di conferma» |
| C3 | **Hooks pre/post tool** | Hooks | Log audit, invalidazione cache, notifiche team |
| C4 | **Guardrails business** | Guardrails | Max 50 email/giorno, no delete admin, budget deal > X → approval |
| C5 | **Memoria fatti utente** | Memory | «Preferisco le email formali», «il cliente Y è sensibile al prezzo» |
| C6 | **Follow-up automatico** | Scheduler | «Ricordami di richiamare» → task + reminder (parziale oggi) |
| C7 | **Spiegazione delle azioni** | Reasoning | Risposta con «Cosa ho fatto / Cosa manca / Prossimo passo» |
| C8 | **Evals & qualità** | Evals | Suite di 30 frasi IT di test, metrica % intent corretti, regression in CI |

---

## 4. Task — Fase D · Multi-agente & prodotto (opzionale, futuro)

> **Priorità:** bassa · **Stima:** 2–4 gg ciascuno · solo se serve

| # | Task | Note |
|---|---|---|
| D1 | **Team agent** | CRM Agent + Marketing Agent coordinati (stesso contesto lead) |
| D2 | **Workflow «inbound lead»** | form → lead → score → task → email → deal (orchestrazione) |
| D3 | **MCP server** | esporre tool CRM a Claude/ChatGPT esterni (se prodotto) |
| D4 | **RAG documenti** | knowledge su offerte/contratti (ispirato Agno Knowledge) |
| D5 | **AgentOS** | solo se multi-tenant / control plane richiesto |

---

## 5. Architettura target (senza framework)

```
Frontend chat (/crm/agent)
        │  POST /api/v1/agent/run
        ▼
┌──────────────────────────────────────────┐
│  CRM Agent Runtime (custom)              │
│  ├─ Context (session + utente + date)    │
│  ├─ Router intent                        │
│  │    ├─ Parser IT (deterministico)      │
│  │    └─ LLM tool-calling                │
│  ├─ Guardrails + Approval gate           │
│  ├─ Tool registry (per dominio)          │
│  └─ Run logger + metrics                 │
└──────────────────────────────────────────┘
        │
        ▼
  Service layer esistenti (lead, deal, invoice, …)
        │
        ▼
  MongoDB · Resend · Cloud Tasks · LLM (settings)
```

**Principi**
1. I tool **non** accedono mai direttamente a Mongo: usano i service già testati.
2. Ogni azione mutante scrive `activities` / `audit_log`.
3. Le azioni esterne (email, WhatsApp, fatture) passano da **approval** se configurato.
4. Il parser resta il path primario per comandi strutturati (veloce + testabile).
5. Il LLM gestisce linguaggio libero, composizione e riferimenti contestuali.

---

## 6. Ordine di esecuzione consigliato

| Sprint | Contenuto | Stima |
|---|---|---|
| **S1** | A1–A6 (fondamenta: session, run log, LLM, guardrail) | 3–5 gg |
| **S2** | B1–B3 (task, lead, deal) | 2–3 gg |
| **S3** | B4–B5 (fatture, proposte, content, sequence) | 2–3 gg |
| **S4** | B6–B7 (whatsapp, calendar, export, report, kpi) | 2–3 gg |
| **S5** | C2 + C4 + C8 (HITL, guardrail business, evals) | 2–3 gg |
| **S6** | C1 + C3 + C5–C7 (planner, hook, memory, UX) | 2–4 gg |

**Totale stimato: 3–4 settimane** di sviluppo a persona per un «vero agente» su tutto il CRM.  
Le fasi A+B da sole (2 settimane) coprono il 90% dei casi d'uso quotidiani.

---

## 7. Metriche di successo

| KPI | Target |
|---|---|
| Intent risolti correttamente (suite IT) | ≥ 90% |
| Azioni CRM eseguite senza errore | ≥ 95% |
| Domande multi-step («trova X e mandami Y») | gestite in 1 turno |
| Latenza media risposta | < 5 s (parser) / < 15 s (LLM) |
| Azioni destructive senza conferma | **0** |
| Copertura moduli CRM via agent | 100% delle entità principali |

---

## 8. Fuori scope (per ora)

- Sostituire l'agent con Agno SDK/AgentOS (vedi analisi dedicata)
- Voice / WhatsApp bot fully automatico
- Auto-send email senza review per lead esterni
- Modifiche GDPR erase senza doppia conferma admin

---

## 9. Riferimenti interni

- `docs/analisi-agno-agent.md` — perché non adottare Agno ora
- `backend/app/services/crm_agent_service.py` — runtime attuale
- `backend/app/routers/` — superficie API completa del CRM
- `docs/wiki/02_Architecture.md` — architettura di progetto

---

*Documento operativo di roadmap — aggiornare lo stato dei task qui o in `docs/task.md` man mano che si completano.*
