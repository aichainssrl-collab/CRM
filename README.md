# AiChain CRM

CRM B2B per AiChain Solutions — gestione lead, pipeline commerciale, email automation, analytics avanzate, marketing AI e CRM agent conversazionale.

## Stack Tecnologico

| Layer | Tecnologia |
|---|---|
| **Backend** | Python 3.12, FastAPI, Motor (MongoDB async), Pydantic v2 |
| **Frontend** | Next.js 14 (App Router), shadcn/ui, Tailwind CSS, TanStack Query |
| **Database** | MongoDB (Docker locale / Atlas produzione) |
| **Auth** | Firebase Auth (JWT verification lato backend) |
| **Email** | Resend API (EU server) |
| **LLM** | litellm multi-provider (OpenAI, Anthropic, Gemini, Ollama, custom OpenAI-compatible) |

## Stato Progetto

| | |
|---|---|
| **Fasi** | 3–20 complete · Agent platform A–G |
| **Test backend** | 394 (pytest) |
| **Router API** | 30 |
| **Sezioni frontend** | 21 (it/en) |
| **Deploy prod** | In pausa — secrets GCP incompleti (`mongodb-uri`, Resend, Apollo) |

Ultimo aggiornamento: 2026-10-23 · `34ae2eb`

### Moduli consegnati

- **Core CRM**: Leads, Deals/Pipeline, Tasks, Activities, Bookings, Calendar, Users
- **Commercial**: Products, Proposals, Invoices, Workflows, Email Sequences, Email Templates
- **Content & Marketing**: Content library, Marketing agent, Meta Ads, Apollo.io, Bulk-enrich, Competitors, Auto-monitor
- **Comms**: WhatsApp/Inbox, Notifications, Export, Reports narrativi
- **Compliance**: GDPR (export, erase, consents append-only)
- **CRM Agent (A–G)**: chat, tool (create/update lead, deals, tasks…), config goal/soul/rules, skills stile Claude, goals auto-update, knowledge search, planner multi-step, azioni approvate
- **PDF**: fpdf2 (proposte, fatture, executive brief)

## Avvio Locale

```bash
# 1. MongoDB
docker start mongodb-crm
# oppure:
docker run -d --name mongodb-crm -p 27017:27017 -e MONGO_INITDB_DATABASE=crm-aichain-db mongo:7

# 2. Backend (terminale 1)
cd backend
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8088 --reload

# 3. Frontend (terminale 2)
cd frontend
npm run dev

# 4. Seed dati (primo avvio)
cd backend
python seed_local.py
python init_db.py
```

**URLs:**
- CRM: http://localhost:3000
- API Docs: http://localhost:8088/api/docs
- Health: http://localhost:8088/api/health

**LLM locale agent:** server OpenAI-compatible su `http://localhost:1235/v1` (es. Bionic). Il model id con `/` (tipo `nvidia/nemotron-3-nano-4b`) viene prefissato automaticamente con `openai/` per litellm.

## Struttura Progetto

```
CRM-AICHAIN/
├── backend/
│   ├── app/
│   │   ├── main.py               # FastAPI app + middleware
│   │   ├── config.py             # Settings da env
│   │   ├── deps.py               # Auth dependencies
│   │   ├── middleware.py         # Security headers
│   │   ├── routers/              # 30 router API
│   │   ├── services/             # Business logic
│   │   ├── schemas/              # Pydantic models
│   │   └── tasks/                # Cloud Tasks handlers
│   ├── tests/                    # 394 test (pytest)
│   ├── init_db.py                # MongoDB indexes
│   └── seed_local.py             # Dev seed data
├── frontend/
│   ├── app/[locale]/crm/         # CRM pages (it/en)
│   ├── components/crm/           # Business components
│   ├── components/ui/            # shadcn/ui
│   ├── hooks/                    # React Query hooks
│   ├── lib/                      # API client, auth, export
│   └── messages/                 # i18n (it/en)
└── docs/wiki/                    # Documentazione progetto
```

