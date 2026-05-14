# AiChain CRM — Specifiche Tecniche Fase 1
> **Stack: Python (FastAPI) · Firebase (Auth + Firestore + Storage) · Next.js 14 · shadcn/ui**
> **Deploy: Google Cloud Platform · Regione EU (europe-west1 / eur3)**
> Versione: 2.0 · Autore: AiChain Solutions CTO

---

## Indice

1. [Panoramica architetturale](#1-panoramica-architetturale)
2. [Servizi GCP & Firebase](#2-servizi-gcp--firebase)
3. [Struttura repository](#3-struttura-repository)
4. [Firebase — Configurazione progetto](#4-firebase--configurazione-progetto)
5. [Firestore — Data model](#5-firestore--data-model)
6. [Backend — FastAPI su Cloud Run](#6-backend--fastapi-su-cloud-run)
7. [Frontend — Next.js su Cloud Run](#7-frontend--nextjs-su-cloud-run)
8. [Autenticazione — Firebase Auth](#8-autenticazione--firebase-auth)
9. [Task asincroni — Cloud Tasks](#9-task-asincroni--cloud-tasks)
10. [Storage — Firebase Storage](#10-storage--firebase-storage)
11. [GDPR & compliance EU](#11-gdpr--compliance-eu)
12. [CI/CD — Cloud Build](#12-cicd--cloud-build)
13. [Variabili d'ambiente & Secret Manager](#13-variabili-dambiente--secret-manager)
14. [Costi stimati](#14-costi-stimati)
15. [Checklist sviluppatore](#15-checklist-sviluppatore)

---

## 1. Panoramica architetturale

```
┌─────────────────────────────────────────────────────────────────────┐
│                        GOOGLE CLOUD PLATFORM                        │
│                     Regione: europe-west1 (Belgio)                  │
│                                                                     │
│  ┌─────────────────────────┐   ┌─────────────────────────────────┐  │
│  │   Cloud Run — Frontend  │   │   Cloud Run — Backend           │  │
│  │   Next.js 14 App Router │   │   FastAPI + firebase-admin      │  │
│  │   shadcn/ui · Tailwind  │   │   Python 3.12 · Pydantic v2     │  │
│  │   porta 3000            │◄──►   porta 8000                    │  │
│  └────────────┬────────────┘   └──────────────┬──────────────────┘  │
│               │                               │                     │
│  ┌────────────▼───────────────────────────────▼──────────────────┐  │
│  │                     FIREBASE (eur3 — EU multi-region)          │  │
│  │                                                               │  │
│  │  ┌──────────────┐  ┌────────────────┐  ┌──────────────────┐  │  │
│  │  │ Firebase Auth│  │   Firestore    │  │ Firebase Storage │  │  │
│  │  │ UID + JWT    │  │ NoSQL Database │  │ File & allegati  │  │  │
│  │  └──────────────┘  └────────────────┘  └──────────────────┘  │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  │
│  │  Cloud Tasks     │  │  Secret Manager  │  │ Artifact Registry│  │
│  │  Job asincroni   │  │  Env & secrets   │  │ Docker images    │  │
│  │  (sostituisce    │  │  GDPR-safe       │  │ EU repository    │  │
│  │   Celery)        │  │                  │  │                  │  │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘  │
│                                                                     │
│  ┌──────────────────┐  ┌──────────────────┐                        │
│  │  Cloud Build     │  │  Cloud Logging   │                        │
│  │  CI/CD pipeline  │  │  + Monitoring    │                        │
│  └──────────────────┘  └──────────────────┘                        │
└─────────────────────────────────────────────────────────────────────┘
```

### Flusso dati principale

```
Browser → Cloud Run (Next.js) → Cloud Run (FastAPI)
                                       │
                                       ├── Firebase Auth (verifica token)
                                       ├── Firestore (leggi/scrivi dati)
                                       ├── Firebase Storage (upload file)
                                       └── Cloud Tasks (job asincroni)
                                                    │
                                              Resend API (email)
                                              [server EU Frankfurt]
```

### Perché questa architettura

| Scelta | Motivazione |
|---|---|
| **Firestore** invece di PostgreSQL | Serverless, scala a 0, nessun server da gestire, SDK nativo per Python e Next.js |
| **Firebase Auth** invece di JWT custom | Gestione token, refresh, revoca già pronta — zero codice auth da scrivere |
| **Cloud Run** invece di VM/GKE | Pay-per-request, scala automaticamente, cold start < 2s, GDPR-friendly |
| **Cloud Tasks** invece di Celery | Nessun worker sempre attivo — job asincroni gestiti da GCP, costo zero a riposo |
| **eur3** per Firebase | Multi-region EU: europe-west1 (Belgio) + europe-west4 (Olanda) — massima disponibilità |
| **europe-west1** per Cloud Run | Belgio — stessa area geografica di eur3, latenza minima tra i servizi |

---

## 2. Servizi GCP & Firebase

### Firebase — progetto unico con due ambienti

```
firebase-project-id: aichain-crm-prod
├── Firestore:       eur3   (EU multi-region)
├── Firebase Auth:   eur3
├── Firebase Storage: europe-west1
└── Hosting:         non usato (usiamo Cloud Run)

firebase-project-id: aichain-crm-dev
└── (stesso schema, dati di test)
```

### GCP — risorse da creare

```bash
# Regione default per tutte le risorse
gcloud config set compute/region europe-west1

# Servizi da abilitare
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  cloudtasks.googleapis.com \
  secretmanager.googleapis.com \
  artifactregistry.googleapis.com \
  firebase.googleapis.com \
  firestore.googleapis.com \
  logging.googleapis.com \
  monitoring.googleapis.com
```

### Tabella risorse e costi indicativi (Fase 1, traffico iniziale)

| Servizio | Configurazione | Costo/mese stimato |
|---|---|---|
| Cloud Run — Backend | Min 0 istanze, max 10, 512MB RAM, 1 vCPU | €0–15 |
| Cloud Run — Frontend | Min 0 istanze, max 5, 256MB RAM | €0–8 |
| Firestore | ~50K operazioni/giorno, 1GB storage | €0–5 |
| Firebase Auth | Fino a 10K utenti attivi/mese | €0 (free tier) |
| Firebase Storage | 5GB storage, 1GB/mese trasferimento | €0–2 |
| Cloud Tasks | ~10K task/mese | €0 (free tier) |
| Secret Manager | ~10 secret, ~1K accessi/mese | €0–1 |
| Artifact Registry | 2 immagini Docker, ~2GB | €0–1 |
| **Totale stimato** | | **€0–32/mese** |

---

## 3. Struttura repository

```
aichain-crm/
├── backend/                              # Python FastAPI
│   ├── app/
│   │   ├── main.py                       # Entry point, middleware, router
│   │   ├── config.py                     # Settings da Secret Manager / env
│   │   ├── firebase_admin.py             # Init firebase-admin SDK
│   │   ├── deps.py                       # Dependency injection (db, current_user)
│   │   │
│   │   ├── models/                       # Pydantic models (no ORM — Firestore è NoSQL)
│   │   │   ├── lead.py
│   │   │   ├── activity.py
│   │   │   ├── task.py
│   │   │   ├── deal.py
│   │   │   ├── booking.py
│   │   │   └── gdpr_consent.py
│   │   │
│   │   ├── schemas/                      # Pydantic schemas request/response
│   │   │   ├── lead.py
│   │   │   ├── activity.py
│   │   │   ├── task.py
│   │   │   ├── analytics.py
│   │   │   └── forms.py
│   │   │
│   │   ├── routers/
│   │   │   ├── auth.py                   # Verifica token Firebase
│   │   │   ├── leads.py
│   │   │   ├── pipeline.py
│   │   │   ├── activities.py
│   │   │   ├── tasks.py
│   │   │   ├── forms.py                  # Endpoint pubblici (no auth)
│   │   │   ├── analytics.py
│   │   │   ├── bookings.py
│   │   │   └── webhooks.py
│   │   │
│   │   ├── services/
│   │   │   ├── firestore_service.py      # Helper CRUD su Firestore
│   │   │   ├── lead_service.py
│   │   │   ├── scoring_service.py
│   │   │   ├── email_service.py          # Resend integration
│   │   │   └── gdpr_service.py
│   │   │
│   │   ├── tasks/                        # Cloud Tasks handlers
│   │   │   ├── handlers.py               # Endpoint che Cloud Tasks chiama
│   │   │   ├── email_tasks.py
│   │   │   └── scoring_tasks.py
│   │   │
│   │   └── utils/
│   │       ├── cloud_tasks.py            # Helper per creare task su Cloud Tasks
│   │       ├── utm_parser.py
│   │       └── pagination.py
│   │
│   ├── tests/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── .env.example
│   └── cloudbuild.yaml                   # CI/CD pipeline
│
├── frontend/                             # Next.js 14
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── (auth)/login/page.tsx
│   │   └── crm/
│   │       ├── layout.tsx
│   │       ├── page.tsx                  # Dashboard
│   │       ├── leads/
│   │       │   ├── page.tsx
│   │       │   └── [id]/page.tsx
│   │       ├── pipeline/page.tsx
│   │       ├── tasks/page.tsx
│   │       └── reports/page.tsx
│   │
│   ├── components/
│   │   ├── ui/                           # shadcn/ui (auto-generati)
│   │   └── crm/
│   │       ├── layout/
│   │       ├── leads/
│   │       ├── pipeline/
│   │       ├── tasks/
│   │       └── dashboard/
│   │
│   ├── lib/
│   │   ├── firebase.ts                   # Firebase client SDK init
│   │   ├── api.ts                        # Axios verso backend FastAPI
│   │   ├── auth.ts                       # Firebase Auth helpers
│   │   └── utils.ts
│   │
│   ├── hooks/
│   │   ├── useAuth.ts                    # Firebase Auth state
│   │   ├── useLeads.ts
│   │   ├── usePipeline.ts
│   │   └── useTasks.ts
│   │
│   ├── Dockerfile
│   ├── .env.example
│   └── cloudbuild.yaml
│
├── firestore.rules                       # Security rules Firestore
├── firestore.indexes.json                # Indici compositi Firestore
├── firebase.json                         # Config Firebase CLI
├── .firebaserc                           # Alias progetti (dev/prod)
├── docker-compose.yml                    # Dev locale con emulatori Firebase
└── README.md
```

---

## 4. Firebase — Configurazione progetto

### `firebase.json`

```json
{
  "firestore": {
    "rules": "firestore.rules",
    "indexes": "firestore.indexes.json"
  },
  "storage": {
    "rules": "storage.rules"
  },
  "emulators": {
    "auth": { "port": 9099 },
    "firestore": { "port": 8080 },
    "storage": { "port": 9199 },
    "ui": { "enabled": true, "port": 4000 }
  }
}
```

### `.firebaserc`

```json
{
  "projects": {
    "default": "aichain-crm-dev",
    "production": "aichain-crm-prod"
  }
}
```

### `firestore.rules`

```js
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {

    // ── Helper functions ───────────────────────────────────────
    function isAuthenticated() {
      return request.auth != null;
    }

    function isAdmin() {
      return isAuthenticated() &&
        get(/databases/$(database)/documents/users/$(request.auth.uid)).data.role == 'admin';
    }

    function isSales() {
      return isAuthenticated() &&
        get(/databases/$(database)/documents/users/$(request.auth.uid)).data.role in ['admin', 'sales'];
    }

    function isOwner(assignedTo) {
      return isAuthenticated() && request.auth.uid == assignedTo;
    }

    // ── Users (team CRM) ───────────────────────────────────────
    match /users/{userId} {
      allow read: if isAuthenticated();
      allow write: if isAdmin();
    }

    // ── Leads ──────────────────────────────────────────────────
    match /leads/{leadId} {
      allow read: if isSales();
      allow create: if isSales();
      allow update: if isSales();
      allow delete: if isAdmin();   // Solo admin può soft-delete

      // Subcollection activities — append-only
      match /activities/{activityId} {
        allow read: if isSales();
        allow create: if isSales();
        allow update, delete: if false;   // MAI modificare activity
      }

      // Subcollection tasks
      match /tasks/{taskId} {
        allow read: if isSales();
        allow create: if isSales();
        allow update: if isSales();
        allow delete: if isAdmin();
      }
    }

    // ── Deals ──────────────────────────────────────────────────
    match /deals/{dealId} {
      allow read, write: if isSales();
    }

    // ── GDPR consents — SOLO lettura dopo scrittura ────────────
    match /gdpr_consents/{consentId} {
      allow read: if isAdmin();
      allow create: if true;           // Scritto anche da form pubblici
      allow update, delete: if false;  // MAI modificare — audit trail
    }

    // ── Form submissions — scritto dal backend pubblico ────────
    match /form_submissions/{submissionId} {
      allow read: if isSales();
      allow create: if true;           // Endpoint pubblico
      allow update: if isSales();
      allow delete: if false;
    }

    // ── Bookings ───────────────────────────────────────────────
    match /bookings/{bookingId} {
      allow read: if isSales();
      allow write: if isSales();
    }

    match /booking_slots/{slotId} {
      allow read: if true;             // Pubblico per visualizzare disponibilità
      allow write: if isSales();
    }
  }
}
```

### `firestore.indexes.json`

```json
{
  "indexes": [
    {
      "collectionGroup": "leads",
      "queryScope": "COLLECTION",
      "fields": [
        { "fieldPath": "status",     "order": "ASCENDING" },
        { "fieldPath": "createdAt",  "order": "DESCENDING" }
      ]
    },
    {
      "collectionGroup": "leads",
      "queryScope": "COLLECTION",
      "fields": [
        { "fieldPath": "source",     "order": "ASCENDING" },
        { "fieldPath": "leadScore",  "order": "DESCENDING" }
      ]
    },
    {
      "collectionGroup": "leads",
      "queryScope": "COLLECTION",
      "fields": [
        { "fieldPath": "assignedTo", "order": "ASCENDING" },
        { "fieldPath": "status",     "order": "ASCENDING" },
        { "fieldPath": "createdAt",  "order": "DESCENDING" }
      ]
    },
    {
      "collectionGroup": "leads",
      "queryScope": "COLLECTION",
      "fields": [
        { "fieldPath": "industry",   "order": "ASCENDING" },
        { "fieldPath": "leadScore",  "order": "DESCENDING" }
      ]
    },
    {
      "collectionGroup": "activities",
      "queryScope": "COLLECTION_GROUP",
      "fields": [
        { "fieldPath": "leadId",    "order": "ASCENDING" },
        { "fieldPath": "createdAt", "order": "DESCENDING" }
      ]
    },
    {
      "collectionGroup": "tasks",
      "queryScope": "COLLECTION_GROUP",
      "fields": [
        { "fieldPath": "assignedTo", "order": "ASCENDING" },
        { "fieldPath": "dueDate",    "order": "ASCENDING" }
      ]
    }
  ],
  "fieldOverrides": []
}
```

---

## 5. Firestore — Data model

Firestore è **NoSQL document-based** — nessun JOIN, nessun schema fisso.
La struttura è ottimizzata per le query più frequenti del CRM.

### Convenzioni

- Tutti i document ID sono UUID v4 (generati lato backend, non da Firestore)
- Timestamp sempre in UTC come `Timestamp` nativo Firestore
- Soft delete: campo `deletedAt: Timestamp | null`
- Subcollection per dati 1-to-many con accesso frequente (activities, tasks)
- Dati 1-to-few embedded nel documento padre (tags, pain_points come array)

### Struttura collezioni

```
firestore-root/
│
├── users/{uid}                       # uid = Firebase Auth UID
├── leads/{leadId}
│   ├── activities/{activityId}       # Subcollection — append-only
│   └── tasks/{taskId}                # Subcollection
├── deals/{dealId}
├── bookings/{bookingId}
├── booking_slots/{slotId}
├── form_submissions/{submissionId}
└── gdpr_consents/{consentId}         # Append-only — mai modificare
```

### Schema documenti

#### `users/{uid}`

```typescript
{
  uid:        string,           // = Firebase Auth UID
  email:      string,
  fullName:   string,
  role:       "admin" | "sales" | "readonly",
  avatarUrl:  string | null,
  isActive:   boolean,
  createdAt:  Timestamp,
  updatedAt:  Timestamp,
}
```

#### `leads/{leadId}`

```typescript
{
  // Anagrafica
  firstName:    string | null,
  lastName:     string | null,
  email:        string,           // REQUIRED — indice unique gestito lato app
  phone:        string | null,
  linkedinUrl:  string | null,

  // Azienda
  companyName:  string | null,
  companySize:  "1-10" | "11-50" | "51-200" | "201-500" | "500+" | null,
  industry:     "legal" | "finance" | "manufacturing" | "insurance" | "other" | null,
  roleTitle:    string | null,
  roleSeniority: "c_level" | "director" | "manager" | "staff" | null,

  // Fonte & tracking
  source:       "linkedin" | "google_organic" | "google_ads" | "instagram" |
                "assessment" | "playbook" | "referral" | "direct" | null,
  utm: {                          // Oggetto embedded
    source:   string | null,
    medium:   string | null,
    campaign: string | null,
    content:  string | null,
    term:     string | null,
  },
  landingPage:  string | null,
  referrerUrl:  string | null,

  // Stato pipeline
  status:         "new" | "contacted" | "qualified" | "demo_scheduled" |
                  "proposal_sent" | "won" | "lost" | "cold",
  pipelineStage:  string,           // Specchio di status — usato per Kanban
  lostReason:     string | null,

  // Qualifica
  leadScore:    number,             // 0–100
  isQualified:  boolean,
  budgetRange:  "under_500" | "500_2000" | "2000_5000" | "over_5000" | null,
  timeline:     "immediate" | "1_3_months" | "3_6_months" | "exploring" | null,
  painPoints:   string[],           // Array embedded — max 10 elementi

  // Note e metadata
  notes:        string | null,
  tags:         string[],
  customFields: Record<string, unknown>,

  // Assegnazione
  assignedTo:   string | null,      // uid utente CRM

  // Counters (aggiornati con increment atomico)
  activityCount: number,
  taskCount:     number,

  // Timestamps
  firstContactAt:  Timestamp | null,
  lastActivityAt:  Timestamp | null,
  createdAt:       Timestamp,
  updatedAt:       Timestamp,
  deletedAt:       Timestamp | null,
}
```

#### `leads/{leadId}/activities/{activityId}`

```typescript
{
  // APPEND-ONLY — mai aggiornare
  leadId:   string,             // Riferimento al lead padre (per query cross-lead)
  userId:   string | null,      // null = azione automatica del sistema
  type:     "note" | "call" | "email_sent" | "email_received" |
            "email_opened" | "email_clicked" | "form_submitted" |
            "page_visited" | "stage_changed" | "score_updated" |
            "task_completed" | "booking_created" | "booking_attended",
  title:    string | null,
  body:     string | null,
  metadata: {
    // Varia per tipo:
    // email_sent:     { subject, resendId, templateId }
    // page_visited:   { url, durationSeconds }
    // stage_changed:  { from, to }
    // score_updated:  { oldScore, newScore, reason }
    // email_opened:   { emailId, openedAt }
  },
  createdAt: Timestamp,
}
```

#### `leads/{leadId}/tasks/{taskId}`

```typescript
{
  leadId:      string,
  dealId:      string | null,
  assignedTo:  string,          // uid
  createdBy:   string,          // uid
  title:       string,
  description: string | null,
  type:        "call" | "email" | "followup" | "demo" | "proposal" | "other",
  priority:    "low" | "medium" | "high" | "urgent",
  dueDate:     Timestamp,
  reminderAt:  Timestamp | null,
  completedAt: Timestamp | null,
  createdAt:   Timestamp,
  updatedAt:   Timestamp,
  deletedAt:   Timestamp | null,
}
```

#### `deals/{dealId}`

```typescript
{
  leadId:       string,
  assignedTo:   string | null,
  title:        string,
  value:        number | null,  // EUR
  probability:  number,         // 0–100
  expectedClose: Timestamp | null,
  stage:        string,
  product:      "zentratto" | "signsisure" | "enterprise_agent" | "custom" | null,
  notes:        string | null,
  createdAt:    Timestamp,
  updatedAt:    Timestamp,
  closedAt:     Timestamp | null,
  deletedAt:    Timestamp | null,
}
```

#### `gdpr_consents/{consentId}` — APPEND-ONLY

```typescript
{
  leadId:        string,
  action:        "granted" | "withdrawn" | "updated" | "export_requested" |
                 "deletion_requested" | "deletion_completed",
  purpose:       "marketing" | "service_communication" | "analytics" | "all",
  consentText:   string,        // Testo esatto mostrato all'utente
  policyVersion: string,        // Es: "2.1"
  ipAddress:     string | null,
  userAgent:     string | null,
  dataHash:      string,        // SHA-256 del documento — Fase 3: su blockchain
  createdAt:     Timestamp,
  // NO updatedAt — questo documento non va MAI modificato
}
```

#### `form_submissions/{submissionId}`

```typescript
{
  formType:   "contact" | "playbook_download" | "assessment" |
              "booking" | "exit_intent" | "trial_request",
  rawData:    Record<string, unknown>,  // Dati grezzi del form
  ipAddress:  string | null,
  userAgent:  string | null,
  utm: {
    source: string | null,
    medium: string | null,
    campaign: string | null,
    content: string | null,
  },
  referrerUrl: string | null,
  landingPage: string | null,
  processed:   boolean,
  leadId:      string | null,   // Popolato dopo processing
  consentGiven:   boolean,
  consentText:    string,
  consentVersion: string,
  createdAt:      Timestamp,
  processedAt:    Timestamp | null,
}
```

---

## 6. Backend — FastAPI su Cloud Run

### `backend/app/firebase_admin.py`

```python
import firebase_admin
from firebase_admin import credentials, firestore_async, auth, storage
from app.config import settings
import json

def initialize_firebase():
    """
    In Cloud Run: usa Application Default Credentials (ADC).
    In locale: usa il service account JSON dal Secret Manager / file.
    """
    if firebase_admin._apps:
        return  # Già inizializzato

    if settings.GOOGLE_APPLICATION_CREDENTIALS_JSON:
        # Locale o CI — da Secret Manager
        cred_dict = json.loads(settings.GOOGLE_APPLICATION_CREDENTIALS_JSON)
        cred = credentials.Certificate(cred_dict)
    else:
        # Cloud Run — ADC automatico dal service account del servizio
        cred = credentials.ApplicationDefault()

    firebase_admin.initialize_app(cred, {
        "storageBucket": settings.FIREBASE_STORAGE_BUCKET,
        "projectId": settings.FIREBASE_PROJECT_ID,
    })

initialize_firebase()

# Client globali (thread-safe, riutilizzabili)
db      = firestore_async.client()   # Firestore async
bucket  = storage.bucket()          # Firebase Storage
```

### `backend/app/config.py`

```python
from pydantic_settings import BaseSettings
from typing import List, Optional

class Settings(BaseSettings):
    # Firebase / GCP
    FIREBASE_PROJECT_ID:    str
    FIREBASE_STORAGE_BUCKET: str  # es: aichain-crm-prod.appspot.com
    GOOGLE_APPLICATION_CREDENTIALS_JSON: Optional[str] = None
    # In Cloud Run: None → usa ADC del service account
    # In locale: JSON string dal Secret Manager

    # Cloud Tasks
    GCP_LOCATION:          str = "europe-west1"
    CLOUD_TASKS_QUEUE:     str = "crm-tasks"
    BACKEND_INTERNAL_URL:  str  # URL interno Cloud Run per task handlers

    # Email
    RESEND_API_KEY:        str
    EMAIL_FROM:            str = "noreply@aichainsolutions.net"

    # Security
    ALLOWED_ORIGINS:       List[str] = ["https://crm.aichainsolutions.net"]
    RATE_LIMIT_PER_MINUTE: int = 60

    # Feature
    DEBUG: bool = False

    class Config:
        env_file = ".env"

settings = Settings()
```

### `backend/app/deps.py`

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from firebase_admin import auth
from app.firebase_admin import db
from app.models.user import UserRecord

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> UserRecord:
    """
    Verifica il Firebase ID token nell'header Authorization: Bearer <token>
    Firebase Auth gestisce validità, scadenza e revoca automaticamente.
    """
    try:
        decoded = auth.verify_id_token(credentials.credentials)
    except auth.ExpiredIdTokenError:
        raise HTTPException(status_code=401, detail="Token scaduto")
    except auth.InvalidIdTokenError:
        raise HTTPException(status_code=401, detail="Token non valido")
    except Exception:
        raise HTTPException(status_code=401, detail="Autenticazione fallita")

    # Recupera ruolo da Firestore
    user_doc = await db.collection("users").document(decoded["uid"]).get()
    if not user_doc.exists:
        raise HTTPException(status_code=403, detail="Utente non registrato nel CRM")

    user_data = user_doc.to_dict()
    if not user_data.get("isActive", False):
        raise HTTPException(status_code=403, detail="Account disattivato")

    return UserRecord(
        uid=decoded["uid"],
        email=decoded.get("email"),
        role=user_data.get("role", "readonly"),
    )

async def require_admin(user: UserRecord = Depends(get_current_user)) -> UserRecord:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Richiesti permessi admin")
    return user

async def require_sales(user: UserRecord = Depends(get_current_user)) -> UserRecord:
    if user.role not in ("admin", "sales"):
        raise HTTPException(status_code=403, detail="Richiesti permessi sales")
    return user
```

### `backend/app/services/firestore_service.py`

```python
"""
Helper CRUD generico per Firestore.
Gestisce: paginazione, soft delete, timestamp automatici, batch writes.
"""
from google.cloud.firestore_v1 import AsyncClient, AsyncDocumentReference
from google.cloud.firestore_v1.base_query import BaseQuery
from datetime import datetime, timezone
from typing import Optional, Any
import uuid

def utcnow():
    return datetime.now(timezone.utc)

def new_id() -> str:
    return str(uuid.uuid4())

async def create_document(
    db: AsyncClient,
    collection: str,
    data: dict,
    doc_id: str = None,
) -> dict:
    """Crea documento con id custom e timestamp automatici."""
    doc_id = doc_id or new_id()
    now = utcnow()
    payload = {
        **data,
        "createdAt": now,
        "updatedAt": now,
        "deletedAt": None,
    }
    await db.collection(collection).document(doc_id).set(payload)
    return {"id": doc_id, **payload}

async def update_document(
    db: AsyncClient,
    collection: str,
    doc_id: str,
    data: dict,
) -> dict:
    """Update parziale — solo i campi presenti in data."""
    payload = {**data, "updatedAt": utcnow()}
    ref = db.collection(collection).document(doc_id)
    await ref.update(payload)
    snap = await ref.get()
    return {"id": doc_id, **snap.to_dict()}

async def soft_delete(
    db: AsyncClient,
    collection: str,
    doc_id: str,
) -> None:
    """Soft delete — imposta deletedAt, non rimuove il documento."""
    await db.collection(collection).document(doc_id).update({
        "deletedAt": utcnow(),
        "updatedAt": utcnow(),
    })

async def get_document(
    db: AsyncClient,
    collection: str,
    doc_id: str,
    include_deleted: bool = False,
) -> Optional[dict]:
    snap = await db.collection(collection).document(doc_id).get()
    if not snap.exists:
        return None
    data = {"id": doc_id, **snap.to_dict()}
    if not include_deleted and data.get("deletedAt"):
        return None
    return data

async def append_activity(
    db: AsyncClient,
    lead_id: str,
    activity_data: dict,
) -> dict:
    """Aggiunge activity alla subcollection — append-only."""
    activity_id = new_id()
    payload = {
        **activity_data,
        "leadId": lead_id,
        "createdAt": utcnow(),
        # NO updatedAt — append-only
    }
    await (
        db.collection("leads")
          .document(lead_id)
          .collection("activities")
          .document(activity_id)
          .set(payload)
    )
    # Increment counter atomico sul lead padre
    from google.cloud.firestore_v1 import Increment
    await db.collection("leads").document(lead_id).update({
        "activityCount": Increment(1),
        "lastActivityAt": utcnow(),
    })
    return {"id": activity_id, **payload}
```

### `backend/app/routers/leads.py`

```python
from fastapi import APIRouter, Depends, HTTPException, Query, status
from google.cloud.firestore_v1 import AsyncClient, FieldFilter
from typing import Optional
from app.firebase_admin import db
from app.deps import get_current_user, require_sales
from app.schemas.lead import LeadCreate, LeadUpdate, LeadStageUpdate
from app.services.lead_service import LeadService
from app.models.user import UserRecord
from app.utils.cloud_tasks import enqueue_task

router = APIRouter()

@router.get("")
async def list_leads(
    page_size:   int = Query(25, ge=1, le=100),
    last_doc_id: Optional[str] = None,   # Cursore per paginazione Firestore
    status:      Optional[str] = None,
    source:      Optional[str] = None,
    industry:    Optional[str] = None,
    assigned_to: Optional[str] = None,
    min_score:   Optional[int] = None,
    user:        UserRecord = Depends(require_sales),
):
    service = LeadService(db)
    return await service.list_leads(
        page_size=page_size,
        last_doc_id=last_doc_id,
        status=status,
        source=source,
        industry=industry,
        assigned_to=assigned_to,
        min_score=min_score,
    )

@router.post("", status_code=201)
async def create_lead(
    data: LeadCreate,
    user: UserRecord = Depends(require_sales),
):
    service = LeadService(db)

    # Verifica unicità email (Firestore non ha UNIQUE constraint)
    existing = await service.find_by_email(data.email)
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Lead con email {data.email} già presente (id: {existing['id']})"
        )

    lead = await service.create_lead(data, created_by=user.uid)

    # Calcolo score asincrono via Cloud Tasks
    await enqueue_task("recalculate-score", {"lead_id": lead["id"]})
    return lead

@router.get("/{lead_id}")
async def get_lead(
    lead_id: str,
    user: UserRecord = Depends(require_sales),
):
    service = LeadService(db)
    lead = await service.get_lead_with_activities(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead non trovato")
    return lead

@router.patch("/{lead_id}")
async def update_lead(
    lead_id: str,
    data: LeadUpdate,
    user: UserRecord = Depends(require_sales),
):
    service = LeadService(db)
    updated = await service.update_lead(lead_id, data, updated_by=user.uid)
    await enqueue_task("recalculate-score", {"lead_id": lead_id})
    return updated

@router.patch("/{lead_id}/stage")
async def update_stage(
    lead_id: str,
    data: LeadStageUpdate,
    user: UserRecord = Depends(require_sales),
):
    """
    Cambio stadio pipeline — logga automaticamente activity 'stage_changed'
    """
    service = LeadService(db)
    return await service.update_stage(lead_id, data, updated_by=user.uid)

@router.delete("/{lead_id}", status_code=204)
async def delete_lead(
    lead_id: str,
    user: UserRecord = Depends(require_sales),
):
    if user.role != "admin":
        raise HTTPException(403, "Solo admin può eliminare lead")
    from app.services.firestore_service import soft_delete
    await soft_delete(db, "leads", lead_id)
```

### `backend/app/routers/forms.py` — endpoint pubblico

```python
from fastapi import APIRouter, Request, BackgroundTasks, HTTPException
from app.firebase_admin import db
from app.schemas.forms import PlaybookFormData, AssessmentFormData, ContactFormData
from app.services.lead_service import LeadService
from app.services.gdpr_service import log_consent
from app.utils.cloud_tasks import enqueue_task
from app.utils.rate_limiter import check_rate_limit

router = APIRouter()

@router.post("/playbook", status_code=201)
async def submit_playbook(
    data: PlaybookFormData,
    request: Request,
):
    ip = str(request.client.host)
    await check_rate_limit(ip, "playbook", max_per_minute=5)

    if not data.consent_given:
        raise HTTPException(422, "Consenso GDPR obbligatorio")

    service = LeadService(db)
    lead = await service.create_or_update_from_form(
        email=data.email,
        form_data=data.model_dump(),
        form_type="playbook_download",
        source="playbook",
        ip=ip,
        user_agent=request.headers.get("user-agent"),
    )

    # Logga consenso GDPR (append-only)
    await log_consent(db, lead["id"], "granted", "marketing", data.consent_text, ip)

    # Sequenza email in background via Cloud Tasks
    await enqueue_task("email-sequence", {
        "lead_id": lead["id"],
        "sequence": "playbook_welcome",
    })

    return {
        "success": True,
        "download_url": "/downloads/aichain-playbook.pdf",
    }

@router.post("/contact", status_code=201)
async def submit_contact(data: ContactFormData, request: Request):
    ip = str(request.client.host)
    await check_rate_limit(ip, "contact", max_per_minute=3)

    if not data.consent_given:
        raise HTTPException(422, "Consenso GDPR obbligatorio")

    service = LeadService(db)
    lead = await service.create_or_update_from_form(
        email=data.email,
        form_data=data.model_dump(),
        form_type="contact",
        source="direct",
        ip=ip,
        user_agent=request.headers.get("user-agent"),
    )
    await log_consent(db, lead["id"], "granted", "service_communication", data.consent_text, ip)
    await enqueue_task("notify-sales", {"lead_id": lead["id"]})

    return {"success": True}
```

### `backend/app/utils/cloud_tasks.py`

```python
"""
Helper per enqueue job su Google Cloud Tasks.
Sostituisce Celery — nessun worker sempre attivo.
Cloud Tasks chiama il backend su /tasks/handlers/{task_name}
"""
import json
from google.cloud import tasks_v2
from app.config import settings

tasks_client = tasks_v2.CloudTasksAsyncClient()

async def enqueue_task(task_name: str, payload: dict, delay_seconds: int = 0):
    """
    Crea un task su Cloud Tasks.
    Cloud Tasks chiamerà POST {BACKEND_INTERNAL_URL}/tasks/handlers/{task_name}
    """
    parent = tasks_client.queue_path(
        settings.FIREBASE_PROJECT_ID,
        settings.GCP_LOCATION,
        settings.CLOUD_TASKS_QUEUE,
    )

    task = {
        "http_request": {
            "http_method": tasks_v2.HttpMethod.POST,
            "url": f"{settings.BACKEND_INTERNAL_URL}/tasks/handlers/{task_name}",
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(payload).encode(),
            "oidc_token": {
                # Autenticazione tra Cloud Tasks e Cloud Run via OIDC
                "service_account_email": f"crm-backend@{settings.FIREBASE_PROJECT_ID}.iam.gserviceaccount.com",
            },
        }
    }

    if delay_seconds > 0:
        from google.protobuf.timestamp_pb2 import Timestamp
        from datetime import datetime, timezone, timedelta
        schedule_time = datetime.now(timezone.utc) + timedelta(seconds=delay_seconds)
        ts = Timestamp()
        ts.FromDatetime(schedule_time)
        task["schedule_time"] = ts

    await tasks_client.create_task(parent=parent, task=task)
```

### `backend/app/tasks/handlers.py`

```python
"""
Endpoint chiamati da Cloud Tasks — non esposti pubblicamente.
Autenticati tramite OIDC token verificato da Cloud Run.
"""
from fastapi import APIRouter, Request, HTTPException
from app.firebase_admin import db
from app.services.scoring_service import calculate_lead_score
from app.services.email_service import send_sequence_email

router = APIRouter()

async def verify_cloud_tasks_request(request: Request):
    """Verifica che la request venga da Cloud Tasks (OIDC token)."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(403, "Richiesta non autorizzata")
    # In Cloud Run, la verifica OIDC è automatica se configurata nel servizio
    # In alternativa: verifica manuale del JWT con google-auth

@router.post("/recalculate-score")
async def handle_recalculate_score(request: Request):
    await verify_cloud_tasks_request(request)
    payload = await request.json()
    lead_id = payload["lead_id"]
    new_score = await calculate_lead_score(lead_id, db)
    return {"success": True, "score": new_score}

@router.post("/email-sequence")
async def handle_email_sequence(request: Request):
    await verify_cloud_tasks_request(request)
    payload = await request.json()
    await send_sequence_email(
        lead_id=payload["lead_id"],
        sequence=payload["sequence"],
        step=payload.get("step", 0),
        db=db,
    )
    return {"success": True}

@router.post("/notify-sales")
async def handle_notify_sales(request: Request):
    await verify_cloud_tasks_request(request)
    payload = await request.json()
    # Invia email al team sales con dettagli del nuovo lead
    await notify_sales_team(lead_id=payload["lead_id"], db=db)
    return {"success": True}
```

### `backend/Dockerfile`

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Dipendenze di sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Source code
COPY app/ ./app/

# Cloud Run: porta da variabile d'ambiente (default 8080)
ENV PORT=8080
EXPOSE 8080

# Avvio con Uvicorn — workers proporzionali alle CPU disponibili
CMD exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port $PORT \
    --workers 2 \
    --loop uvloop \
    --access-log
```

### `backend/requirements.txt`

```txt
fastapi==0.115.0
uvicorn[standard]==0.32.0
uvloop==0.21.0
pydantic==2.9.0
pydantic-settings==2.5.0
firebase-admin==6.5.0
google-cloud-tasks==2.16.3
google-cloud-secret-manager==2.20.0
httpx==0.27.0
python-multipart==0.0.12
slowapi==0.1.9
resend==2.3.0
python-jose[cryptography]==3.3.0
```

---

## 7. Frontend — Next.js su Cloud Run

### `frontend/lib/firebase.ts`

```typescript
import { initializeApp, getApps } from "firebase/app"
import { getAuth, connectAuthEmulator } from "firebase/auth"
import { getFirestore, connectFirestoreEmulator } from "firebase/firestore"
import { getStorage, connectStorageEmulator } from "firebase/storage"

const firebaseConfig = {
  apiKey:            process.env.NEXT_PUBLIC_FIREBASE_API_KEY!,
  authDomain:        process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN!,
  projectId:         process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID!,
  storageBucket:     process.env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET!,
  messagingSenderId: process.env.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID!,
  appId:             process.env.NEXT_PUBLIC_FIREBASE_APP_ID!,
}

const app = getApps().length === 0 ? initializeApp(firebaseConfig) : getApps()[0]

export const auth    = getAuth(app)
export const firestoreDb = getFirestore(app)
export const storage = getStorage(app)

// Connetti emulatori in locale
if (process.env.NODE_ENV === "development" && process.env.NEXT_PUBLIC_USE_EMULATOR === "true") {
  connectAuthEmulator(auth, "http://localhost:9099", { disableWarnings: true })
  connectFirestoreEmulator(firestoreDb, "localhost", 8080)
  connectStorageEmulator(storage, "localhost", 9199)
}
```

### `frontend/lib/auth.ts`

```typescript
import {
  signInWithEmailAndPassword,
  signOut,
  onAuthStateChanged,
  User,
  getIdToken,
} from "firebase/auth"
import { auth } from "./firebase"

export async function login(email: string, password: string) {
  return signInWithEmailAndPassword(auth, email, password)
}

export async function logout() {
  return signOut(auth)
}

export function onAuthChange(callback: (user: User | null) => void) {
  return onAuthStateChanged(auth, callback)
}

/**
 * Restituisce il token Firebase fresco (auto-refresh se scaduto).
 * Usato dall'interceptor Axios per ogni request al backend FastAPI.
 */
export async function getAuthToken(): Promise<string | null> {
  const user = auth.currentUser
  if (!user) return null
  return getIdToken(user, /* forceRefresh */ false)
}
```

### `frontend/lib/api.ts`

```typescript
import axios from "axios"
import { getAuthToken } from "./auth"

export const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL + "/api/v1",
  headers: { "Content-Type": "application/json" },
})

// Inietta token Firebase in ogni request
api.interceptors.request.use(async (config) => {
  const token = await getAuthToken()
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Gestisci errori globali
api.interceptors.response.use(
  (res) => res,
  (error) => {
    if (error.response?.status === 401) {
      window.location.href = "/login"
    }
    return Promise.reject(error)
  }
)
```

### `frontend/hooks/useAuth.ts`

```typescript
"use client"
import { useState, useEffect } from "react"
import { User } from "firebase/auth"
import { onAuthChange } from "@/lib/auth"

export function useAuth() {
  const [user, setUser]       = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const unsubscribe = onAuthChange((firebaseUser) => {
      setUser(firebaseUser)
      setLoading(false)
    })
    return unsubscribe
  }, [])

  return { user, loading, isAuthenticated: !!user }
}
```

### `frontend/Dockerfile`

```dockerfile
FROM node:20-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# Immagine produzione minimale
FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV PORT=3000

COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public

EXPOSE 3000
CMD node server.js
```

---

## 8. Autenticazione — Firebase Auth

### Flusso completo

```
1. Frontend: login con email/password
   → Firebase Auth SDK → verifica credenziali
   → ritorna: { idToken (1h), refreshToken (∞) }

2. Frontend: ogni request API
   → getIdToken() → refresh automatico se scaduto
   → Header: Authorization: Bearer <idToken>

3. Backend FastAPI: ogni endpoint protetto
   → auth.verify_id_token(token)
   → recupera ruolo da Firestore /users/{uid}
   → autorizza o rifiuta

4. Token revoca (logout o account disabilitato)
   → Firebase Auth invalida tutti i token esistenti
   → Backend riceve 401 al prossimo verify_id_token
```

### Creazione utenti CRM (solo admin)

```python
# backend/app/routers/auth.py
from firebase_admin import auth
from app.services.firestore_service import create_document

@router.post("/users", status_code=201)
async def create_crm_user(
    data: UserCreate,
    admin: UserRecord = Depends(require_admin),
):
    """
    Crea utente in Firebase Auth + documento in Firestore /users/{uid}
    """
    # 1. Crea in Firebase Auth
    firebase_user = auth.create_user(
        email=data.email,
        password=data.temporary_password,
        display_name=data.full_name,
    )

    # 2. Crea profilo in Firestore
    await create_document(
        db=db,
        collection="users",
        doc_id=firebase_user.uid,  # uid = doc_id
        data={
            "uid":      firebase_user.uid,
            "email":    data.email,
            "fullName": data.full_name,
            "role":     data.role,
            "isActive": True,
        }
    )

    # 3. Invia email "imposta password" via Firebase Auth
    link = auth.generate_password_reset_link(data.email)
    await send_onboarding_email(data.email, link)

    return {"uid": firebase_user.uid, "email": data.email}
```

---

## 9. Task asincroni — Cloud Tasks

### Creazione queue

```bash
gcloud tasks queues create crm-tasks \
  --location=europe-west1 \
  --max-attempts=3 \
  --min-backoff=10s \
  --max-backoff=300s \
  --max-doublings=3
```

### Pattern di utilizzo

```
Backend riceve request → risponde subito al client (< 200ms)
                      → enqueue_task("nome-task", payload)
                               │
                     Cloud Tasks (europe-west1)
                               │
                     POST /tasks/handlers/nome-task   ← (dopo Ns)
                               │
                     Backend esegue lavoro pesante
                     (email, scoring, notifiche)
```

### Task disponibili in Fase 1

| Task name | Trigger | Azione |
|---|---|---|
| `recalculate-score` | Nuovo lead, nuova activity, update profilo | Ricalcola lead score su Firestore |
| `email-sequence` | Form submit, booking, stage change | Invia prossima email della sequenza |
| `notify-sales` | Nuovo lead caldo (score > 70) | Notifica email al sales assignato |
| `send-booking-reminder` | Booking creato | Reminder 24h e 1h prima via Resend |
| `process-form-submission` | Form submit | Crea/aggiorna lead da form_submission raw |

---

## 10. Storage — Firebase Storage

### Struttura bucket

```
gs://aichain-crm-prod.appspot.com/
├── leads/{leadId}/
│   ├── attachments/          # File allegati alla scheda lead
│   └── proposals/            # PDF offerte generate
├── downloads/
│   └── aichain-playbook.pdf  # Playbook (accesso pubblico read)
└── avatars/{uid}/
    └── avatar.jpg
```

### Security rules — `storage.rules`

```
rules_version = '2';
service firebase.storage {
  match /b/{bucket}/o {

    // Download pubblici (playbook)
    match /downloads/{file} {
      allow read: if true;
      allow write: if false;  // Solo backend può scrivere
    }

    // File lead — solo utenti CRM autenticati
    match /leads/{leadId}/{allPaths=**} {
      allow read:  if request.auth != null;
      allow write: if request.auth != null;
      allow delete: if request.auth != null
                    && firestore.get(/databases/(default)/documents/users/$(request.auth.uid)).data.role == 'admin';
    }

    // Avatar profilo — solo il proprio
    match /avatars/{uid}/{file} {
      allow read:  if request.auth != null;
      allow write: if request.auth.uid == uid;
    }
  }
}
```

---

## 11. GDPR & compliance EU

### Residenza dei dati

| Dato | Servizio | Regione |
|---|---|---|
| Lead, attività, tasks | Firestore | **eur3** (EU multi-region) |
| File allegati | Firebase Storage | **europe-west1** (Belgio) |
| Autenticazione | Firebase Auth | **eur3** |
| Log applicazione | Cloud Logging | **europe-west1** |
| Email transazionali | Resend (server EU Frankfurt) | **EU** |

> ⚠️ **Nessun dato lascia l'UE.** Verificare che Resend sia configurato con endpoint EU: `api.eu.resend.com`

### Implementazione diritti GDPR

```python
# backend/app/services/gdpr_service.py
import hashlib, json
from datetime import datetime, timezone
from app.firebase_admin import db
from app.services.firestore_service import append_activity, utcnow

async def log_consent(
    db, lead_id: str, action: str,
    purpose: str, consent_text: str, ip: str,
    policy_version: str = "2.1",
):
    """
    Registra consenso in gdpr_consents — APPEND-ONLY.
    In Fase 3: il dataHash verrà ancorato su blockchain via SignSisure.
    """
    payload = {
        "leadId":        lead_id,
        "action":        action,
        "purpose":       purpose,
        "consentText":   consent_text,
        "policyVersion": policy_version,
        "ipAddress":     ip,
        "createdAt":     utcnow(),
    }
    # Hash SHA-256 del documento per integrità
    payload["dataHash"] = hashlib.sha256(
        json.dumps(payload, default=str, sort_keys=True).encode()
    ).hexdigest()

    consent_id = new_id()
    await db.collection("gdpr_consents").document(consent_id).set(payload)
    return consent_id

async def gdpr_export(lead_id: str) -> dict:
    """
    Art. 20 GDPR — Portabilità dei dati.
    Ritorna tutti i dati del lead in formato JSON.
    """
    lead = await db.collection("leads").document(lead_id).get()
    activities = await db.collection("leads").document(lead_id)\
        .collection("activities").get()
    tasks = await db.collection("leads").document(lead_id)\
        .collection("tasks").get()
    consents = await db.collection("gdpr_consents")\
        .where(filter=FieldFilter("leadId", "==", lead_id)).get()

    return {
        "exported_at": utcnow().isoformat(),
        "lead": lead.to_dict() if lead.exists else None,
        "activities": [a.to_dict() for a in activities],
        "tasks": [t.to_dict() for t in tasks],
        "gdpr_consents": [c.to_dict() for c in consents],
    }

async def gdpr_erase(lead_id: str, erased_by_uid: str):
    """
    Art. 17 GDPR — Diritto all'oblio.
    Anonimizza i dati personali — NON cancella il documento.
    Mantiene i dati aggregati per analytics.
    """
    anonymized = {
        "firstName":   "CANCELLATO",
        "lastName":    "GDPR",
        "email":       f"gdpr-erased-{lead_id}@deleted.invalid",
        "phone":       None,
        "linkedinUrl": None,
        "notes":       None,
        "customFields": {},
        "deletedAt":   utcnow(),
        "updatedAt":   utcnow(),
    }
    await db.collection("leads").document(lead_id).update(anonymized)
    await log_consent(db, lead_id, "deletion_completed", "all", "GDPR Art.17", erased_by_uid)
```

---

## 12. CI/CD — Cloud Build

### `backend/cloudbuild.yaml`

```yaml
steps:
  # 1. Test
  - name: "python:3.12"
    entrypoint: bash
    args:
      - -c
      - |
        pip install -r requirements.txt -r requirements-dev.txt
        pytest tests/ -v --tb=short
    env:
      - "FIREBASE_PROJECT_ID=aichain-crm-dev"
      - "NEXT_PUBLIC_USE_EMULATOR=true"

  # 2. Build immagine Docker
  - name: "gcr.io/cloud-builders/docker"
    args:
      - build
      - -t
      - europe-west1-docker.pkg.dev/$PROJECT_ID/crm/backend:$SHORT_SHA
      - -t
      - europe-west1-docker.pkg.dev/$PROJECT_ID/crm/backend:latest
      - .

  # 3. Push su Artifact Registry (EU)
  - name: "gcr.io/cloud-builders/docker"
    args:
      - push
      - --all-tags
      - europe-west1-docker.pkg.dev/$PROJECT_ID/crm/backend

  # 4. Deploy su Cloud Run (europe-west1)
  - name: "gcr.io/google.com/cloudsdktool/cloud-sdk"
    entrypoint: gcloud
    args:
      - run
      - deploy
      - crm-backend
      - --image=europe-west1-docker.pkg.dev/$PROJECT_ID/crm/backend:$SHORT_SHA
      - --region=europe-west1
      - --platform=managed
      - --no-allow-unauthenticated  # Solo invocazioni autenticate
      - --service-account=crm-backend@$PROJECT_ID.iam.gserviceaccount.com
      - --memory=512Mi
      - --cpu=1
      - --min-instances=0
      - --max-instances=10
      - --concurrency=80

images:
  - europe-west1-docker.pkg.dev/$PROJECT_ID/crm/backend:$SHORT_SHA

options:
  logging: CLOUD_LOGGING_ONLY
```

### Setup Cloud Build trigger

```bash
# Trigger: push su branch main → deploy produzione
gcloud builds triggers create github \
  --repo-name=aichain-crm \
  --repo-owner=aichain-solutions \
  --branch-pattern=^main$ \
  --build-config=backend/cloudbuild.yaml \
  --name=crm-backend-prod

# Trigger: push su branch develop → deploy staging
gcloud builds triggers create github \
  --repo-name=aichain-crm \
  --repo-owner=aichain-solutions \
  --branch-pattern=^develop$ \
  --build-config=backend/cloudbuild.yaml \
  --name=crm-backend-staging \
  --substitutions=_ENV=staging
```

---

## 13. Variabili d'ambiente & Secret Manager

### Strategia: Secret Manager in produzione, `.env` in locale

```bash
# Crea secrets in Secret Manager (una volta sola)
echo -n "re_xxxxxxxxxx" | gcloud secrets create RESEND_API_KEY \
  --data-file=- \
  --replication-policy=user-managed \
  --locations=europe-west1

echo -n "your-firebase-service-account-json" | gcloud secrets create \
  GOOGLE_APPLICATION_CREDENTIALS_JSON \
  --data-file=- \
  --replication-policy=user-managed \
  --locations=europe-west1

# Concedi accesso al service account del backend
gcloud secrets add-iam-policy-binding RESEND_API_KEY \
  --member=serviceAccount:crm-backend@$PROJECT_ID.iam.gserviceaccount.com \
  --role=roles/secretmanager.secretAccessor
```

### Backend — `.env` (locale)

```bash
# Firebase / GCP
FIREBASE_PROJECT_ID=aichain-crm-dev
FIREBASE_STORAGE_BUCKET=aichain-crm-dev.appspot.com
GOOGLE_APPLICATION_CREDENTIALS_JSON={"type":"service_account",...}  # JSON del SA

# Cloud Tasks
GCP_LOCATION=europe-west1
CLOUD_TASKS_QUEUE=crm-tasks
BACKEND_INTERNAL_URL=http://localhost:8000  # In prod: URL interno Cloud Run

# Email
RESEND_API_KEY=re_xxxxxxxxxx
EMAIL_FROM=noreply@aichainsolutions.net

# Security
ALLOWED_ORIGINS=["http://localhost:3000"]
DEBUG=true
RATE_LIMIT_PER_MINUTE=60
```

### Frontend — `.env.local` (locale)

```bash
# Firebase Client SDK (valori pubblici — OK nel frontend)
NEXT_PUBLIC_FIREBASE_API_KEY=AIzaSy...
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=aichain-crm-dev.firebaseapp.com
NEXT_PUBLIC_FIREBASE_PROJECT_ID=aichain-crm-dev
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=aichain-crm-dev.appspot.com
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=123456789
NEXT_PUBLIC_FIREBASE_APP_ID=1:123456789:web:abc123

# Backend FastAPI
NEXT_PUBLIC_API_URL=http://localhost:8000

# Emulatori Firebase in locale
NEXT_PUBLIC_USE_EMULATOR=true
```

### `docker-compose.yml` — Sviluppo locale con emulatori Firebase

```yaml
version: "3.9"
services:

  firebase-emulators:
    image: node:20-alpine
    working_dir: /app
    command: npx firebase emulators:start --project aichain-crm-dev
    ports:
      - "4000:4000"   # Firebase Emulator UI
      - "9099:9099"   # Auth emulator
      - "8080:8080"   # Firestore emulator
      - "9199:9199"   # Storage emulator
    volumes:
      - ./firebase.json:/app/firebase.json
      - ./firestore.rules:/app/firestore.rules
      - ./firestore.indexes.json:/app/firestore.indexes.json
      - firebase_data:/app/.firebase

  backend:
    build: ./backend
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    ports:
      - "8000:8000"
    env_file: ./backend/.env
    environment:
      - FIRESTORE_EMULATOR_HOST=firebase-emulators:8080
      - FIREBASE_AUTH_EMULATOR_HOST=firebase-emulators:9099
      - FIREBASE_STORAGE_EMULATOR_HOST=firebase-emulators:9199
    depends_on:
      - firebase-emulators
    volumes:
      - ./backend/app:/app/app

  frontend:
    build: ./frontend
    command: npm run dev
    ports:
      - "3000:3000"
    env_file: ./frontend/.env.local
    depends_on:
      - backend
    volumes:
      - ./frontend:/app
      - /app/node_modules

volumes:
  firebase_data:
```

---

## 14. Costi stimati

### Fase 1 — primi 3 mesi (traffico iniziale basso)

```
Scenario: 500 lead nel CRM, 50 form submit/mese, 5 utenti team

Firebase:
  Firestore reads:  ~100K/mese   → €0.00 (free tier: 50K/giorno)
  Firestore writes: ~20K/mese    → €0.00 (free tier: 20K/giorno)
  Firebase Auth:    < 10K utenti → €0.00 (free tier)
  Storage:          < 5GB        → €0.00 (free tier)

GCP:
  Cloud Run Backend:  ~10K requests/mese, 512MB → €2–5
  Cloud Run Frontend: ~50K requests/mese, 256MB → €3–8
  Cloud Tasks:        < 1M task/mese            → €0.00 (free tier)
  Cloud Build:        < 120 min/giorno          → €0.00 (free tier)
  Secret Manager:     < 10K accessi             → €0.00 (free tier)
  Artifact Registry:  ~2GB                      → €0.20

Email (Resend):
  < 3K email/mese                               → €0.00 (free tier)

TOTALE STIMATO: €5–15/mese
```

### Crescita: 10K lead, 500 form/mese

```
TOTALE STIMATO: €30–80/mese
```

---

## 15. Checklist sviluppatore

### Setup iniziale (giorno 1)

```bash
# 1. Installa Firebase CLI e GCP SDK
npm install -g firebase-tools
curl https://sdk.cloud.google.com | bash

# 2. Login
firebase login
gcloud auth login
gcloud config set project aichain-crm-dev

# 3. Clona repository
git clone git@github.com:aichain-solutions/aichain-crm.git
cd aichain-crm

# 4. Avvia emulatori Firebase
firebase emulators:start

# 5. Backend (in altro terminale)
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Compila i valori
uvicorn app.main:app --reload

# 6. Frontend (in altro terminale)
cd frontend
npm install
cp .env.example .env.local  # Compila i valori
npm run dev

# Verifica: http://localhost:4000 (Firebase UI)
#           http://localhost:8000/api/docs (FastAPI OpenAPI)
#           http://localhost:3000 (Next.js CRM)
```

### Sprint 1 — settimane 1–3

- [ ] Configurazione Firebase progetto dev + prod (regione eur3)
- [ ] Firestore rules + indexes deployati e testati
- [ ] Service account CRM con permessi minimi (Principle of Least Privilege)
- [ ] `firebase_admin.py` — init con ADC + fallback JSON locale
- [ ] `deps.py` — verifica token Firebase + recupero ruolo
- [ ] Models Pydantic: Lead, Activity, Task, Deal
- [ ] `firestore_service.py` — CRUD helpers generici
- [ ] Router `/api/v1/leads` — CRUD completo
- [ ] Router `/api/v1/forms` — endpoint pubblici + rate limiting
- [ ] `gdpr_service.py` — log_consent, gdpr_export, gdpr_erase
- [ ] Cloud Tasks queue creata in europe-west1
- [ ] `cloud_tasks.py` + `tasks/handlers.py`

### Sprint 2 — settimane 4–6

- [ ] Frontend: `firebase.ts` con emulator support
- [ ] Frontend: `useAuth.ts` + pagina login
- [ ] Frontend: `LeadTable` con filtri e paginazione cursor-based
- [ ] Frontend: `LeadDetail` con `ActivityTimeline`
- [ ] Frontend: `KanbanBoard` drag & drop (dnd-kit)
- [ ] Frontend: Form multi-step con UTM capture
- [ ] Frontend: `Dashboard` con KPI (TanStack Query + Recharts)
- [ ] Sequenza email Resend (endpoint EU: api.eu.resend.com)
- [ ] Booking slots + calendario prenotazioni
- [ ] Scoring engine + Cloud Task `recalculate-score`

### Sprint 3 — settimane 7–8

- [ ] Artifact Registry creato in europe-west1
- [ ] `cloudbuild.yaml` backend + frontend testati
- [ ] Cloud Build trigger su branch main → deploy prod
- [ ] Cloud Run backend deployato con min-instances=0
- [ ] Cloud Run frontend deployato
- [ ] Secret Manager: tutti i secret migrati da .env
- [ ] Test E2E: flusso form → lead → pipeline → task
- [ ] Security review: Firestore rules, CORS, rate limit
- [ ] GDPR audit: export, erasure, consent log testati
- [ ] Monitoring: Cloud Logging alert su errori 5xx
- [ ] Handover QA + documentazione endpoint OpenAPI

---

> **Prossimo documento:** `CRM_ARCHITECTURE_PHASE2.md`
> Automation: Cloud Pub/Sub per eventi, sequenze email avanzate,
> lead scoring ML con Vertex AI, WhatsApp Business API.

---

*AiChain Solutions — CTO Office · Fase 1 Foundation · Maggio 2026*
*Stack: FastAPI · Firebase (Firestore + Auth + Storage) · Next.js 14 · GCP europe-west1*
