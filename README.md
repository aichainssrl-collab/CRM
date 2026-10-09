# AiChain CRM

CRM B2B per AiChain Solutions — gestione lead, pipeline commerciale, email automation, analytics avanzate e marketing AI.

## Stack Tecnologico

| Layer | Tecnologia |
|---|---|
| **Backend** | Python 3.12, FastAPI, Motor (MongoDB async), Pydantic v2 |
| **Frontend** | Next.js 14 (App Router), shadcn/ui, Tailwind CSS, TanStack Query |
| **Database** | MongoDB (Docker locale / Atlas produzione) |
| **Auth** | Firebase Auth (JWT verification lato backend) |
| **Email** | Resend API (EU server) |
| **LLM** | litellm multi-provider (OpenAI, Anthropic, Gemini, Ollama) |

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

## Struttura Progetto

```
CRM-AICHAIN/
├── backend/
│   ├── app/
│   │   ├── main.py               # FastAPI app + middleware
│   │   ├── config.py             # Settings da env
│   │   ├── deps.py               # Auth dependencies
│   │   ├── middleware.py          # Security headers
│   │   ├── routers/              # 15 router API
│   │   ├── services/             # Business logic
│   │   ├── schemas/              # Pydantic models
│   │   └── tasks/                # Cloud Tasks handlers
│   ├── tests/                    # 146 test (pytest)
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
| **Leads** | `/api/v1/leads/` | CRUD, import CSV/Excel, soft delete |
| **Deals** | `/api/v1/deals/` | Pipeline commerciale |
| **Tasks** | `/api/v1/tasks/` | Attività assegnate |
| **Activities** | `/api/v1/leads/{id}/activities` | Timeline lead (append-only) |
| **GDPR** | `/api/v1/gdpr/` | Export, erase, consents |
| **Dashboard** | `/api/v1/dashboard/metrics` | KPI |
| **Analytics** | `/api/v1/analytics/` | Funnel, velocity, forecast, cohorts |
| **Reports** | `/api/v1/reports/` | Generate, send via email |
| **Email Sequences** | `/api/v1/email-sequences/` | Drip campaigns |
| **Notifications** | `/api/v1/notifications/` | In-app notifications, activity feed, search |
| **Export** | `/api/v1/export/` | CSV export leads/deals/contacts |
| **Marketing** | `/api/v1/marketing/` | AI Agent chat, content gen, insights |

## Testing

```bash
cd backend
source venv/bin/activate
python -m pytest tests/ -v
```

146 test che coprono: security, CORS, input validation, rate limiting, CRUD operations, analytics, email sequences, notifications, export.

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

## Deploy

Cloud Run via Cloud Build (`cloudbuild.yaml`). Vedi `docs/deploy-cloud-run.md`.

---

© AiChain Solutions — Catania, Italia