## API Endpoints Principali

| Modulo | Endpoint | Descrizione |
|---|---|---|
| **Auth** | `/api/v1/auth/` | Firebase JWT verification |
| **Leads** | `/api/v1/leads/` | CRUD, import CSV/Excel, soft delete, search/filtri |
| **Deals** | `/api/v1/deals/` | Pipeline commerciale |
| **Tasks** | `/api/v1/tasks/` | Attività assegnate, reminder email |
| **Activities** | `/api/v1/leads/{id}/activities` | Timeline lead (append-only) |
| **GDPR** | `/api/v1/gdpr/` | Export, erase, consents |
| **Dashboard** | `/api/v1/dashboard/metrics` | KPI, scadenze, task reminder |
| **Analytics** | `/api/v1/analytics/` | Funnel, velocity, forecast, cohorts |
| **Reports** | `/api/v1/reports/` | Report narrativi, send via email |
| **Products** | `/api/v1/products/` | Catalogo prodotti |
| **Proposals** | `/api/v1/proposals/` | Proposte commerciali + PDF |
| **Invoices** | `/api/v1/invoices/` | Fatture + PDF |
| **Workflows** | `/api/v1/workflows/` | Automazioni |
| **Email Sequences** | `/api/v1/email-sequences/` | Drip campaigns |
| **Email Templates** | `/api/v1/email-templates/` | Template email |
| **Content** | `/api/v1/content/` | Content library |
| **Marketing** | `/api/v1/marketing/` | Marketing agent, content gen, insights |
| **CRM Agent** | `/api/v1/agent/` | Chat, tools, config, skills, goals, health |
| **Apollo** | `/api/v1/apollo/` | Lead enrichment Apollo.io |
| **Competitors** | `/api/v1/competitors/` | Monitoraggio competitor |
| **WhatsApp** | `/api/v1/whatsapp/` | Inbox e invii |
| **Notifications** | `/api/v1/notifications/` | In-app, activity feed, search |
| **Export** | `/api/v1/export/` | CSV export leads/deals/contacts |
| **Bookings** | `/api/v1/bookings/` | Prenotazioni demo |
| **Users** | `/api/v1/users/` | Team e ruoli |

## Testing

```bash
cd backend
source venv/bin/activate
python -m pytest tests/ -v
```

394 test che coprono: security, CORS, input validation, rate limiting, CRUD, analytics, email sequences, notifications, export, agent tools, LLM settings, PDF, workflows, competitor monitor.

## Ambiente

Variabili d'ambiente in `backend/.env`:

```env
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB_NAME=crm-aichain-db
FIREBASE_PROJECT_ID=level-facility-479122-u4
GOOGLE_APPLICATION_CREDENTIALS_JSON={"type":"service_account",...}
RESEND_API_KEY=re_...
EMAIL_FROM=noreply@aichainsolutions.net
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
ALLOWED_ORIGINS=["http://localhost:3000"]
DEBUG=true
```

## Sicurezza

- Firebase Auth JWT verification su ogni endpoint protetto
- Security headers (HSTS, CSP, X-Frame-Options, X-Content-Type-Options)
- Rate limiting su endpoint pubblici
- Error handler safe in produzione (DEBUG=false)
- Soft delete su leads/deals
- Activities e gdpr_consents append-only
- GDPR: export dati, cancellazione, audit trail
- Regex su input utente con `re.escape` (no ReDoS)

## Deploy

Cloud Run via Cloud Build (`cloudbuild.yaml`). Vedi `docs/deploy-cloud-run.md`.

> **Nota:** il deploy di produzione è attualmente **in pausa** finché lo sviluppo non è completo e non esiste un MongoDB URI di produzione. Infra GCP parziale presente (registry, SA); secrets `mongodb-uri`, `RESEND_API_KEY`, `APOLLO_API_KEY` ancora da popolare.

---

© AiChain Solutions — Catania, Italia
