# CRM Agent AiChain — Documentazione operativa

**Versione:** fasi A–G · **Data:** 2026-10-16  
**Stato:** produzione-ready (modulo agent) · **Test:** 371 backend + 29 frontend · **Evals parser:** 32/32 (100%)

---

## 1. Panoramica

L'agent CRM permette di gestire **tutto il CRM in linguaggio naturale** (italiano), con:

| Capacità | Descrizione |
|---|---|
| **Parser deterministico** | Comandi strutturati IT, veloci e testabili (senza LLM) |
| **Tool-calling LLM** | Linguaggio libero via litellm + modello configurato in Impostazioni LLM |
| **45+ tool** | Lead, task, deal, fatture, proposte, email, WhatsApp, report, export, knowledge |
| **Sessioni multi-turno** | Contesto «la sua email», «quel lead» |
| **HITL** | Approvazione umana per invii esterni e eliminazioni |
| **Guardrail** | Quota email/WhatsApp, soglia deal, validazione input |
| **Memoria utente** | «ricorda che…», «preferisco…» |
| **Workflow** | Inbound lead (score → task → deal hint), planner multi-step |
| **Team** | Delega a Marketing Agent (contenuti, insight) |
| **MCP-lite** | Manifest + invoke per client esterni |
| **Osservabilità** | Run log, health, metrics |

**Stack:** FastAPI + MongoDB · LLM OpenAI-compatible (settings DB) · Resend (EU) · Firebase JWT

---

## 2. Architettura

```
Frontend /crm/agent  ──POST /api/v1/agent/run──►  CRM Agent Runtime
                                                  │
                    ┌─────────────────────────────┼──────────────────────────┐
                    │  Guardrail + HITL           │  Session + Run log       │
                    │  Planner (compound)         │  Memory facts            │
                    │  Parser IT  │  LLM tools    │  Knowledge / Workflows   │
                    └─────────────────────────────┼──────────────────────────┘
                                                  ▼
                    Service CRM (lead, deal, invoice, email, …) → MongoDB
```

### File principali

| File | Ruolo |
|---|---|
| `backend/app/services/crm_agent_service.py` | Runtime: parser, LLM, registry tool |
| `backend/app/services/agent_tools_phase_b.py` | Tool moduli CRM (B) + workflow/team (D) + knowledge (F) |
| `backend/app/services/agent_session_service.py` | Sessioni + run log (A) |
| `backend/app/services/agent_governance.py` | HITL, quote, guardrail (C) |
| `backend/app/services/agent_memory.py` | Fatti utente (C) |
| `backend/app/services/agent_knowledge.py` | RAG-lite keyword (F) |
| `backend/app/services/agent_planner.py` | Decomposizione + reply strutturata (F) |
| `backend/app/services/agent_workflows.py` | Inbound lead + team marketing + MCP (D) |
| `backend/app/services/agent_metrics.py` | Health + metrics (G) |
| `backend/app/services/agent_evals.py` | Suite 32 intent IT (C) |
| `frontend/hooks/useAgent.ts` | Hook API agent |
| `frontend/app/[locale]/crm/agent/page.tsx` | Chat + pannello ops |

---

## 3. API

| Metodo | Endpoint | Descrizione |
|---|---|---|
| POST | `/api/v1/agent/run` | Esegui turno chat (`message`, `sessionId`) |
| GET | `/api/v1/agent/tools` | Elenco tool |
| POST | `/api/v1/agent/tools/{name}` | Esecuzione diretta tool |
| GET | `/api/v1/agent/runs` | Storico run |
| GET | `/api/v1/agent/approvals` | Approvazioni pending |
| POST | `/api/v1/agent/approvals/{id}/decision` | Approva (esegue) / rifiuta |
| GET | `/api/v1/agent/memory` | Fatti memorizzati |
| GET | `/api/v1/agent/health` | Stato LLM + pending + run 24h |
| GET | `/api/v1/agent/metrics?days=7` | Success rate, latenza, top tool |
| GET | `/api/v1/agent/mcp/manifest` | Manifest MCP-lite |
| POST | `/api/v1/agent/mcp/invoke` | Invoke stile MCP |

Auth: **Firebase JWT** + ruolo `admin` o `sales`.

---

## 4. Tool (50)

### Lead
`create_lead` · `update_lead` · `find_lead` · `list_leads` · `search_leads` · `delete_lead`* · `enrich` (via agent legacy)

### Task & attività
`create_task` · `list_tasks` · `complete_task` · `delete_task`* · `add_activity` · `reschedule_task` · `set_reminder` · `list_deadlines` · `schedule_followup`

### Deal
`create_deal` · `update_deal` · `list_deals` · `move_deal_stage` · `delete_deal`* · `deal_pipeline`

### Commerciale
`list_proposals` · `create_proposal` · `mark_proposal` · `list_invoices` · `create_invoice` · `mark_invoice`* · `invoice_stats`

