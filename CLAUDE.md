# AiChain CRM — Guida per sviluppatori Claude

> 🧠 **NOTA IMPORTANTE PER GLI LLM**: Questo progetto utilizza una Wiki (Obsidian Vault) situata in `docs/wiki/` per mantenere la memoria di progetto. 
> - Consulta **sempre** i file in `docs/wiki/` prima di fare scelte architetturali.
> - Se aggiungi nuove librerie, paradigmi o prendi decisioni tecniche, **aggiorna** la Wiki e/o crea un nuovo ADR in `docs/wiki/04_ADRs/`.

## Panoramica progetto

CRM B2B per AiChain Solutions. Stack:
- **Backend**: Python 3.12, FastAPI, firebase-admin, Pydantic v2 — Cloud Run (europe-west1)
- **Frontend**: Next.js 14 (App Router), shadcn/ui, Tailwind CSS — Cloud Run (europe-west1)
- **Database**: Firestore (eur3 EU multi-region) — NoSQL document-based, nessun ORM
- **Auth**: Firebase Auth (JWT — verifica lato backend, mai lato frontend)
- **Storage**: Firebase Storage (europe-west1)
- **Job asincroni**: Cloud Tasks (europe-west1) — non Celery, nessun worker attivo
- **Email**: Resend API su server EU (api.eu.resend.com)
- **CI/CD**: Cloud Build → Artifact Registry EU → Cloud Run

Specifiche complete: `CRM_ARCHITECTURE_PHASE1_v2.md`

---

## Struttura repository

```
aichain-crm/
├── backend/                    # FastAPI
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py           # Settings da env / Secret Manager
│   │   ├── firebase_admin.py   # Init SDK firebase-admin
│   │   ├── deps.py             # Dependency injection (auth, db)
│   │   ├── models/             # Pydantic models (dati Firestore)
│   │   ├── schemas/            # Pydantic schemas request/response API
│   │   ├── routers/            # FastAPI routers
│   │   ├── services/           # Business logic
│   │   ├── tasks/              # Cloud Tasks handlers
│   │   └── utils/
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/                   # Next.js 14
│   ├── app/                    # App Router
│   ├── components/
│   │   ├── ui/                 # shadcn/ui (auto-generati, non modificare)
│   │   └── crm/                # Componenti business
│   ├── lib/
│   │   ├── firebase.ts         # Firebase client SDK init + emulator
│   │   ├── api.ts              # Axios client con Firebase token interceptor
│   │   └── auth.ts             # Firebase Auth helpers
│   ├── hooks/
│   └── Dockerfile
├── firestore.rules
├── firestore.indexes.json
├── firebase.json
├── .firebaserc
└── docker-compose.yml          # Dev locale con emulatori Firebase
```

---

## Convenzioni di codice

### Backend (Python)

- Tutto il codice async/await — Firestore usa `firestore_async.client()`
- UUID v4 come document ID di Firestore (generati lato backend, non da Firestore)
- Timestamp sempre in UTC: `datetime.now(timezone.utc)`
- Soft delete: campo `deletedAt: Timestamp | null` — mai cancellare documenti lead/deals
- Activities sono **append-only** — mai update/delete su `/leads/{id}/activities/{id}`
- `gdpr_consents` è **append-only** — audit trail immutabile
- Naming Firestore: `camelCase` per i campi dei documenti
- Paginazione: cursor-based con `last_doc_id` (non offset) — Firestore non supporta OFFSET
- Firestore non ha UNIQUE constraint — verificare unicità email lato applicazione prima di creare lead

### Frontend (TypeScript)

- App Router Next.js 14 — usare `"use client"` solo dove strettamente necessario
- shadcn/ui per tutti i componenti UI base — non reinventare componenti già presenti
- Axios (`lib/api.ts`) per tutte le chiamate al backend FastAPI
- Token Firebase iniettato automaticamente dall'interceptor in `lib/api.ts`
- TanStack Query per data fetching e cache
- Tailwind CSS per lo stile — applicare classi direttamente, non creare CSS custom

