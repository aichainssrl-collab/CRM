# AiChain CRM — Guida per sviluppatori Claude

> 🧠 **NOTA IMPORTANTE PER GLI LLM**: Questo progetto utilizza una Wiki (Obsidian Vault) situata in `docs/wiki/` per mantenere la memoria di progetto.
> - Consulta **sempre** i file in `docs/wiki/` prima di fare scelte architetturali.
> - Se aggiungi nuove librerie, paradigmi o prendi decisioni tecniche, **aggiorna** la Wiki e/o crea un nuovo ADR in `docs/wiki/04_ADRs/`.

---

## ⚠️ CORREZIONE ARCHITETTURALE IMPORTANTE

Il database è **MongoDB** (NON Firestore). Firebase viene usato SOLO per l'autenticazione JWT.
- **Auth**: Firebase Auth → verifica token JWT lato backend
- **Database**: MongoDB — gestito via `motor` (driver async) — collezione `crm-aichain-db`
- **In locale**: MongoDB gira tramite Docker (vedi sezione "Avvio locale")
- **In produzione**: MongoDB Atlas oppure istanza self-hosted

Qualsiasi riferimento a "Firestore" come database è **obsoleto e incorretto**.

---

## Panoramica progetto

CRM B2B per AiChain Solutions. Stack reale:
- **Backend**: Python 3.12, FastAPI, firebase-admin (solo auth), motor (MongoDB async), Pydantic v2 — porta 8088
- **Frontend**: Next.js 14 (App Router), shadcn/ui, Tailwind CSS — porta 3000
- **Database**: MongoDB — `crm-aichain-db` — in locale via Docker su porta 27017
- **Auth**: Firebase Auth (JWT — verifica lato backend, mai lato frontend)
- **Storage**: Firebase Storage (europe-west1)
- **Email**: Resend API su server EU (api.eu.resend.com)

Specifiche complete: `CRM_ARCHITECTURE_PHASE1_v2.md`

---

## 🚀 Avvio locale — Procedura corretta

### Ordine di avvio obbligatorio

```bash
# PASSO 1: Avviare MongoDB (Docker)
docker start mongodb-crm
# oppure, se il container non esiste ancora:
docker run -d --name mongodb-crm -p 27017:27017 -e MONGO_INITDB_DATABASE=crm-aichain-db mongo:7
docker update --restart unless-stopped mongodb-crm

# Verifica che MongoDB sia attivo:
docker ps | grep mongodb-crm

# PASSO 2: Backend FastAPI (in un terminale separato)
cd /Users/fred/dev/CRM-AICHAIN/backend
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8088 --reload
# Docs: http://localhost:8088/api/docs

# PASSO 3: Frontend Next.js (in un altro terminale)
cd /Users/fred/dev/CRM-AICHAIN/frontend
npm run dev
# CRM: http://localhost:3000
```

### Seed dati iniziali (primo avvio o container ricreato)

Dopo aver avviato MongoDB, popolare gli utenti e i dati di esempio:

```bash
cd /Users/fred/dev/CRM-AICHAIN/backend
source venv/bin/activate
python seed_local.py   # se esiste
```

Se lo script non esiste, creare manualmente gli utenti nel DB. Gli utenti devono avere:
- Campo `uid` corrispondente al Firebase Auth UID
- Campo `role`: `"admin"` o `"sales"`
- Campo `isActive`: `true`
- Campo `email`: email dell'utente Firebase

**Utenti di sviluppo attuali** (MongoDB `users` collection):
| Email | Firebase UID | Ruolo |
|---|---|---|
| fred@it.it | `eHFeSPGP8cWxWHFcM5In4KVYQQ42` | admin |
| admin@aichain.it | `fFW6zJBJxCYQ77y0vXskwuFQEIH3` | admin |
| marketing@aichainsolutions.net | `JY9qlgBlfWMmtSLo4n2bjte6q8Z2` | sales |

---

## 🚨 Troubleshooting — Problemi comuni

### API restituisce 403 su tutti gli endpoint

**Causa più probabile**: MongoDB non è avviato oppure la collection `users` è vuota.

Il flusso di autenticazione è:
1. Frontend invia Firebase JWT nell'header `Authorization: Bearer <token>`
2. Backend verifica il token con firebase-admin
3. Backend cerca l'utente in MongoDB `users` collection (per `uid`)
4. Se non trovato → **403 "Utente non registrato nel CRM"**

**Fix**:
```bash
# 1. Verificare che MongoDB sia up
docker ps | grep mongodb-crm
# Se non è nella lista:
docker start mongodb-crm

# 2. Verificare che la collection users non sia vuota
docker exec -it mongodb-crm mongosh crm-aichain-db --eval "db.users.countDocuments()"
# Se ritorna 0 → eseguire il seed (vedi sopra)

# 3. Riavviare il backend dopo aver fixato MongoDB
```

### MongoDB container non esiste

```bash
docker run -d \
  --name mongodb-crm \
  -p 27017:27017 \
  -e MONGO_INITDB_DATABASE=crm-aichain-db \
  mongo:7
docker update --restart unless-stopped mongodb-crm
# Poi eseguire il seed degli utenti!
```

### I lead non si vedono nella UI

1. Verificare che l'API `/api/v1/leads` ritorni 200 (non 403)
2. Se 403 → problema MongoDB/utenti (vedi sopra)
3. Se 200 ma array vuoto → il DB è vuoto, eseguire il seed dei lead

### TypeScript / Build errors