### Comunicazioni
`draft_email` · `send_email`* · `send_whatsapp`* · `list_whatsapp_conversations` · `notify` · `list_notifications` · `book_demo`

### Content & marketing
`list_products` · `search_content` · `list_email_templates` · `enroll_sequence` · `marketing_content` · `marketing_insights`

### Ops & knowledge
`crm_summary` · `crm_kpi` · `generate_report` · `list_reports` · `export_csv` · `list_calendar_events` · `competitor_status` · `search_knowledge` · `workflow_inbound_lead` · `help` · `remember_fact`

\* = richiede `confirm=true` o approvazione HITL

---

## 5. Comandi chat (esempi)

```
crea lead Mario Rossi email mario@studio.it
dammi il settore di mario@studio.it
imposta settore marketing sul lead mario@studio.it
Danilo Zanni in quale azienda lavora?
mostra fatture · mostra proposte · pipeline dei deal
mostra i task · i miei task · scadenze dei prossimi 7 giorni
riepilogo CRM · kpi · export csv
workflow inbound per mario@studio.it
crea lead X email x@y.it e poi crea task Chiamalo email x@y.it
genera contenuto marketing per ZenTratto
ricorda che il cliente Marco preferisce le email formali
aiuto
```

**Multi-turno:** «dammi la sua email» dopo aver nominato un lead usa la sessione.

---

## 6. Governance (HITL & guardrail)

| Regola | Comportamento |
|---|---|
| `send_email`, `send_whatsapp`, `delete_*`, `mark_invoice` | Coda approvazione (o `confirm=true`) |
| Max **50 email / 30 WhatsApp** al giorno per utente | Blocco con messaggio quota |
| Deal ≥ **50.000 €** | Richiede approvazione |
| Input > 4000 char / pattern injection | Rifiuto (`mode: invalid`) |

Approvazione: pannello UI oppure  
`POST /api/v1/agent/approvals/{id}/decision` `{"approve": true}` → **esegue** il tool.

---

## 7. Sessioni, memoria, run

- **`agent_sessions`** — history turni, `lastEntity` (riferimenti «lui / quel lead»)
- **`agent_memory`** — fatti `note` / `preference` (max 50/utente)
- **`agent_runs`** — messaggio, mode, tools, latenza, errori
- **`agent_actions`** — audit azioni mutanti (rate limit)
- **`agent_approvals`** — coda HITL

---

## 8. Qualità & test

| Suite | Risultato |
|---|---|
| Backend `pytest tests/` | **371 passed** |
| Evals parser (`python -m app.services.agent_evals`) | **32/32 (100%)** |
| Frontend Vitest | **29 passed** |
| TypeScript `tsc --noEmit` | pulito |

**Metriche live (smoke 2026-10-16):** 26 run · success rate 92.3% · MCP 50 tool · LLM ping ok.

Come lanciare:
```bash
cd backend && source venv/bin/activate && pytest tests/ -q
python -m app.services.agent_evals
cd ../frontend && npm test && npx tsc --noEmit
```

---

## 9. Operatività

### Impostazioni LLM
Mongo `app_settings` / `_id: "llm"` o UI **Impostazioni → LLM**  
(`provider`, `model`, `baseUrl`, `apiKey`).  
Supportati: OpenAI, custom OpenAI-compatible (es. Bionic/LM Studio), Ollama, Anthropic, Gemini.

### Health check
```bash
curl -H "Authorization: Bearer $TOKEN" http://localhost:8088/api/v1/agent/health
```
Camposi: `llmAvailable`, `llmPing.ok`, `pendingApprovals`, `runsLast24h`.

### Note
- LLM locale (es. Nemotron 4B) può risultare `No models loaded` se idle: il fallback parser copre le azioni CRM strutturate.
- Telemetry terzi: nessuna (solo log locali / EU).
- Soft delete su lead/task/deal; activity log append-only.

---

## 10. Roadmap eseguita (A–G)

| Fase | Contenuto | Stato |
|---|---|---|
| **A** | Sessioni, context, run log, LLM resiliente, guardrail input | ✅ |
| **B** | Tool su tutti i moduli CRM | ✅ |
| **C** | HITL, quote, memory, evals | ✅ |
| **D** | Workflow inbound, team marketing, MCP-lite | ✅ |
| **E** | UI approvazioni / memoria / run | ✅ |
| **F** | Knowledge, planner, follow-up, reply strutturata | ✅ |
| **G** | Esecuzione approvazioni, health, metrics | ✅ |

**Fuori scope / futuro:** RAG con embeddings, AgentOS, voice, auto-send senza review.

---

## 11. Riferimenti

- `docs/analisi-agno-agent.md` — perché non adottare Agno
- `docs/agent-crm-roadmap-tasks.md` — task dettagliati A–G
- `docs/wiki/02_Architecture.md` — architettura CRM
- Repo: https://github.com/aichainssrl-collab/CRM

---

*Documentazione agent CRM AiChain Solutions — aggiornata al completamento fasi A–G (2026-10-16).*