### Sicurezza

- **Nessun dato lascia l'UE** — verificare sempre regione prima di aggiungere servizi
- CORS: solo `crm.aichainsolutions.net` in produzione
- Rate limiting su endpoint pubblici (`/api/v1/forms/*`)
- Endpoint `/tasks/handlers/*` protetti da OIDC token Cloud Tasks
- Firebase Auth: verificare token lato backend su OGNI richiesta protetta

---

## Avvio sviluppo locale

```bash
# 1. Emulatori Firebase (Firestore + Auth + Storage)
firebase emulators:start --project aichain-crm-dev
# UI: http://localhost:4000

# 2. Backend (altro terminale)
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # compilare con valori dev
uvicorn app.main:app --reload
# API docs: http://localhost:8000/api/docs

# 3. Frontend (altro terminale)
cd frontend
npm install
cp .env.example .env.local  # compilare con valori dev
npm run dev
# CRM: http://localhost:3000
```

Con Docker Compose:
```bash
docker-compose up
```

Variabili d'ambiente critiche backend (`.env`):
```
FIREBASE_PROJECT_ID=aichain-crm-dev
FIREBASE_STORAGE_BUCKET=aichain-crm-dev.appspot.com
GOOGLE_APPLICATION_CREDENTIALS_JSON=<json service account>
GCP_LOCATION=europe-west1
BACKEND_INTERNAL_URL=http://localhost:8000
RESEND_API_KEY=re_...
ALLOWED_ORIGINS=["http://localhost:3000"]
```

---

## Firestore — Collezioni principali

| Collezione | Descrizione | Note |
|---|---|---|
| `users/{uid}` | Team CRM | uid = Firebase Auth UID |
| `leads/{leadId}` | Lead/contatti | Soft delete, unicità email gestita lato app |
| `leads/{id}/activities/{id}` | Log attività | **Append-only** — mai modificare |
| `leads/{id}/tasks/{id}` | Attività pianificate | CRUD completo |
| `deals/{dealId}` | Opportunità commerciali | |
| `gdpr_consents/{id}` | Log consensi GDPR | **Append-only** — audit trail |
| `form_submissions/{id}` | Invii form pubblici | Create via endpoint pubblico, poi processati |
| `bookings/{id}` | Prenotazioni demo | |
| `booking_slots/{id}` | Slot disponibili | Lettura pubblica |

---

## Pattern ricorrenti

### Aggiungere un nuovo router FastAPI

1. Creare `backend/app/routers/nuovo.py` con `router = APIRouter()`
2. Aggiungere schema in `backend/app/schemas/`
3. Aggiungere service in `backend/app/services/` se la logica è complessa
4. Registrare in `backend/app/main.py`: `app.include_router(router, prefix="/api/v1/nuovo")`

### Aggiungere un Cloud Task

1. Aggiungere handler in `backend/app/tasks/handlers.py`
2. Registrare il router task in `main.py` (prefix `/tasks/handlers`)
3. Chiamare tramite `await enqueue_task("nome-task", payload)` nel service

### Aggiungere una pagina frontend

1. Creare `frontend/app/crm/nuova-pagina/page.tsx`
2. Usare hook in `hooks/` per data fetching
3. Usare componenti shadcn/ui di base + componenti `crm/` per logica business

---

## Progetti Firebase

| Ambiente | Firebase Project ID |
|---|---|
| Sviluppo | `aichain-crm-dev` |
| Produzione | `aichain-crm-prod` |

---

## Sprint plan (Fase 1)

**Sprint 1 (sett. 1–3):** Setup Firebase/GCP, backend core (auth, leads, forms, GDPR, Cloud Tasks)
**Sprint 2 (sett. 4–6):** Frontend (login, lead table, kanban, forms, dashboard, email Resend)
**Sprint 3 (sett. 7–8):** CI/CD Cloud Build, deploy Cloud Run, monitoring, security review

Checklist dettagliata: sezione 15 di `CRM_ARCHITECTURE_PHASE1_v2.md`