```bash
cd frontend
npx tsc --noEmit   # verifica errori di tipo
npm run build      # build completa
```

### Classi Tailwind non funzionanti (colori non applicati)

- Questo progetto usa **shadcn/ui con Tailwind v3** e variabili CSS oklch
- I token di colore Material Design 3 (`text-on-primary`, `bg-surface-variant`, ecc.) sono stati **rimossi**
- Usare sempre token shadcn standard: `text-primary-foreground`, `bg-card`, `text-muted-foreground`, ecc.
- Le variabili CSS sono definite in `frontend/app/globals.css`
- I colori Tailwind sono mappati in `frontend/tailwind.config.ts` come `"var(--CSS-VAR)"`

---

## Struttura repository

```
aichain-crm/
├── backend/                    # FastAPI
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py           # Settings da env
│   │   ├── firebase_admin.py   # Init SDK firebase-admin (solo auth JWT)
│   │   ├── deps.py             # Dependency injection (auth, db MongoDB)
│   │   ├── models/             # Pydantic models (dati MongoDB)
│   │   ├── schemas/            # Pydantic schemas request/response API
│   │   ├── routers/            # FastAPI routers
│   │   ├── services/           # Business logic
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
│   │   ├── firebase.ts         # Firebase client SDK init (solo auth)
│   │   ├── api.ts              # Axios client con Firebase token interceptor
│   │   └── auth.ts             # Firebase Auth helpers
│   ├── hooks/
│   └── Dockerfile
└── docs/
    ├── setup.md                # Setup locale completo
    └── wiki/                   # Wiki di progetto (Obsidian Vault)
        ├── 03_Tech_Stack.md
        └── 04_ADRs/
            ├── 001_Firebase_Auth_MongoDB.md
            └── 002_MongoDB_Docker_LocalDev.md
```

---

## Convenzioni di codice

### Backend (Python)

- Tutto il codice async/await — MongoDB via `motor` client async
- UUID v4 come `_id` dei documenti MongoDB (generati lato backend)
- Timestamp sempre in UTC: `datetime.now(timezone.utc)`
- Soft delete: campo `deletedAt: datetime | None` — mai cancellare documenti lead/deals
- Activities sono **append-only** — mai update/delete
- `gdpr_consents` è **append-only** — audit trail immutabile
- Naming MongoDB: `camelCase` per i campi dei documenti
- Unicità email: verificare lato applicazione prima di creare lead (MongoDB non ha UNIQUE constraint nativo in questo setup)

### Frontend (TypeScript)

- App Router Next.js 14 — usare `"use client"` solo dove strettamente necessario
- **shadcn/ui per tutti i componenti UI base** — non usare bottoni/input HTML grezzi
- Axios (`lib/api.ts`) per tutte le chiamate al backend FastAPI
- Token Firebase iniettato automaticamente dall'interceptor in `lib/api.ts`
- TanStack Query per data fetching e cache
- Tailwind CSS per lo stile — token shadcn standard, no MD3 tokens
- Design system: Charter-inspired — navy primario `oklch(0.338 0.189 264)`, sfondo perla `oklch(0.978 0.007 264)`, card bianche

### Sicurezza

- **Nessun dato lascia l'UE** — verificare sempre regione prima di aggiungere servizi
- CORS: solo `crm.aichainsolutions.net` in produzione
- Rate limiting su endpoint pubblici (`/api/v1/forms/*`)
- Firebase Auth: verificare token lato backend su OGNI richiesta protetta

---

## MongoDB — Collezioni principali

| Collezione | Descrizione | Note |
|---|---|---|
| `users` | Team CRM | `uid` = Firebase Auth UID, campi: `role`, `isActive`, `email` |
| `leads` | Lead/contatti | Soft delete, unicità email gestita lato app |
| `deals` | Opportunità commerciali | |
| `tasks` | Attività pianificate | |
| `form_submissions` | Invii form pubblici | |
| `bookings` | Prenotazioni demo | |
| `gdpr_consents` | Log consensi GDPR | **Append-only** — audit trail |

Connessione locale: `mongodb://localhost:27017` — DB: `crm-aichain-db`

---

## Pattern ricorrenti

### Aggiungere un nuovo router FastAPI

1. Creare `backend/app/routers/nuovo.py` con `router = APIRouter()`
2. Aggiungere schema in `backend/app/schemas/`
3. Aggiungere service in `backend/app/services/` se la logica è complessa
4. Registrare in `backend/app/main.py`: `app.include_router(router, prefix="/api/v1/nuovo")`

### Aggiungere una pagina frontend

1. Creare `frontend/app/crm/nuova-pagina/page.tsx`
2. Usare hook in `hooks/` per data fetching
3. Usare componenti shadcn/ui di base + componenti `crm/` per logica business
4. NON usare token colore Material Design 3 — usare token shadcn standard

---

## Ambienti Firebase

| Ambiente | Firebase Project ID |
|---|---|
| Sviluppo | `aichain-crm-dev` |
| Produzione | `aichain-crm-prod` |

> Firebase è usato **solo per Auth** (JWT). I dati applicativi sono in MongoDB.

---

## Sprint plan (Fase 1)

**Sprint 1 (sett. 1–3):** Setup Firebase/GCP, backend core (auth, leads, forms, GDPR)
**Sprint 2 (sett. 4–6):** Frontend (login, lead table, kanban, forms, dashboard, email Resend)
**Sprint 3 (sett. 7–8):** CI/CD, deploy, monitoring, security review
