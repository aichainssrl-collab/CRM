# AiChain CRM — Specifiche Tecniche Fase 3
> **Intelligence: ZenTratto RAG · Vertex AI · SignSisure Blockchain · BigQuery · Revenue Forecasting**
> **Stack: FastAPI · Firebase · Vertex AI (europe-west4) · BigQuery EU · SignSisure API**
> Versione: 1.0 · Prerequisito: Fase 1 + Fase 2 completate · Autore: AiChain Solutions CTO

---

## Indice

1. [Panoramica architetturale](#1-panoramica-architetturale)
2. [Nuovi servizi GCP — setup](#2-nuovi-servizi-gcp--setup)
3. [Struttura repository — delta da Fase 2](#3-struttura-repository--delta-da-fase-2)
4. [Firestore + BigQuery — nuove collezioni e dataset](#4-firestore--bigquery--nuove-collezioni-e-dataset)
5. [ZenTratto RAG sul CRM](#5-zentratto-rag-sul-crm)
6. [AI Email Writer — Gemini](#6-ai-email-writer--gemini)
7. [Trascrizione e analisi call](#7-trascrizione-e-analisi-call)
8. [Lead scoring predittivo — Vertex AI](#8-lead-scoring-predittivo--vertex-ai)
9. [Blockchain audit trail — SignSisure](#9-blockchain-audit-trail--signsisure)
10. [BigQuery analytics pipeline](#10-bigquery-analytics-pipeline)
11. [Revenue forecasting](#11-revenue-forecasting)
12. [Report CEO/CMO — generato da LLM](#12-report-ceocmo--generato-da-llm)
13. [Customer success module](#13-customer-success-module)
14. [CRM API pubblica](#14-crm-api-pubblica)
15. [Frontend — nuovi componenti](#15-frontend--nuovi-componenti)
16. [Firestore rules — aggiornamento Fase 3](#16-firestore-rules--aggiornamento-fase-3)
17. [CI/CD — aggiornamento Fase 3](#17-cicd--aggiornamento-fase-3)
18. [Costi stimati Fase 3](#18-costi-stimati-fase-3)
19. [Checklist sviluppatore](#19-checklist-sviluppatore)

---

## 1. Panoramica architetturale

```
┌────────────────────────────────────────────────────────────────────────────┐
│                        GOOGLE CLOUD PLATFORM — EU                          │
│                                                                            │
│  ┌───────────────────┐      ┌─────────────────────────────────────────┐   │
│  │  Cloud Run        │      │  Cloud Run — Backend FastAPI            │   │
│  │  Next.js CRM      │◄────►│  + router Fase 3 (AI, blockchain, API) │   │
│  └───────────────────┘      └────────────────────┬────────────────────┘   │
│                                                  │                        │
│     ┌────────────────────────────────────────────┼──────────────────────┐ │
│     │                                            │                      │ │
│  ┌──▼──────────────────┐         ┌───────────────▼───────────────────┐ │ │
│  │  VERTEX AI          │         │  FIREBASE (eur3)                  │ │ │
│  │  europe-west4       │         │  Firestore · Auth · Storage       │ │ │
│  │                     │         │  Realtime DB                      │ │ │
│  │  ┌───────────────┐  │         └───────────────────────────────────┘ │ │
│  │  │ Gemini 1.5 Pro│  │                                               │ │
│  │  │ (email writer │  │         ┌───────────────────────────────────┐ │ │
│  │  │  report CEO   │  │         │  BIGQUERY (EU multi-region)       │ │ │
│  │  │  RAG + chat)  │  │         │  Dataset: aichain_crm_analytics   │ │ │
│  │  └───────────────┘  │         │                                   │ │ │
│  │  ┌───────────────┐  │         │  leads_snapshot (daily)           │ │ │
│  │  │ Matching      │  │         │  pipeline_history                 │ │ │
│  │  │ Engine        │  │         │  email_performance                │ │ │
│  │  │ (Vector DB    │  │         │  revenue_forecast                 │ │ │
│  │  │  per RAG CRM) │  │         │  activity_events                  │ │ │
│  │  └───────────────┘  │         └───────────────────────────────────┘ │ │
│  │  ┌───────────────┐  │                                               │ │
│  │  │ Speech-to-    │  │         ┌───────────────────────────────────┐ │ │
│  │  │ Text v2       │  │         │  Cloud Pub/Sub (da Fase 2)        │ │ │
│  │  │ (call         │  │         │  + 2 nuovi topic Fase 3           │ │ │
│  │  │  transcription│  │         │  crm.ai.events                   │ │ │
│  │  └───────────────┘  │         │  crm.blockchain.events           │ │ │
│  └─────────────────────┘         └───────────────────────────────────┘ │ │
│                                                                          │ │
│  ┌──────────────────────────────────────────────────────────────────┐   │ │
│  │                Cloud Run — Workers Fase 3                        │   │ │
│  │  ai_worker · blockchain_worker · analytics_worker · cs_worker   │   │ │
│  └──────────────────────────────────────────────────────────────────┘   │ │
│                                                                          │ │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────────────┐    │ │
│  │ Cloud Scheduler │  │ Secret Manager  │  │ Artifact Registry    │    │ │
│  │ + 4 nuovi job   │  │ + chiavi AI/WA  │  │ + immagini Fase 3    │    │ │
│  └─────────────────┘  └─────────────────┘  └──────────────────────┘    │ │
└──────────────────────────────────────────────────────────────────────────┘ │
           │                          │                                       │
   ┌───────▼───────┐        ┌─────────▼──────────┐                           │
   │  SignSisure   │        │  Google Meet / Zoom │                           │
   │  API          │        │  Recording API      │                           │
   │  (blockchain  │        │  (trascrizione call)│                           │
   │   notarizza.) │        └─────────────────────┘                           │
   └───────────────┘                                                          │
```

### Note sulle regioni

| Servizio | Regione | Motivazione |
|---|---|---|
| Cloud Run, Firebase, Pub/Sub | `europe-west1` (Belgio) | Come Fase 1–2 |
| Vertex AI Gemini | `europe-west4` (Olanda) | Unica regione EU con Gemini 1.5 Pro |
| Vertex AI Matching Engine | `europe-west4` | Stessa regione del modello |
| BigQuery | `EU` (multi-region) | Massima disponibilità, GDPR-compliant |
| Cloud Speech-to-Text | `europe-west1` | Disponibile, stessa regione backend |

> **Latenza cross-region** `europe-west1` ↔ `europe-west4`: ~5ms — trascurabile
> per chiamate asincrone. Tutte le chiamate Vertex AI sono **fire-and-forget** via
> Cloud Tasks / worker — non impattano la latenza percepita dall'utente.

---

## 2. Nuovi servizi GCP — setup

```bash
# Abilita nuovi servizi
gcloud services enable \
  aiplatform.googleapis.com \
  speech.googleapis.com \
  bigquery.googleapis.com \
  bigquerydatatransfer.googleapis.com \
  bigqueryconnection.googleapis.com

# ── BigQuery — Dataset EU ────────────────────────────────────────
bq mk --dataset \
  --location=EU \
  --description="CRM Analytics — AiChain" \
  $PROJECT_ID:aichain_crm_analytics

# ── Vertex AI — Matching Engine Index ───────────────────────────
# (per RAG sul CRM — vedi sezione 5)
gcloud ai indexes create \
  --metadata-file=vertex_ai/crm_index_metadata.json \
  --region=europe-west4 \
  --display-name="crm-leads-index"

# ── Service account AI worker ────────────────────────────────────
gcloud iam service-accounts create crm-ai-worker \
  --display-name="CRM AI Worker"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:crm-ai-worker@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:crm-ai-worker@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/bigquery.dataEditor"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:crm-ai-worker@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/speech.client"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:crm-ai-worker@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/datastore.user"
```

---

## 3. Struttura repository — delta da Fase 2

```
aichain-crm/
├── backend/
│   └── app/
│       ├── routers/
│       │   ├── [FASE 1–2 — invariati]
│       │   ├── ai.py                  ✨ NUOVO — email writer, chat RAG, scoring AI
│       │   ├── calls.py               ✨ NUOVO — upload recording, trascrizione
│       │   ├── blockchain.py          ✨ NUOVO — notarizzazione via SignSisure
│       │   ├── analytics.py           🔄 AGGIORNATO — BigQuery queries
│       │   ├── forecasting.py         ✨ NUOVO — revenue forecast
│       │   ├── customer_success.py    ✨ NUOVO — NPS, churn detection
│       │   └── public_api/            ✨ NUOVO — CRM API pubblica v1
│       │       ├── __init__.py
│       │       ├── router.py          Endpoint pubblici con API key auth
│       │       ├── auth.py            API key management
│       │       └── webhooks_out.py    Outbound webhooks
│       │
│       ├── services/
│       │   ├── [FASE 1–2 — invariati]
│       │   ├── gemini_service.py      ✨ NUOVO — wrapper Vertex AI Gemini
│       │   ├── rag_service.py         ✨ NUOVO — ZenTratto RAG sul CRM
│       │   ├── speech_service.py      ✨ NUOVO — Cloud Speech-to-Text
│       │   ├── call_analysis_service.py ✨ NUOVO — analisi LLM post-call
│       │   ├── signsisure_service.py  ✨ NUOVO — blockchain notarizzazione
│       │   ├── bigquery_service.py    ✨ NUOVO — query e ingestion BigQuery
│       │   ├── forecast_service.py    ✨ NUOVO — revenue forecasting
│       │   ├── cs_service.py          ✨ NUOVO — customer success logic
│       │   └── api_key_service.py     ✨ NUOVO — gestione API key esterne
│       │
│       ├── workers/
│       │   ├── [FASE 2 — invariati]
│       │   ├── ai_worker/             ✨ NUOVO — processa job AI pesanti
│       │   │   ├── main.py
│       │   │   ├── handlers.py        email_writer, call_analysis, scoring_ai
│       │   │   └── Dockerfile
│       │   ├── blockchain_worker/     ✨ NUOVO — notarizza su SignSisure
│       │   │   ├── main.py
│       │   │   ├── handlers.py
│       │   │   └── Dockerfile
│       │   ├── analytics_worker/      ✨ NUOVO — sync Firestore → BigQuery
│       │   │   ├── main.py
│       │   │   ├── handlers.py
│       │   │   └── Dockerfile
│       │   └── cs_worker/             ✨ NUOVO — NPS, churn, upsell
│       │       ├── main.py
│       │       └── Dockerfile
│       │
│       └── scheduler_handlers/
│           ├── [FASE 2 — invariati]
│           ├── bigquery_sync.py       ✨ NUOVO — sync notturno Firestore→BQ
│           ├── nps_send.py            ✨ NUOVO — NPS automatico 30/90 giorni
│           ├── churn_check.py         ✨ NUOVO — check inattività clienti
│           └── forecast_refresh.py    ✨ NUOVO — aggiorna previsioni
│
├── frontend/
│   └── app/crm/
│       ├── [FASE 1–2 — invariati]
│       ├── ai-assistant/page.tsx      ✨ NUOVO — chat RAG + email writer
│       ├── calls/page.tsx             ✨ NUOVO — lista call + trascrizioni
│       ├── analytics/page.tsx         🔄 AGGIORNATO — BigQuery-powered
│       ├── forecasting/page.tsx       ✨ NUOVO — revenue forecast dashboard
│       ├── customer-success/page.tsx  ✨ NUOVO — NPS, churn, accounts
│       └── developer/page.tsx         ✨ NUOVO — API keys + docs
│
├── vertex_ai/                         ✨ NUOVO
│   ├── crm_index_metadata.json        Config Matching Engine index
│   ├── embed_leads.py                 Script one-shot: embeds lead data
│   └── update_index.py                Aggiornamento incrementale index
│
└── bigquery/                          ✨ NUOVO
    ├── schemas/                       JSON schema per ogni tabella BQ
    │   ├── leads_snapshot.json
    │   ├── pipeline_history.json
    │   ├── email_performance.json
    │   └── activity_events.json
    └── views/                         SQL view per dashboard
        ├── conversion_funnel.sql
        ├── revenue_by_source.sql
        ├── email_engagement.sql
        └── forecast_model.sql
```

---

## 4. Firestore + BigQuery — nuove collezioni e dataset

### Nuove collezioni Firestore Fase 3

```
firestore-root/
├── [FASE 1–2 — invariate]
├── call_recordings/{callId}           ✨ Registrazioni call + trascrizione
├── call_insights/{callId}             ✨ Analisi AI post-call
├── blockchain_records/{recordId}      ✨ Proof of notarizzazione (append-only)
├── ai_suggestions/{suggestionId}      ✨ Suggerimenti AI (email bozze, score AI)
├── nps_surveys/{surveyId}             ✨ Survey NPS inviati ai clienti
├── accounts/{accountId}               ✨ Clienti attivi post-vendita
│   └── health_scores/{scoreId}        ✨ Health score timeline
├── api_keys/{keyId}                   ✨ API key per accesso esterno
└── outbound_webhooks/{webhookId}      ✨ Webhook outbound configurati
```

### Schema documenti Fase 3

#### `call_recordings/{callId}`

```typescript
{
  leadId:          string,
  dealId:          string | null,
  userId:          string,              // Chi ha condotto la call
  platform:        "google_meet" | "zoom" | "phone" | "other",
  recordingUrl:    string | null,       // URL temporaneo della registrazione
  storagePath:     string | null,       // gs://bucket/calls/{callId}/audio.mp3
  durationSeconds: number,
  status:          "uploaded" | "transcribing" | "transcribed" | "analyzed" | "failed",
  // Trascrizione
  transcript:      string | null,       // Testo completo trascritto
  transcriptWords: Array<{             // Word-level timing per highlight
    word:       string,
    startTime:  number,               // Secondi dall'inizio
    endTime:    number,
    confidence: number,
  }> | null,
  language:        string,              // "it-IT" | "en-US"
  createdAt:       Timestamp,
  transcribedAt:   Timestamp | null,
  analyzedAt:      Timestamp | null,
}
```

#### `call_insights/{callId}`

```typescript
{
  callId:          string,
  leadId:          string,
  // Analisi LLM
  summary:         string,             // Riassunto 3-5 frasi
  sentiment:       "positive" | "neutral" | "negative",
  interestLevel:   number,             // 1–10 stimato dall'AI
  // Dati estratti
  nextSteps:       string[],           // Azioni concordate
  objections:      string[],           // Obiezioni sollevate
  competitorsMentioned: string[],      // Competitor citati
  budgetMentioned: boolean,
  timelineMentioned: boolean,
  // CRM updates automatici suggeriti dall'AI
  suggestedStage:  string | null,
  suggestedTasks:  Array<{
    title:    string,
    dueInDays: number,
    type:     string,
  }>,
  suggestedNotes:  string,             // Note da aggiungere alla scheda lead
  // Metadata
  modelUsed:       string,             // "gemini-1.5-pro"
  promptVersion:   string,
  createdAt:       Timestamp,
}
```

#### `blockchain_records/{recordId}` — APPEND-ONLY

```typescript
{
  // Record immutabile — MAI modificare o cancellare
  entityType:      "gdpr_consent" | "crm_activity" | "proposal_accepted" |
                   "deal_closed" | "api_access_log",
  entityId:        string,             // ID del documento notarizzato
  leadId:          string | null,
  // Hash e blockchain
  dataHash:        string,             // SHA-256 del contenuto
  transactionHash: string,             // Hash transazione blockchain
  blockNumber:     number,
  network:         "polygon" | "arbitrum",
  contractAddress: string,
  // Dati originali hashati (per verifica)
  dataSnapshot:    Record<string, unknown>,
  // SignSisure
  signsisureId:    string,             // ID univoco SignSisure
  signsisureUrl:   string,             // Link verifica pubblica
  notarizedAt:     Timestamp,
  createdAt:       Timestamp,
  // NO updatedAt — append-only per definizione
}
```

#### `ai_suggestions/{suggestionId}`

```typescript
{
  leadId:       string,
  userId:       string,                // Utente che ha richiesto il suggerimento
  type:         "email_draft" | "call_prep" | "objection_handler" | "proposal_summary",
  prompt:       string,                // Prompt usato
  suggestion:   string,                // Output dell'AI
  modelUsed:    string,
  tokensUsed:   number,
  wasUsed:      boolean,               // L'utente ha usato il suggerimento?
  feedback:     "positive" | "negative" | null,
  createdAt:    Timestamp,
}
```

#### `accounts/{accountId}` — Clienti attivi post-vendita

```typescript
{
  leadId:          string,             // Lead originale che ha acquistato
  dealId:          string,
  companyName:     string,
  products:        string[],           // ["zentratto", "signsisure"]
  planTier:        "starter" | "professional" | "enterprise",
  mrr:             number,             // Monthly Recurring Revenue (EUR)
  startDate:       Timestamp,
  renewalDate:     Timestamp,
  csOwnerId:       string,             // uid del Customer Success manager
  // Health score
  healthScore:     number,             // 0–100
  healthStatus:    "healthy" | "at_risk" | "churning",
  // Engagement
  lastLoginAt:     Timestamp | null,
  loginCount30d:   number,
  apiCallsCount30d: number,
  // NPS
  lastNpsScore:    number | null,       // 0–10
  lastNpsSentAt:   Timestamp | null,
  createdAt:       Timestamp,
  updatedAt:       Timestamp,
}
```

#### `api_keys/{keyId}`

```typescript
{
  name:            string,             // "Integrazione ERP Martini Legal"
  keyPrefix:       string,             // "ak_live_" — primissimi 8 char (non segreto)
  keyHash:         string,             // SHA-256 della chiave (mai la chiave in chiaro)
  ownerId:         string,             // uid utente CRM
  scopes:          string[],           // ["leads:read", "leads:write", "webhooks"]
  isActive:        boolean,
  rateLimit:       number,             // Req/minuto
  lastUsedAt:      Timestamp | null,
  usageCount:      number,
  expiresAt:       Timestamp | null,
  createdAt:       Timestamp,
  updatedAt:       Timestamp,
}
```

### BigQuery — schema tabelle

```sql
-- Dataset: aichain_crm_analytics (regione EU)

-- Snapshot giornaliero di tutti i lead (storico)
-- Popola da: Cloud Scheduler → Firestore → BigQuery
CREATE TABLE IF NOT EXISTS aichain_crm_analytics.leads_snapshot (
  snapshot_date   DATE NOT NULL,
  lead_id         STRING NOT NULL,
  email           STRING,
  company_name    STRING,
  company_size    STRING,
  industry        STRING,
  role_seniority  STRING,
  source          STRING,
  utm_campaign    STRING,
  status          STRING,
  pipeline_stage  STRING,
  lead_score      INT64,
  is_qualified    BOOL,
  assigned_to     STRING,
  created_at      TIMESTAMP,
  first_contact_at TIMESTAMP,
  days_to_qualify INT64,        -- Giorni da creazione a qualified
  days_to_demo    INT64,        -- Giorni da creazione a demo
  days_to_close   INT64         -- Giorni da creazione a won/lost
)
PARTITION BY snapshot_date
CLUSTER BY industry, source, status;

-- Storico movimenti pipeline
CREATE TABLE IF NOT EXISTS aichain_crm_analytics.pipeline_history (
  event_id        STRING NOT NULL,
  lead_id         STRING NOT NULL,
  from_stage      STRING,
  to_stage        STRING NOT NULL,
  changed_by      STRING,
  changed_at      TIMESTAMP NOT NULL,
  days_in_stage   INT64,
  lead_score_at_change INT64
)
PARTITION BY DATE(changed_at)
CLUSTER BY to_stage;

-- Performance email per sequenza
CREATE TABLE IF NOT EXISTS aichain_crm_analytics.email_performance (
  send_id         STRING NOT NULL,
  lead_id         STRING NOT NULL,
  sequence_id     STRING,
  template_id     STRING,
  sent_at         TIMESTAMP NOT NULL,
  opened_at       TIMESTAMP,
  clicked_at      TIMESTAMP,
  bounced_at      TIMESTAMP,
  industry        STRING,
  source          STRING,
  lead_score      INT64,
  time_to_open_min FLOAT64,     -- Minuti da invio ad apertura
  time_to_click_min FLOAT64
)
PARTITION BY DATE(sent_at)
CLUSTER BY sequence_id, industry;

-- Tutti gli eventi di attività (per ML e analytics)
CREATE TABLE IF NOT EXISTS aichain_crm_analytics.activity_events (
  event_id        STRING NOT NULL,
  lead_id         STRING NOT NULL,
  activity_type   STRING NOT NULL,
  occurred_at     TIMESTAMP NOT NULL,
  industry        STRING,
  source          STRING,
  company_size    STRING,
  lead_score_at_event INT64,
  pipeline_stage  STRING,
  metadata_json   STRING         -- JSON serializzato dei metadata
)
PARTITION BY DATE(occurred_at)
CLUSTER BY activity_type, industry;

-- Previsioni revenue (aggiornate ogni settimana)
CREATE TABLE IF NOT EXISTS aichain_crm_analytics.revenue_forecast (
  forecast_date   DATE NOT NULL,
  forecast_period STRING NOT NULL,   -- "2026-Q3", "2026-07"
  lower_bound     FLOAT64,           -- P10 (pessimistico)
  central         FLOAT64,           -- P50 (base)
  upper_bound     FLOAT64,           -- P90 (ottimistico)
  pipeline_value  FLOAT64,           -- Valore totale pipeline corrente
  open_deals      INT64,
  avg_deal_value  FLOAT64,
  model_version   STRING,
  generated_at    TIMESTAMP
)
PARTITION BY forecast_date;
```

---

## 5. ZenTratto RAG sul CRM

> **Il differenziatore assoluto di Fase 3.**
> Usi il tuo stesso prodotto internamente.
> Il tuo team può interrogare l'intero CRM in linguaggio naturale.

### Architettura RAG interna

```
Query utente                Vector store              Contesto + Risposta
─────────────              (Vertex AI               ──────────────────────
"Mostrami lead di    →     Matching Engine)    →     Gemini 1.5 Pro
 studi legali che           ↑                         con grounding
 hanno citato eIDAS"        │ embedding query          su dati CRM reali
                            │
                    Firestore → Embedding
                    (notes, activities,
                     email subjects,
                     call transcripts)
```

### Cosa viene indicizzato

```python
# I dati CRM vengono convertiti in embedding testuali e indicizzati
# Ogni "chunk" indicizzato ha: testo + metadati per filtri

INDEXABLE_SOURCES = [
    # Note sui lead
    "leads.notes",
    "leads.painPoints",
    # Attività (ultime 6 mesi)
    "leads.activities[type=note].body",
    "leads.activities[type=call].body",
    "leads.activities[type=email_received].body",
    # Trascrizioni call
    "call_recordings.transcript",
    "call_insights.summary",
    "call_insights.objections",
    # Oggetti email ricevute
    "conversations.messages[direction=inbound].body",
]
```

### `backend/app/services/rag_service.py`

```python
"""
ZenTratto RAG applicato al CRM AiChain.
Usa Vertex AI Matching Engine per vector search
e Gemini 1.5 Pro per generation con grounding.
"""
import vertexai
from vertexai.language_models import TextEmbeddingModel
from vertexai.preview.generative_models import GenerativeModel, Content, Part
from google.cloud.aiplatform.matching_engine import MatchingEngineIndexEndpoint
from app.firebase_admin import db
from app.config import settings
from typing import AsyncIterator

# Init Vertex AI — regione europe-west4 (unica con Gemini in EU)
vertexai.init(project=settings.FIREBASE_PROJECT_ID, location="europe-west4")

EMBEDDING_MODEL  = TextEmbeddingModel.from_pretrained("text-multilingual-embedding-002")
GEMINI_MODEL     = GenerativeModel("gemini-1.5-pro")
INDEX_ENDPOINT   = MatchingEngineIndexEndpoint(
    index_endpoint_name=settings.VERTEX_INDEX_ENDPOINT_ID,
)

# Prompt di sistema per il RAG CRM
CRM_SYSTEM_PROMPT = """Sei l'assistente AI del CRM di AiChain Solutions.
Rispondi SOLO usando le informazioni del contesto fornito (dati CRM reali).
Se l'informazione non è nel contesto, dillo esplicitamente — non inventare mai.
Formato: risposte concise, professionali, con elenchi puntati dove utile.
Lingua: italiano, tono business professionale.
Quando citi lead specifici, includi sempre nome, azienda e data ultima attività."""

async def embed_text(text: str) -> list[float]:
    """Genera embedding di un testo — usato sia per indicizzazione che per query"""
    embeddings = EMBEDDING_MODEL.get_embeddings([text])
    return embeddings[0].values

async def query_crm(
    question: str,
    user_uid: str,
    top_k: int = 8,
    filter_industry: str = None,
    filter_status: str = None,
) -> AsyncIterator[str]:
    """
    Query RAG sul CRM: embedding → vector search → Gemini con contesto.
    Restituisce un AsyncIterator per lo streaming della risposta.

    Args:
        question:        Domanda in linguaggio naturale
        user_uid:        uid utente — per audit e personalizzazione
        top_k:           Numero di chunk da recuperare
        filter_industry: Filtra per settore
        filter_status:   Filtra per stato pipeline
    """
    # 1. Embedding della query
    query_embedding = await embed_text(question)

    # 2. Vector search su Matching Engine
    # I restricts sono filtri metadata (industria, stato, ecc.)
    restricts = []
    if filter_industry:
        restricts.append({
            "namespace": "industry",
            "allow_list": [filter_industry],
        })
    if filter_status:
        restricts.append({
            "namespace": "status",
            "allow_list": [filter_status],
        })

    response = INDEX_ENDPOINT.find_neighbors(
        deployed_index_id=settings.VERTEX_DEPLOYED_INDEX_ID,
        queries=[query_embedding],
        num_neighbors=top_k,
        restricts=restricts if restricts else None,
    )

    neighbors = response[0] if response else []

    # 3. Recupera testi originali da Firestore per ogni neighbor
    context_chunks = []
    lead_ids_seen   = set()

    for neighbor in neighbors:
        # L'ID del neighbor codifica il tipo e l'ID del documento
        # Formato: "{type}_{leadId}_{chunkId}"
        chunk_id   = neighbor.id
        chunk_data = await _fetch_chunk(chunk_id)

        if chunk_data:
            context_chunks.append(chunk_data)
            lead_ids_seen.add(chunk_data.get("lead_id", ""))

    if not context_chunks:
        yield "Non ho trovato dati rilevanti nel CRM per questa domanda."
        return

    # 4. Costruisci contesto per Gemini
    context_text = _format_context(context_chunks)

    # 5. Genera risposta in streaming con Gemini
    prompt = f"""
CONTESTO DAL CRM (dati reali — {len(context_chunks)} risultati da {len(lead_ids_seen)} lead):

{context_text}

---
DOMANDA: {question}

Rispondi basandoti ESCLUSIVAMENTE sul contesto sopra.
"""
    contents = [
        Content(role="user", parts=[Part.from_text(prompt)])
    ]

    stream = GEMINI_MODEL.generate_content_async(
        contents=contents,
        system_instruction=CRM_SYSTEM_PROMPT,
        stream=True,
        generation_config={
            "temperature":     0.2,   # Bassa temperatura = risposte più precise
            "max_output_tokens": 1024,
        }
    )

    async for chunk in await stream:
        if chunk.text:
            yield chunk.text

    # 6. Logga la query per audit e miglioramento continuo
    await _log_rag_query(question, user_uid, len(context_chunks), lead_ids_seen)

def _format_context(chunks: list[dict]) -> str:
    """Formatta i chunk per il prompt Gemini"""
    sections = []
    for chunk in chunks:
        lead_name = f"{chunk.get('first_name', '')} {chunk.get('last_name', '')}".strip()
        company   = chunk.get("company_name", "—")
        industry  = chunk.get("industry", "")
        date      = chunk.get("date", "")
        text      = chunk.get("text", "")

        sections.append(
            f"[{chunk['type'].upper()} | {lead_name} ({company}, {industry}) | {date}]\n{text}"
        )
    return "\n\n".join(sections)

async def _fetch_chunk(chunk_id: str) -> dict | None:
    """Recupera il testo di un chunk dal Firestore dato il suo ID"""
    parts  = chunk_id.split("_", 2)
    if len(parts) < 2:
        return None
    chunk_type, lead_id = parts[0], parts[1]

    if chunk_type == "note":
        lead = await db.collection("leads").document(lead_id).get()
        if lead.exists:
            data = lead.to_dict()
            return {
                "type":         "nota lead",
                "lead_id":      lead_id,
                "first_name":   data.get("firstName"),
                "last_name":    data.get("lastName"),
                "company_name": data.get("companyName"),
                "industry":     data.get("industry"),
                "date":         str(data.get("updatedAt", "")),
                "text":         data.get("notes", ""),
            }

    elif chunk_type == "activity":
        activity_id = parts[2] if len(parts) > 2 else ""
        act = await db.collection("leads").document(lead_id)\
            .collection("activities").document(activity_id).get()
        if act.exists:
            lead = await db.collection("leads").document(lead_id).get()
            lead_data = lead.to_dict() if lead.exists else {}
            act_data  = act.to_dict()
            return {
                "type":         f"attività {act_data.get('type', '')}",
                "lead_id":      lead_id,
                "first_name":   lead_data.get("firstName"),
                "last_name":    lead_data.get("lastName"),
                "company_name": lead_data.get("companyName"),
                "industry":     lead_data.get("industry"),
                "date":         str(act_data.get("createdAt", "")),
                "text":         act_data.get("body") or act_data.get("title", ""),
            }

    elif chunk_type == "transcript":
        call = await db.collection("call_recordings").document(lead_id).get()
        if call.exists:
            call_data = call.to_dict()
            lead = await db.collection("leads").document(call_data.get("leadId", "")).get()
            lead_data = lead.to_dict() if lead.exists else {}
            return {
                "type":         "trascrizione call",
                "lead_id":      call_data.get("leadId", ""),
                "first_name":   lead_data.get("firstName"),
                "last_name":    lead_data.get("lastName"),
                "company_name": lead_data.get("companyName"),
                "industry":     lead_data.get("industry"),
                "date":         str(call_data.get("createdAt", "")),
                "text":         (call_data.get("transcript", "") or "")[:2000],
            }
    return None

async def index_lead_data(lead_id: str):
    """
    Indicizza tutti i dati testuali di un lead nel Matching Engine.
    Chiamato da Cloud Task ogni volta che note o attività vengono aggiornate.
    """
    lead_snap = await db.collection("leads").document(lead_id).get()
    if not lead_snap.exists:
        return
    lead = lead_snap.to_dict()

    datapoints = []

    # Indicizza note
    if lead.get("notes"):
        emb = await embed_text(lead["notes"])
        datapoints.append({
            "id":         f"note_{lead_id}",
            "embedding":  emb,
            "restricts":  [
                {"namespace": "industry", "allow_list": [lead.get("industry", "other")]},
                {"namespace": "status",   "allow_list": [lead.get("status", "new")]},
                {"namespace": "type",     "allow_list": ["note"]},
            ],
        })

    # Indicizza attività con testo
    activities = await db.collection("leads").document(lead_id)\
        .collection("activities")\
        .where("type", "in", ["note", "call", "email_received"])\
        .limit(50).get()

    for act in activities:
        act_data = act.to_dict()
        text     = act_data.get("body") or act_data.get("title", "")
        if text and len(text) > 20:
            emb = await embed_text(text[:2000])
            datapoints.append({
                "id":        f"activity_{lead_id}_{act.id}",
                "embedding": emb,
                "restricts": [
                    {"namespace": "industry", "allow_list": [lead.get("industry", "other")]},
                    {"namespace": "status",   "allow_list": [lead.get("status", "new")]},
                    {"namespace": "type",     "allow_list": ["activity"]},
                ],
            })

    if datapoints:
        # Upsert batch nel Matching Engine
        INDEX_ENDPOINT.upsert_datapoints(datapoints=datapoints)
```

### `backend/app/routers/ai.py`

```python
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from app.deps import require_sales
from app.services.rag_service import query_crm
from app.services.gemini_service import generate_email_draft, generate_call_prep
from app.models.user import UserRecord
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

class CrmQueryRequest(BaseModel):
    question:        str
    filter_industry: Optional[str] = None
    filter_status:   Optional[str] = None

class EmailDraftRequest(BaseModel):
    lead_id:    str
    email_type: str   # "followup" | "intro" | "proposal" | "reengagement"
    context:    Optional[str] = None  # Note aggiuntive del sales

@router.post("/query")
async def query_crm_endpoint(
    request: CrmQueryRequest,
    user: UserRecord = Depends(require_sales),
):
    """
    Chat RAG sul CRM — risposta in streaming.
    Esempio: "Mostrami tutti i lead legali che hanno menzionato compliance"
    """
    async def stream():
        async for chunk in query_crm(
            question=request.question,
            user_uid=user.uid,
            filter_industry=request.filter_industry,
            filter_status=request.filter_status,
        ):
            yield f"data: {chunk}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream")

@router.post("/email-draft")
async def generate_email(
    request: EmailDraftRequest,
    user: UserRecord = Depends(require_sales),
):
    """
    Genera bozza email personalizzata sul lead.
    Il sales ritocca e invia — non parte in automatico.
    """
    draft = await generate_email_draft(
        lead_id=request.lead_id,
        email_type=request.email_type,
        context=request.context,
        db=__import__('app.firebase_admin', fromlist=['db']).db,
    )
    return {"draft": draft}

@router.post("/call-prep/{lead_id}")
async def generate_call_preparation(
    lead_id: str,
    user: UserRecord = Depends(require_sales),
):
    """
    Genera briefing pre-call: storia lead, argomenti suggeriti, obiezioni attese.
    """
    briefing = await generate_call_prep(lead_id=lead_id)
    return {"briefing": briefing}
```

---

## 6. AI Email Writer — Gemini

### `backend/app/services/gemini_service.py`

```python
"""
Wrapper Vertex AI Gemini per tutte le funzionalità AI del CRM.
Ogni funzione ha il suo prompt ottimizzato.
"""
import vertexai
from vertexai.preview.generative_models import GenerativeModel
from app.firebase_admin import db
from app.config import settings

vertexai.init(project=settings.FIREBASE_PROJECT_ID, location="europe-west4")
model = GenerativeModel("gemini-1.5-pro")

EMAIL_WRITER_PROMPTS = {
    "followup": """Sei un consulente B2B esperto in legal tech.
Scrivi una email di follow-up professionale per {fullName} di {companyName}.

PROFILO LEAD:
- Settore: {industry}
- Dimensione azienda: {companySize}
- Ruolo: {roleTitle}
- Fonte: {source}
- Problemi dichiarati: {painPoints}
- Ultima interazione: {lastActivity}
- Score lead: {leadScore}/100

CONTESTO AGGIUNTIVO: {context}

REGOLE:
- Max 150 parole
- Tono: professionale ma umano — non robotico
- Personalizza con dati specifici del lead
- CTA chiara e a bassa frizione (es: "15 minuti questa settimana?")
- NON usare frasi cliché ("spero che tu stia bene", "come stai")
- Inizia con qualcosa di specifico del loro contesto
- Firma: "[Il tuo nome] · AiChain Solutions"

Scrivi SOLO il corpo dell'email (non includere oggetto o intestazione).""",

    "intro": """Scrivi una email di primo contatto B2B per {fullName} di {companyName}.

PROFILO:
- Settore: {industry} | Dimensione: {companySize} | Ruolo: {roleTitle}
- Fonte: {source} (usala per la personalizzazione)
- Score attuale: {leadScore}/100

REGOLE:
- Max 120 parole
- Inizia con un insight specifico del loro settore ({industry})
- Mostra che hai fatto ricerca — non è un'email di massa
- Il CTA è SOLO: "Vale la pena di un confronto di 15 min?"
- Nessun link, nessun allegato nel primo contatto""",

    "reengagement": """Scrivi una email per riattivare {fullName} di {companyName}
che non risponde da {daysSinceLastActivity} giorni.

STORICO: {lastActivity}

REGOLE:
- Max 80 parole — brevità è fondamentale per il reengagement
- Inizia con qualcosa di nuovo (un dato di settore, un caso studio recente)
- Nessuna menzione al fatto che non ha risposto
- CTA: domanda diretta con alternativa binaria ("Preferisci una call o una demo registrata?")
- Se non risponde a questa → cambia stato a cold""",

    "proposal": """Scrivi una email di accompagnamento al preventivo per {fullName}.

OFFERTA: {proposalTitle} — €{proposalTotal}
VALIDITÀ: {proposalValidUntil}

REGOLE:
- Max 100 parole
- Elenca 3 benefici chiave dell'offerta (non le feature — i risultati)
- Menziona la validità senza pressione eccessiva
- CTA: "Hai domande? Sono disponibile per una call di 20 min"
- Tono: consulenziale, non venditore"""
}

async def generate_email_draft(
    lead_id: str,
    email_type: str,
    context: str,
    db,
) -> str:
    """Genera bozza email personalizzata con Gemini"""
    lead_snap = await db.collection("leads").document(lead_id).get()
    if not lead_snap.exists:
        raise ValueError(f"Lead {lead_id} non trovato")
    lead = lead_snap.to_dict()

    # Recupera ultima attività per contesto
    activities = await db.collection("leads").document(lead_id)\
        .collection("activities")\
        .order_by("createdAt", direction="DESCENDING")\
        .limit(3).get()

    last_activity_summary = "; ".join([
        a.to_dict().get("title", "") for a in activities
    ]) or "Nessuna attività recente"

    prompt_template = EMAIL_WRITER_PROMPTS.get(email_type, EMAIL_WRITER_PROMPTS["followup"])
    prompt = prompt_template.format(
        fullName=f"{lead.get('firstName', '')} {lead.get('lastName', '')}".strip(),
        companyName=lead.get("companyName", "la loro azienda"),
        industry=lead.get("industry", "non specificato"),
        companySize=lead.get("companySize", "non specificata"),
        roleTitle=lead.get("roleTitle", "non specificato"),
        source=lead.get("source", "non specificata"),
        painPoints=", ".join(lead.get("painPoints", []) or []) or "non specificati",
        lastActivity=last_activity_summary,
        leadScore=lead.get("leadScore", 0),
        context=context or "Nessun contesto aggiuntivo",
        daysSinceLastActivity=_days_since(lead.get("lastActivityAt")),
        proposalTitle=context or "Proposta personalizzata",
        proposalTotal="—",
        proposalValidUntil="—",
    )

    response = model.generate_content(
        prompt,
        generation_config={
            "temperature":     0.7,
            "max_output_tokens": 400,
        }
    )

    # Salva il suggerimento per analytics e feedback
    await db.collection("ai_suggestions").add({
        "leadId":     lead_id,
        "userId":     "system",
        "type":       "email_draft",
        "prompt":     prompt[:500],
        "suggestion": response.text,
        "modelUsed":  "gemini-1.5-pro",
        "tokensUsed": response.usage_metadata.total_token_count if response.usage_metadata else 0,
        "wasUsed":    False,
        "feedback":   None,
        "createdAt":  __import__('app.services.firestore_service', fromlist=['utcnow']).utcnow(),
    })

    return response.text

async def generate_call_prep(lead_id: str) -> str:
    """Genera briefing pre-call: storia, argomenti suggeriti, obiezioni attese"""
    from app.firebase_admin import db as firebase_db
    lead_snap = await firebase_db.collection("leads").document(lead_id).get()
    lead      = lead_snap.to_dict() if lead_snap.exists else {}

    activities = await firebase_db.collection("leads").document(lead_id)\
        .collection("activities")\
        .order_by("createdAt", direction="DESCENDING")\
        .limit(10).get()

    activity_text = "\n".join([
        f"- [{a.to_dict().get('type')}] {a.to_dict().get('title', '')}"
        for a in activities
    ])

    prompt = f"""Sei un coach di vendita B2B per AiChain Solutions (AI + Blockchain per documenti legali).
Preparami un briefing pre-call per: {lead.get('firstName')} {lead.get('lastName')}
Azienda: {lead.get('companyName')} ({lead.get('industry')}, {lead.get('companySize')} dipendenti)
Ruolo: {lead.get('roleTitle')} | Score: {lead.get('leadScore', 0)}/100
Fonte: {lead.get('source')} | Stato: {lead.get('status')}
Problemi dichiarati: {', '.join(lead.get('painPoints', []) or [])}

STORICO INTERAZIONI:
{activity_text or 'Nessuna interazione precedente'}

Genera un briefing strutturato con:
1. **Contesto in 3 righe** — cosa sai di loro
2. **Obiettivo della call** — cosa vuoi ottenere
3. **3 domande aperte** da porre per qualificare meglio
4. **Obiezioni probabili** (2-3) e come risponderle
5. **Next step suggerito** al termine della call

Tono: diretto e pratico — è un briefing operativo, non una presentazione."""

    response = model.generate_content(prompt, generation_config={"temperature": 0.3})
    return response.text

def _days_since(timestamp) -> int:
    if not timestamp:
        return 999
    from datetime import datetime, timezone
    ts = timestamp.replace(tzinfo=timezone.utc) if timestamp.tzinfo is None else timestamp
    return (datetime.now(timezone.utc) - ts).days
```

---

## 7. Trascrizione e analisi call

### `backend/app/services/speech_service.py`

```python
"""
Cloud Speech-to-Text v2 per trascrizione call.
Supporta: italiano (it-IT), inglese (en-US), audio da Google Meet / Zoom.
"""
from google.cloud.speech_v2 import SpeechClient, types as speech_types
from google.cloud import storage as gcs
from app.config import settings

speech_client = SpeechClient()
RECOGNIZER    = f"projects/{settings.FIREBASE_PROJECT_ID}/locations/europe-west1/recognizers/_"

async def transcribe_call_audio(
    gcs_uri: str,           # gs://bucket/calls/{callId}/audio.mp3
    language: str = "it-IT",
    num_speakers: int = 2,
) -> dict:
    """
    Trascrive audio da GCS con diarization (distingue i parlatori).
    Ritorna trascrizione completa + word-level timing.
    """
    config = speech_types.RecognitionConfig(
        auto_decoding_config=speech_types.AutoDetectDecodingConfig(),
        language_codes=[language],
        model="chirp",                  # Modello più accurato per business
        features=speech_types.RecognitionFeatures(
            enable_word_time_offsets=True,
            enable_word_confidence=True,
            diarization_config=speech_types.SpeakerDiarizationConfig(
                min_speaker_count=num_speakers,
                max_speaker_count=num_speakers,
            ),
            enable_automatic_punctuation=True,
        ),
    )

    request = speech_types.BatchRecognizeRequest(
        recognizer=RECOGNIZER,
        config=config,
        files=[speech_types.BatchRecognizeFileMetadata(uri=gcs_uri)],
        recognition_output_config=speech_types.RecognitionOutputConfig(
            inline_response_config=speech_types.InlineOutputConfig(),
        ),
    )

    operation = speech_client.batch_recognize(request=request)
    result    = operation.result(timeout=600)   # Max 10 minuti per call lunghe

    # Processa risultato
    transcript_text  = ""
    words_with_timing = []

    for file_result in result.results.values():
        for res in file_result.transcript.results:
            if not res.alternatives:
                continue
            best = res.alternatives[0]
            transcript_text += best.transcript + " "

            for word_info in best.words:
                words_with_timing.append({
                    "word":       word_info.word,
                    "startTime":  word_info.start_offset.total_seconds(),
                    "endTime":    word_info.end_offset.total_seconds(),
                    "confidence": word_info.confidence,
                    "speaker":    word_info.speaker_label,  # "1" o "2"
                })

    return {
        "transcript":      transcript_text.strip(),
        "transcriptWords": words_with_timing,
    }
```

### `backend/app/services/call_analysis_service.py`

```python
"""
Analisi LLM post-trascrizione.
Estrae: riassunto, sentiment, next steps, obiezioni, competitor, score interesse.
"""
import vertexai
from vertexai.preview.generative_models import GenerativeModel
from app.firebase_admin import db
from app.services.firestore_service import create_document, update_document, utcnow

vertexai.init(project=__import__('app.config', fromlist=['settings']).settings.FIREBASE_PROJECT_ID,
              location="europe-west4")
model = GenerativeModel("gemini-1.5-pro")

ANALYSIS_PROMPT = """Analizza la seguente trascrizione di una call di vendita B2B
(prodotto: ZenTratto — AI per gestione documenti legali/finanziari).

TRASCRIZIONE:
{transcript}

Rispondi ESCLUSIVAMENTE in JSON con questa struttura esatta:
{{
  "summary": "Riassunto in 3-4 frasi complete",
  "sentiment": "positive|neutral|negative",
  "interestLevel": 7,
  "nextSteps": ["Azione 1 concordata", "Azione 2 concordata"],
  "objections": ["Obiezione sollevata 1", "Obiezione 2"],
  "competitorsMentioned": ["Nome competitor se citato"],
  "budgetMentioned": true,
  "timelineMentioned": false,
  "suggestedStage": "qualified|demo_scheduled|proposal_sent|null",
  "suggestedTasks": [
    {{"title": "Inviare case study legale", "dueInDays": 2, "type": "email"}},
    {{"title": "Richiamare per feedback", "dueInDays": 5, "type": "call"}}
  ],
  "suggestedNotes": "Note concise da aggiungere alla scheda lead (2-3 righe max)"
}}

SOLO JSON valido — nessun testo prima o dopo."""

async def analyze_call(call_id: str, lead_id: str) -> dict:
    """
    Analizza trascrizione call con Gemini e aggiorna il CRM.
    Chiamato da Cloud Task dopo completamento trascrizione.
    """
    call_snap = await db.collection("call_recordings").document(call_id).get()
    if not call_snap.exists:
        raise ValueError(f"Call {call_id} non trovata")

    call      = call_snap.to_dict()
    transcript = call.get("transcript", "")

    if not transcript or len(transcript) < 100:
        return {"error": "Trascrizione troppo breve per l'analisi"}

    prompt   = ANALYSIS_PROMPT.format(transcript=transcript[:12000])
    response = model.generate_content(
        prompt,
        generation_config={"temperature": 0.1, "max_output_tokens": 1024}
    )

    import json
    try:
        # Rimuovi eventuali backtick markdown
        raw   = response.text.strip().strip("```json").strip("```").strip()
        insights = json.loads(raw)
    except json.JSONDecodeError:
        insights = {"summary": response.text, "error": "parsing_failed"}

    # Salva insights
    await create_document(db, "call_insights", insights | {
        "callId":      call_id,
        "leadId":      lead_id,
        "modelUsed":   "gemini-1.5-pro",
        "promptVersion": "1.0",
        "createdAt":   utcnow(),
    }, doc_id=call_id)

    # Aggiorna stato call
    await update_document(db, "call_recordings", call_id, {
        "status":     "analyzed",
        "analyzedAt": utcnow(),
    })

    # Applica suggerimenti AI al lead (se affidabili)
    await _apply_insights_to_lead(lead_id, insights)

    return insights

async def _apply_insights_to_lead(lead_id: str, insights: dict):
    """Applica automaticamente i suggerimenti dell'AI al lead"""
    from app.services.firestore_service import append_activity

    # Aggiungi note suggerite
    if insights.get("suggestedNotes"):
        await append_activity(db, lead_id, {
            "type":  "note",
            "title": "Note automatiche post-call (AI)",
            "body":  insights["suggestedNotes"],
            "metadata": {
                "sentiment":    insights.get("sentiment"),
                "interestLevel": insights.get("interestLevel"),
                "aiGenerated":  True,
            }
        })

    # Crea task suggeriti
    from datetime import timedelta
    for task_suggestion in (insights.get("suggestedTasks") or []):
        from app.services.firestore_service import utcnow as _now, new_id
        due = _now() + timedelta(days=task_suggestion.get("dueInDays", 3))
        lead = await db.collection("leads").document(lead_id).get()
        lead_data = lead.to_dict() if lead.exists else {}

        await db.collection("leads").document(lead_id)\
            .collection("tasks").document(new_id()).set({
            "leadId":      lead_id,
            "assignedTo":  lead_data.get("assignedTo", ""),
            "createdBy":   "system_ai",
            "title":       task_suggestion["title"],
            "type":        task_suggestion.get("type", "followup"),
            "priority":    "medium",
            "dueDate":     due,
            "completedAt": None,
            "aiGenerated": True,
            "createdAt":   _now(),
            "updatedAt":   _now(),
            "deletedAt":   None,
        })
```

---

## 8. Lead scoring predittivo — Vertex AI

### `backend/app/services/scoring_service.py` — v3

```python
"""
Scoring Engine v3 — Fase 3
Aggiunge: modello ML BigQuery su dati storici di conversione.
Il modello impara dai pattern dei lead che hanno convertito in passato.
"""
from google.cloud import bigquery
from app.config import settings

bq_client = bigquery.Client(project=settings.FIREBASE_PROJECT_ID)

# ── BigQuery ML model (addestrato sui dati storici) ──────────────
# Creato una volta sola con questa query in BigQuery:
CREATE_ML_MODEL_SQL = """
CREATE OR REPLACE MODEL `aichain_crm_analytics.lead_conversion_model`
OPTIONS (
  model_type = 'LOGISTIC_REG',
  input_label_cols = ['converted'],
  data_split_method = 'AUTO_SPLIT',
  auto_class_weights = TRUE
) AS
SELECT
  -- Feature demografiche
  industry,
  company_size,
  role_seniority,
  source,
  -- Feature comportamentali (da activity_events)
  COUNT(CASE WHEN activity_type = 'email_opened'  THEN 1 END) AS emails_opened,
  COUNT(CASE WHEN activity_type = 'email_clicked' THEN 1 END) AS emails_clicked,
  COUNT(CASE WHEN activity_type = 'page_visited'  THEN 1 END) AS pages_visited,
  COUNT(CASE WHEN activity_type = 'booking_created' THEN 1 END) AS bookings,
  COUNT(CASE WHEN activity_type = 'assessment'    THEN 1 END) AS assessments,
  -- Timing
  IFNULL(days_to_qualify, 999) AS days_to_qualify,
  -- Label
  CASE WHEN status = 'won' THEN 1 ELSE 0 END AS converted
FROM `aichain_crm_analytics.leads_snapshot` AS ls
LEFT JOIN `aichain_crm_analytics.activity_events` AS ae
  USING (lead_id)
WHERE snapshot_date = (
  SELECT MAX(snapshot_date) FROM `aichain_crm_analytics.leads_snapshot`
)
GROUP BY 1,2,3,4,5,12,13
"""

async def get_ml_conversion_probability(lead_id: str) -> dict:
    """
    Chiede al modello BigQuery ML la probabilità di conversione del lead.
    Ritorna: { probability: 0.0–1.0, features_importance: {...}, top_factors: [...] }
    """
    # Prima recupera i dati del lead per la predizione
    query = f"""
    SELECT
      predicted_converted_probs[OFFSET(1)].prob AS conversion_probability,
      predicted_converted_probs
    FROM ML.PREDICT(
      MODEL `aichain_crm_analytics.lead_conversion_model`,
      (
        SELECT
          ls.industry,
          ls.company_size,
          ls.role_seniority,
          ls.source,
          COUNT(CASE WHEN ae.activity_type = 'email_opened'   THEN 1 END) AS emails_opened,
          COUNT(CASE WHEN ae.activity_type = 'email_clicked'  THEN 1 END) AS emails_clicked,
          COUNT(CASE WHEN ae.activity_type = 'page_visited'   THEN 1 END) AS pages_visited,
          COUNT(CASE WHEN ae.activity_type = 'booking_created' THEN 1 END) AS bookings,
          COUNT(CASE WHEN ae.activity_type = 'assessment'     THEN 1 END) AS assessments,
          IFNULL(ls.days_to_qualify, 999) AS days_to_qualify
        FROM `aichain_crm_analytics.leads_snapshot` AS ls
        LEFT JOIN `aichain_crm_analytics.activity_events` AS ae
          ON ls.lead_id = ae.lead_id
        WHERE ls.lead_id = '{lead_id}'
          AND ls.snapshot_date = (
            SELECT MAX(snapshot_date)
            FROM `aichain_crm_analytics.leads_snapshot`
          )
        GROUP BY 1,2,3,4,10
      )
    )
    """
    rows = list(bq_client.query(query).result())
    if not rows:
        return {"probability": None, "error": "Dati insufficienti per predizione ML"}

    prob = float(rows[0]["conversion_probability"])

    # Determina fattori chiave (rule-based su probabilità alta/bassa)
    top_factors = _explain_prediction(prob, rows[0])

    return {
        "probability":      prob,
        "probability_pct":  f"{prob * 100:.0f}%",
        "confidence_level": "alta" if prob > 0.7 else "media" if prob > 0.4 else "bassa",
        "top_factors":      top_factors,
        "model_version":    "bigquery_logistic_v1",
    }

def _explain_prediction(prob: float, row) -> list[str]:
    """Genera spiegazione human-readable dei fattori principali"""
    factors = []
    if row.get("bookings", 0) > 0:
        factors.append("Ha prenotato una call (+)")
    if row.get("assessments", 0) > 0:
        factors.append("Ha completato l'assessment (+)")
    if row.get("emails_clicked", 0) > 2:
        factors.append(f"Alto engagement email: {row['emails_clicked']} click (+)")
    if row.get("industry") in ("legal", "finance"):
        factors.append(f"Settore target: {row['industry']} (+)")
    if row.get("days_to_qualify", 999) < 30:
        factors.append("Qualificato rapidamente (+)")
    return factors[:4]   # Max 4 fattori
```

---

## 9. Blockchain audit trail — SignSisure

### `backend/app/services/signsisure_service.py`

```python
"""
Integrazione SignSisure per notarizzazione blockchain.
Usa il nostro stesso prodotto internamente per:
1. Notarizzare i consensi GDPR
2. Certificare gli audit trail CRM critici
3. Ancorare le offerte accettate su blockchain

API SignSisure (interna AiChain):
POST /api/notarize   → { hash, tx_hash, block, network, signsisure_id, verify_url }
GET  /api/verify/:id → verifica pubblica senza auth
"""
import httpx
import hashlib
import json
from datetime import datetime, timezone
from app.config import settings
from app.firebase_admin import db
from app.services.firestore_service import create_document, utcnow, new_id
from app.services.pubsub_service import publish_event

SIGNSISURE_API = settings.SIGNSISURE_API_URL   # URL interno microservizio
SIGNSISURE_KEY = settings.SIGNSISURE_API_KEY

async def notarize(
    entity_type: str,
    entity_id: str,
    data: dict,
    lead_id: str = None,
) -> dict:
    """
    Notarizza un documento su blockchain tramite SignSisure.
    1. Calcola SHA-256 del dato
    2. Chiama SignSisure API per l'ancoraggio
    3. Salva il record in Firestore blockchain_records (append-only)
    4. Emette evento Pub/Sub per audit

    Args:
        entity_type: tipo di entità ("gdpr_consent", "deal_closed", ecc.)
        entity_id:   ID del documento da notarizzare
        data:        Contenuto da hashare (deve essere deterministic JSON)
        lead_id:     Lead associato (per ricerca)
    """
    # 1. Hash deterministico (chiavi ordinate = stesso hash per stesso contenuto)
    canonical = json.dumps(data, sort_keys=True, default=str, ensure_ascii=False)
    data_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    # 2. Chiama SignSisure API
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            f"{SIGNSISURE_API}/api/notarize",
            headers={
                "Authorization": f"Bearer {SIGNSISURE_KEY}",
                "Content-Type":  "application/json",
                "X-Source":      "aichain-crm-internal",
            },
            json={
                "hash":        data_hash,
                "entity_type": entity_type,
                "entity_id":   entity_id,
                "metadata": {
                    "system":   "aichain_crm",
                    "version":  "3.0",
                    "lead_id":  lead_id,
                }
            }
        )
        response.raise_for_status()
        signsisure_response = response.json()

    # 3. Salva record immutabile in Firestore
    record = await create_document(db, "blockchain_records", {
        "entityType":      entity_type,
        "entityId":        entity_id,
        "leadId":          lead_id,
        "dataHash":        data_hash,
        "transactionHash": signsisure_response["tx_hash"],
        "blockNumber":     signsisure_response["block"],
        "network":         signsisure_response.get("network", "polygon"),
        "contractAddress": signsisure_response.get("contract_address", ""),
        "dataSnapshot":    data,           # Copia del dato notarizzato
        "signsisureId":    signsisure_response["signsisure_id"],
        "signsisureUrl":   signsisure_response["verify_url"],
        "notarizedAt":     utcnow(),
        # NO updatedAt — questo documento non cambia mai
    })

    # 4. Aggiorna il documento originale con il riferimento blockchain
    if entity_type == "gdpr_consent":
        await db.collection("gdpr_consents").document(entity_id).update({
            "blockchainRecordId": record["id"],
            "signsisureUrl":      signsisure_response["verify_url"],
        })
    elif entity_type == "deal_closed":
        await db.collection("deals").document(entity_id).update({
            "blockchainRecordId": record["id"],
            "signsisureUrl":      signsisure_response["verify_url"],
        })

    # 5. Pub/Sub evento per audit
    await publish_event("crm.blockchain.events", "blockchain.notarized", {
        "record_id":   record["id"],
        "entity_type": entity_type,
        "entity_id":   entity_id,
        "data_hash":   data_hash,
        "tx_hash":     signsisure_response["tx_hash"],
    })

    return record

# ── Trigger automatici di notarizzazione ─────────────────────────

async def notarize_gdpr_consent(consent_id: str):
    """Notarizza consenso GDPR su blockchain — chiamato da blockchain_worker"""
    consent_snap = await db.collection("gdpr_consents").document(consent_id).get()
    if not consent_snap.exists:
        return
    consent = consent_snap.to_dict()
    await notarize(
        entity_type="gdpr_consent",
        entity_id=consent_id,
        data={
            "lead_id":       consent["leadId"],
            "action":        consent["action"],
            "consent_text":  consent["consentText"],
            "policy_version": consent["policyVersion"],
            "ip_address":    consent.get("ipAddress"),
            "created_at":    str(consent["createdAt"]),
        },
        lead_id=consent["leadId"],
    )

async def notarize_deal_closed(deal_id: str):
    """Notarizza accordo commerciale su blockchain quando deal → won"""
    deal_snap = await db.collection("deals").document(deal_id).get()
    if not deal_snap.exists:
        return
    deal = deal_snap.to_dict()
    await notarize(
        entity_type="deal_closed",
        entity_id=deal_id,
        data={
            "deal_id":     deal_id,
            "lead_id":     deal["leadId"],
            "product":     deal.get("product"),
            "value":       deal.get("value"),
            "closed_at":   str(deal.get("closedAt")),
        },
        lead_id=deal.get("leadId"),
    )

async def notarize_critical_activity(activity_id: str, lead_id: str):
    """
    Notarizza attività critiche: cambio stage, accesso dati sensibili.
    Usato per compliance ISO 27001.
    """
    act_snap = await db.collection("leads").document(lead_id)\
        .collection("activities").document(activity_id).get()
    if not act_snap.exists:
        return
    act = act_snap.to_dict()
    if act.get("type") not in ("stage_changed", "proposal_sent", "gdpr_export"):
        return  # Notarizza solo attività critiche
    await notarize(
        entity_type="crm_activity",
        entity_id=activity_id,
        data={
            "activity_id": activity_id,
            "lead_id":     lead_id,
            "type":        act["type"],
            "user_id":     act.get("userId"),
            "metadata":    act.get("metadata", {}),
            "created_at":  str(act["createdAt"]),
        },
        lead_id=lead_id,
    )
```

---

## 10. BigQuery analytics pipeline

### `backend/app/services/bigquery_service.py`

```python
"""
Sync Firestore → BigQuery per analytics avanzate.
Due modalità:
1. Streaming insert (real-time, per eventi ad alto valore)
2. Batch nightly (snapshot completo, per ML e reporting)
"""
from google.cloud import bigquery
from app.config import settings
from app.firebase_admin import db
from app.services.firestore_service import utcnow
import asyncio

bq = bigquery.Client(project=settings.FIREBASE_PROJECT_ID)
DATASET = f"{settings.FIREBASE_PROJECT_ID}.aichain_crm_analytics"

async def stream_activity_event(activity_data: dict, lead_data: dict):
    """
    Insert streaming real-time in BigQuery per ogni nuova activity.
    Latenza: < 1 secondo — disponibile nelle query entro secondi.
    """
    row = {
        "event_id":          f"{activity_data['leadId']}_{activity_data.get('id', '')}",
        "lead_id":           activity_data["leadId"],
        "activity_type":     activity_data["type"],
        "occurred_at":       activity_data["createdAt"].isoformat()
                             if hasattr(activity_data["createdAt"], "isoformat")
                             else str(activity_data["createdAt"]),
        "industry":          lead_data.get("industry"),
        "source":            lead_data.get("source"),
        "company_size":      lead_data.get("companySize"),
        "lead_score_at_event": lead_data.get("leadScore", 0),
        "pipeline_stage":    lead_data.get("pipelineStage"),
        "metadata_json":     __import__('json').dumps(
                                 activity_data.get("metadata", {}), default=str
                             ),
    }
    errors = bq.insert_rows_json(f"{DATASET}.activity_events", [row])
    if errors:
        import logging
        logging.error(f"BigQuery streaming insert error: {errors}")

async def nightly_leads_snapshot():
    """
    Snapshot giornaliero di tutti i lead in BigQuery.
    Chiamato da Cloud Scheduler ogni notte alle 01:00.
    Usato per: ML training, storico conversioni, dashboard trend.
    """
    today       = utcnow().date().isoformat()
    all_leads   = await db.collection("leads")\
        .where("deletedAt", "==", None)\
        .get()

    rows = []
    for snap in all_leads:
        l = snap.to_dict()
        rows.append({
            "snapshot_date":   today,
            "lead_id":         snap.id,
            "email":           l.get("email"),
            "company_name":    l.get("companyName"),
            "company_size":    l.get("companySize"),
            "industry":        l.get("industry"),
            "role_seniority":  l.get("roleSeniority"),
            "source":          l.get("source"),
            "utm_campaign":    (l.get("utm") or {}).get("campaign"),
            "status":          l.get("status"),
            "pipeline_stage":  l.get("pipelineStage"),
            "lead_score":      l.get("leadScore", 0),
            "is_qualified":    l.get("isQualified", False),
            "assigned_to":     l.get("assignedTo"),
            "created_at":      str(l.get("createdAt", "")),
            "first_contact_at": str(l.get("firstContactAt", "")),
            "days_to_qualify": _days_between(l.get("createdAt"), l.get("firstContactAt")),
            "days_to_demo":    None,   # Calcolato da pipeline_history
            "days_to_close":   None,
        })

    if rows:
        # Batch insert a blocchi da 1000 (limite BigQuery)
        for i in range(0, len(rows), 1000):
            chunk  = rows[i:i+1000]
            errors = bq.insert_rows_json(f"{DATASET}.leads_snapshot", chunk)
            if errors:
                import logging
                logging.error(f"BQ snapshot error batch {i}: {errors}")

def _days_between(ts1, ts2) -> int | None:
    if not ts1 or not ts2:
        return None
    from datetime import timezone
    t1 = ts1.replace(tzinfo=timezone.utc) if ts1.tzinfo is None else ts1
    t2 = ts2.replace(tzinfo=timezone.utc) if ts2.tzinfo is None else ts2
    return abs((t2 - t1).days)
```

---

## 11. Revenue forecasting

### `backend/app/services/forecast_service.py`

```python
"""
Revenue forecasting basato su:
1. Pipeline attuale pesata per probabilità storica di chiusura per stage
2. Storico velocità di avanzamento per stage (da BigQuery pipeline_history)
3. Narrative LLM-generated per CEO/CMO
"""
from google.cloud import bigquery
from app.firebase_admin import db
from app.services.gemini_service import model as gemini
from app.config import settings

bq = bigquery.Client(project=settings.FIREBASE_PROJECT_ID)

# Probabilità storiche di chiusura per stage (aggiornate dal modello BQ)
DEFAULT_STAGE_PROBABILITIES = {
    "new":            0.05,
    "contacted":      0.10,
    "qualified":      0.25,
    "demo_scheduled": 0.45,
    "proposal_sent":  0.65,
    "won":            1.00,
    "lost":           0.00,
    "cold":           0.02,
}

async def calculate_forecast() -> dict:
    """
    Calcola previsioni revenue per il prossimo mese, trimestre, anno.
    Salva in BigQuery e Firestore per la dashboard.
    """
    # 1. Recupera tutti i deal aperti con il loro valore
    open_deals = await db.collection("deals")\
        .where("deletedAt", "==", None)\
        .where("stage", "not-in", ["won", "lost"])\
        .get()

    weighted_pipeline = 0.0
    deal_count        = 0
    by_product        = {}
    by_stage          = {}

    for snap in open_deals:
        deal     = snap.to_dict()
        value    = deal.get("value") or 0
        stage    = deal.get("stage", "new")
        product  = deal.get("product", "other")
        prob     = DEFAULT_STAGE_PROBABILITIES.get(stage, 0.1)
        weighted = value * prob

        weighted_pipeline += weighted
        deal_count         += 1

        by_product[product]  = by_product.get(product, 0) + weighted
        by_stage[stage]      = by_stage.get(stage, 0) + weighted

    # 2. Calcola range confidenza (10th, 50th, 90th percentile)
    # Semplice approccio: ±30% per P10/P90 sul weighted
    lower_bound = weighted_pipeline * 0.70
    central     = weighted_pipeline
    upper_bound = weighted_pipeline * 1.40

    # 3. Recupera MRR dai clienti attivi per baseline
    accounts = await db.collection("accounts").get()
    total_mrr = sum(a.to_dict().get("mrr", 0) for a in accounts)

    forecast = {
        "generated_at":     __import__('datetime').datetime.utcnow().isoformat(),
        "pipeline_value":   weighted_pipeline,
        "open_deals":       deal_count,
        "lower_bound":      lower_bound,
        "central":          central,
        "upper_bound":      upper_bound,
        "total_mrr":        total_mrr,
        "by_product":       by_product,
        "by_stage":         by_stage,
        "avg_deal_value":   weighted_pipeline / deal_count if deal_count else 0,
    }

    return forecast

async def generate_forecast_narrative(forecast: dict) -> str:
    """Genera narrazione LLM del forecast per CEO/CMO"""
    prompt = f"""Sei il CFO di AiChain Solutions.
Scrivi un paragrafo di analisi del forecast revenue per il board.
Tono: professionale, diretto, con numeri precisi.
Lunghezza: 5-7 frasi.

DATI:
- Pipeline pesata: €{forecast['pipeline_value']:,.0f}
- Range previsionale: €{forecast['lower_bound']:,.0f} — €{forecast['upper_bound']:,.0f}
- Deal aperti: {forecast['open_deals']}
- MRR attuale: €{forecast['total_mrr']:,.0f}
- Per prodotto: {forecast['by_product']}
- Per stage: {forecast['by_stage']}

Includi: insight chiave, rischi principali, raccomandazione strategica."""

    response = gemini.generate_content(
        prompt,
        generation_config={"temperature": 0.3, "max_output_tokens": 512}
    )
    return response.text
```

---

## 12. Report CEO/CMO — generato da LLM

### `backend/scheduler_handlers/weekly_report.py`

```python
"""
Report settimanale automatico generato da Gemini.
Inviato ogni lunedì alle 08:00 (Europe/Rome) a CEO e CMO.
"""
from datetime import datetime, timezone, timedelta
from google.cloud import bigquery
from app.services.gemini_service import model as gemini
from app.services.email_service import send_tracked_email
from app.firebase_admin import db
from app.config import settings

bq = bigquery.Client(project=settings.FIREBASE_PROJECT_ID)

REPORT_PROMPT = """Sei il Chief Revenue Officer di AiChain Solutions.
Scrivi il Weekly Business Review per CEO e CMO.
Sii diretto, usa numeri precisi, evidenzia anomalie e opportunità.

DATI SETTIMANA SCORSA:
{metrics}

STRUTTURA DEL REPORT (usa questi header esatti):
## Highlights settimana
(3 punti in grassetto — i fatti più importanti)

## Pipeline & Revenue
(analisi lead, conversioni, forecast)

## Top 3 lead da contattare questa settimana
(nome, azienda, score, perché è prioritario)

## Cosa non sta funzionando
(1-2 problemi con dati a supporto — sii onesto)

## Raccomandazione della settimana
(1 azione concreta con impatto stimato)

Lunghezza totale: 350-450 parole. Formato: Markdown."""

async def send_weekly_report():
    """Genera e invia report settimanale"""
    now   = datetime.now(timezone.utc)
    week_ago = now - timedelta(days=7)

    # Query BigQuery per metriche settimanali
    metrics = await _fetch_weekly_metrics(week_ago, now)

    # Top lead da contattare
    top_leads = await _get_top_leads()

    metrics_text = _format_metrics(metrics, top_leads)
    narrative    = gemini.generate_content(
        REPORT_PROMPT.format(metrics=metrics_text),
        generation_config={"temperature": 0.4, "max_output_tokens": 800}
    ).text

    # Invia a CEO e CMO (configurati in Secret Manager)
    recipients = settings.WEEKLY_REPORT_RECIPIENTS.split(",")
    for email in recipients:
        await send_tracked_email(
            db=db,
            to=email.strip(),
            subject=f"📊 Weekly CRM Report — {now.strftime('%d %b %Y')}",
            html=_wrap_report_html(narrative, metrics),
            lead_id=None,
            template_id="weekly_report",
        )

async def _fetch_weekly_metrics(from_dt, to_dt) -> dict:
    """Query BigQuery per metriche della settimana"""
    query = f"""
    SELECT
      -- Nuovi lead
      COUNTIF(DATE(created_at) >= DATE('{from_dt.date()}')) AS new_leads,
      -- Lead per fonte
      COUNTIF(source = 'linkedin' AND DATE(created_at) >= DATE('{from_dt.date()}')) AS linkedin_leads,
      COUNTIF(source = 'assessment' AND DATE(created_at) >= DATE('{from_dt.date()}')) AS assessment_leads,
      -- Conversioni
      COUNTIF(status = 'won' AND DATE(created_at) >= DATE('{from_dt.date()}')) AS won_deals,
      -- Pipeline totale
      COUNT(CASE WHEN status NOT IN ('won','lost','cold') THEN 1 END) AS active_pipeline,
      -- Score medio
      AVG(lead_score) AS avg_score
    FROM `{settings.FIREBASE_PROJECT_ID}.aichain_crm_analytics.leads_snapshot`
    WHERE snapshot_date = (
      SELECT MAX(snapshot_date)
      FROM `{settings.FIREBASE_PROJECT_ID}.aichain_crm_analytics.leads_snapshot`
    )
    """
    rows = list(bq.query(query).result())
    return dict(rows[0]) if rows else {}

def _format_metrics(metrics: dict, top_leads: list) -> str:
    top_leads_text = "\n".join([
        f"- {l.get('firstName','')} {l.get('lastName','')} ({l.get('companyName','')}) — score: {l.get('leadScore',0)}"
        for l in top_leads[:3]
    ])
    return f"""
Nuovi lead questa settimana: {metrics.get('new_leads', 0)}
  - Da LinkedIn: {metrics.get('linkedin_leads', 0)}
  - Da Assessment: {metrics.get('assessment_leads', 0)}
Deal chiusi (won): {metrics.get('won_deals', 0)}
Pipeline attiva totale: {metrics.get('active_pipeline', 0)} lead
Score medio lead: {metrics.get('avg_score', 0):.0f}/100

Top lead da contattare:
{top_leads_text}
"""
```

---

## 13. Customer success module

### `backend/app/services/cs_service.py`

```python
"""
Customer Success: health score, NPS, churn detection, upsell triggers.
Gestisce i clienti attivi (accounts) post-vendita.
"""
from google.cloud.firestore_v1 import FieldFilter
from app.firebase_admin import db
from app.services.firestore_service import update_document, utcnow
from app.services.email_service import send_tracked_email
from datetime import datetime, timezone, timedelta

# Soglie health score
HEALTH_THRESHOLDS = {
    "healthy":  70,   # >= 70 = healthy
    "at_risk":  40,   # 40–69 = at_risk
    # < 40 = churning
}

async def calculate_account_health(account_id: str) -> int:
    """
    Health score 0–100 per account attivo.
    Basato su: login frequency, API usage, NPS, support tickets.
    """
    snap = await db.collection("accounts").document(account_id).get()
    if not snap.exists:
        return 0
    acc   = snap.to_dict()
    score = 0

    # Login frequency (30 giorni)
    logins = acc.get("loginCount30d", 0)
    if logins >= 20:   score += 30
    elif logins >= 10: score += 20
    elif logins >= 3:  score += 10

    # API usage (30 giorni)
    api_calls = acc.get("apiCallsCount30d", 0)
    if api_calls >= 500:  score += 25
    elif api_calls >= 100: score += 15
    elif api_calls >= 10:  score += 5

    # NPS score
    nps = acc.get("lastNpsScore")
    if nps is not None:
        if nps >= 9:   score += 30   # Promoter
        elif nps >= 7: score += 15   # Passive
        else:          score += 0    # Detractor

    # Recency (ultimo login)
    last_login = acc.get("lastLoginAt")
    if last_login:
        days_since = (utcnow() - last_login).days
        if days_since <= 7:    score += 15
        elif days_since <= 30: score += 5
        else:                  score -= 10  # Penalità inattività

    # Tenure bonus (fedeltà)
    start    = acc.get("startDate")
    if start:
        months = (utcnow() - start).days // 30
        score += min(months, 10)  # Max 10 punti bonus

    final_score = max(0, min(100, score))

    # Determina status
    if final_score >= HEALTH_THRESHOLDS["healthy"]:
        health_status = "healthy"
    elif final_score >= HEALTH_THRESHOLDS["at_risk"]:
        health_status = "at_risk"
    else:
        health_status = "churning"

    await update_document(db, "accounts", account_id, {
        "healthScore":  final_score,
        "healthStatus": health_status,
    })

    # Salva storico health score
    await db.collection("accounts").document(account_id)\
        .collection("health_scores").add({
        "score":       final_score,
        "status":      health_status,
        "snapshotAt":  utcnow(),
    })

    return final_score

async def send_nps_survey(account_id: str):
    """Invia survey NPS via email — chiamato da Cloud Scheduler a 30 e 90 giorni"""
    snap = await db.collection("accounts").document(account_id).get()
    if not snap.exists:
        return
    acc = snap.to_dict()

    lead_snap = await db.collection("leads").document(acc["leadId"]).get()
    lead      = lead_snap.to_dict() if lead_snap.exists else {}

    # Genera link NPS (form one-click con token)
    import secrets
    nps_token = secrets.token_urlsafe(32)

    await db.collection("nps_surveys").add({
        "accountId":  account_id,
        "leadId":     acc["leadId"],
        "token":      nps_token,
        "status":     "sent",
        "score":      None,
        "feedback":   None,
        "sentAt":     utcnow(),
        "respondedAt": None,
    })

    nps_url = f"https://crm.aichainsolutions.net/nps/{nps_token}"
    html    = f"""
<p>Ciao {lead.get('firstName', '')},</p>
<p>Usi ZenTratto da qualche settimana — quanto saresti propenso a consigliarlo a un collega?</p>
<div style="display:flex;gap:8px;margin:24px 0">
  {''.join([f'<a href="{nps_url}?score={i}" style="display:inline-block;width:36px;height:36px;background:#f0f0f0;border-radius:50%;text-align:center;line-height:36px;text-decoration:none;color:#111">{i}</a>' for i in range(0,11)])}
</div>
<p style="font-size:12px;color:#999">0 = per nulla probabile &nbsp; 10 = assolutamente sì</p>
"""
    await send_tracked_email(
        db=db,
        to=lead.get("email", ""),
        subject="Come sta andando ZenTratto? (1 domanda)",
        html=html,
        lead_id=acc["leadId"],
    )
    await update_document(db, "accounts", account_id, {"lastNpsSentAt": utcnow()})

async def check_churn_risk():
    """
    Controllato ogni notte da Cloud Scheduler.
    Notifica il CS manager se un account diventa 'churning'.
    """
    accounts = await db.collection("accounts")\
        .where(filter=FieldFilter("healthStatus", "==", "churning"))\
        .get()

    for snap in accounts:
        acc = {"id": snap.id, **snap.to_dict()}
        lead_snap = await db.collection("leads").document(acc["leadId"]).get()
        lead = lead_snap.to_dict() if lead_snap.exists else {}

        # Notifica CS owner
        cs_owner_snap = await db.collection("users").document(acc.get("csOwnerId","")).get()
        if cs_owner_snap.exists:
            cs_email = cs_owner_snap.to_dict().get("email", "")
            await send_tracked_email(
                db=db,
                to=cs_email,
                subject=f"⚠️ Rischio churn: {acc.get('companyName', '')}",
                html=f"""<p>Health score: {acc.get('healthScore')}/100<br>
Ultimo login: {acc.get('lastLoginAt')}<br>
MRR a rischio: €{acc.get('mrr', 0)}/mese</p>
<p><a href="https://crm.aichainsolutions.net/crm/customer-success/{acc['id']}">Apri account →</a></p>""",
                lead_id=acc["leadId"],
            )

async def check_upsell_opportunities():
    """
    Identifica account pronti per upsell.
    Trigger: ha ZenTratto da 60+ giorni, health > 80, non ha SignSisure.
    """
    accounts = await db.collection("accounts")\
        .where(filter=FieldFilter("healthScore", ">=", 80))\
        .get()

    for snap in accounts:
        acc = snap.to_dict()
        if "signsisure" in (acc.get("products") or []):
            continue   # Ha già SignSisure

        start = acc.get("startDate")
        if not start:
            continue
        days_as_customer = (utcnow() - start).days
        if days_as_customer < 60:
            continue   # Troppo presto

        # Lead caldo per upsell — crea task per il CS
        lead_snap = await db.collection("leads").document(acc["leadId"]).get()
        lead_data = lead_snap.to_dict() if lead_snap.exists else {}

        await db.collection("leads").document(acc["leadId"])\
            .collection("tasks").add({
            "leadId":      acc["leadId"],
            "assignedTo":  acc.get("csOwnerId", ""),
            "createdBy":   "system_cs",
            "title":       f"Proponi SignSisure a {acc.get('companyName', '')} — cliente attivo da {days_as_customer}gg",
            "type":        "call",
            "priority":    "high",
            "dueDate":     utcnow() + timedelta(days=3),
            "completedAt": None,
            "aiGenerated": True,
            "createdAt":   utcnow(),
            "updatedAt":   utcnow(),
            "deletedAt":   None,
        })
```

---

## 14. CRM API pubblica

### `backend/app/routers/public_api/router.py`

```python
"""
API CRM pubblica v1 — per integrazioni esterne (ERP, DMS clienti).
Autenticazione: API Key in header X-API-Key.
Rate limiting: per API key, configurabile per piano.
"""
from fastapi import APIRouter, Depends, HTTPException, Header, Request
from app.routers.public_api.auth import verify_api_key
from app.firebase_admin import db
from app.services.firestore_service import create_document, update_document, utcnow

router = APIRouter(prefix="/v1", tags=["Public API"])

@router.get("/leads", summary="Lista lead")
async def api_list_leads(
    status:     str = None,
    industry:   str = None,
    limit:      int = 50,
    api_key_data = Depends(verify_api_key),
):
    """Ritorna lista lead filtrata. Scope richiesto: `leads:read`"""
    if "leads:read" not in api_key_data["scopes"]:
        raise HTTPException(403, "Scope 'leads:read' non presente in questa API key")

    query = db.collection("leads").where("deletedAt", "==", None)
    if status:
        query = query.where("status", "==", status)
    if industry:
        query = query.where("industry", "==", industry)

    leads = await query.limit(min(limit, 100)).get()
    return {
        "data": [
            {
                "id":          snap.id,
                "email":       snap.to_dict().get("email"),
                "company":     snap.to_dict().get("companyName"),
                "status":      snap.to_dict().get("status"),
                "lead_score":  snap.to_dict().get("leadScore"),
                "created_at":  str(snap.to_dict().get("createdAt", "")),
            }
            for snap in leads
        ],
        "count": len(leads),
    }

@router.post("/leads", status_code=201, summary="Crea lead")
async def api_create_lead(
    body: dict,
    api_key_data = Depends(verify_api_key),
):
    """Crea nuovo lead da sistema esterno. Scope: `leads:write`"""
    if "leads:write" not in api_key_data["scopes"]:
        raise HTTPException(403, "Scope 'leads:write' non presente")

    if not body.get("email"):
        raise HTTPException(422, "Campo 'email' obbligatorio")
    if not body.get("consent_given"):
        raise HTTPException(422, "Campo 'consent_given' obbligatorio per GDPR")

    lead = await create_document(db, "leads", {
        "email":       body["email"],
        "firstName":   body.get("first_name"),
        "lastName":    body.get("last_name"),
        "companyName": body.get("company_name"),
        "source":      "api_external",
        "status":      "new",
        "pipelineStage": "new",
        "leadScore":   0,
        "isQualified": False,
        "tags":        ["api_import"],
        "customFields": {"api_source": api_key_data["name"]},
    })
    return {"id": lead["id"], "status": "created"}

@router.post("/leads/{lead_id}/activities", status_code=201)
async def api_create_activity(
    lead_id: str,
    body: dict,
    api_key_data = Depends(verify_api_key),
):
    """Logga attività su un lead da sistema esterno. Scope: `leads:write`"""
    if "leads:write" not in api_key_data["scopes"]:
        raise HTTPException(403, "Scope insufficiente")

    from app.services.firestore_service import append_activity
    activity = await append_activity(db, lead_id, {
        "type":   body.get("type", "note"),
        "title":  body.get("title", "Attività da API esterna"),
        "body":   body.get("body"),
        "userId": None,
        "metadata": {"source": "api", "api_key": api_key_data["name"]},
    })
    return {"id": activity["id"]}
```

### `backend/app/routers/public_api/auth.py`

```python
"""
Autenticazione API key per endpoint pubblici.
Le chiavi vengono create nel CRM e salvate come hash SHA-256 in Firestore.
La chiave vera viene mostrata UNA SOLA VOLTA al momento della creazione.
"""
import hashlib
import secrets
from fastapi import Header, HTTPException
from google.cloud.firestore_v1 import FieldFilter
from app.firebase_admin import db
from app.services.firestore_service import utcnow
from google.cloud.firestore_v1 import Increment

async def verify_api_key(x_api_key: str = Header(...)) -> dict:
    """
    Verifica API key nell'header X-API-Key.
    Cerca per hash SHA-256 (mai la chiave in chiaro in DB).
    """
    if not x_api_key or not x_api_key.startswith("ak_"):
        raise HTTPException(401, "API key non valida — deve iniziare con 'ak_'")

    key_hash = hashlib.sha256(x_api_key.encode()).hexdigest()

    keys = await db.collection("api_keys")\
        .where(filter=FieldFilter("keyHash", "==", key_hash))\
        .where(filter=FieldFilter("isActive", "==", True))\
        .limit(1).get()

    if not keys:
        raise HTTPException(401, "API key non trovata o disattivata")

    key_snap = keys[0]
    key_data = {"id": key_snap.id, **key_snap.to_dict()}

    # Verifica scadenza
    if key_data.get("expiresAt") and key_data["expiresAt"] < utcnow():
        raise HTTPException(401, "API key scaduta")

    # Aggiorna statistiche uso (asincrono)
    await key_snap.reference.update({
        "lastUsedAt": utcnow(),
        "usageCount": Increment(1),
    })

    return key_data

async def create_api_key(
    name: str,
    scopes: list[str],
    owner_id: str,
    expires_days: int = None,
) -> tuple[str, str]:
    """
    Crea una nuova API key.
    Ritorna: (raw_key, key_id)
    Il raw_key viene mostrato UNA SOLA VOLTA — non è recuperabile dopo.
    """
    raw_key    = f"ak_live_{secrets.token_urlsafe(32)}"
    key_hash   = hashlib.sha256(raw_key.encode()).hexdigest()
    key_prefix = raw_key[:12]  # "ak_live_XXXX" — per identificazione UI

    from app.services.firestore_service import create_document
    expires_at = None
    if expires_days:
        from datetime import timedelta
        expires_at = utcnow() + timedelta(days=expires_days)

    key_doc = await create_document(db, "api_keys", {
        "name":       name,
        "keyPrefix":  key_prefix,
        "keyHash":    key_hash,
        "ownerId":    owner_id,
        "scopes":     scopes,
        "isActive":   True,
        "rateLimit":  60,
        "lastUsedAt": None,
        "usageCount": 0,
        "expiresAt":  expires_at,
    })

    return raw_key, key_doc["id"]
```

---

## 15. Frontend — nuovi componenti

### `components/crm/ai/CrmChatAssistant.tsx`

```tsx
"use client"
import { useState, useRef, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Badge } from "@/components/ui/badge"
import { Sparkles, Send, Loader2 } from "lucide-react"
import { api } from "@/lib/api"

interface Message {
  id:      string
  role:    "user" | "assistant"
  content: string
  loading?: boolean
}

const SUGGESTED_QUERIES = [
  "Mostrami lead legali con score > 70 inattivi da 14 giorni",
  "Quali lead hanno menzionato eIDAS nelle note o nelle call?",
  "Chi ha visitato la pagina pricing questa settimana?",
  "Lead del settore finance non ancora qualificati con aziende > 50 persone",
]

export function CrmChatAssistant() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input,    setInput]    = useState("")
  const [loading,  setLoading]  = useState(false)
  const scrollRef = useRef<HTMLDivElement>(null)

  async function sendMessage(question: string) {
    if (!question.trim() || loading) return
    setLoading(true)
    setInput("")

    const userMsg: Message = { id: Date.now().toString(), role: "user", content: question }
    const asstMsg: Message = { id: (Date.now()+1).toString(), role: "assistant", content: "", loading: true }
    setMessages(prev => [...prev, userMsg, asstMsg])

    try {
      // Streaming response via SSE
      const response = await fetch("/api/proxy/ai/query", {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify({ question }),
      })

      const reader = response.body!.getReader()
      const decoder = new TextDecoder()
      let accumulated = ""

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = decoder.decode(value)
        const lines = chunk.split("\n")
        for (const line of lines) {
          if (line.startsWith("data: ") && line !== "data: [DONE]") {
            accumulated += line.slice(6)
            setMessages(prev => prev.map(m =>
              m.id === asstMsg.id
                ? { ...m, content: accumulated, loading: false }
                : m
            ))
          }
        }
      }
    } catch (error) {
      setMessages(prev => prev.map(m =>
        m.id === asstMsg.id
          ? { ...m, content: "Errore nella query — riprova.", loading: false }
          : m
      ))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  return (
    <div className="flex flex-col h-full border rounded-lg bg-background">
      {/* Header */}
      <div className="flex items-center gap-2 p-4 border-b">
        <Sparkles className="h-4 w-4 text-primary" />
        <span className="font-medium text-sm">AI Assistant CRM</span>
        <Badge variant="secondary" className="text-xs">ZenTratto RAG</Badge>
      </div>

      {/* Messages */}
      <ScrollArea className="flex-1 p-4">
        {messages.length === 0 && (
          <div className="space-y-3">
            <p className="text-sm text-muted-foreground">
              Interroga il CRM in linguaggio naturale. Esempi:
            </p>
            {SUGGESTED_QUERIES.map((q, i) => (
              <button
                key={i}
                onClick={() => sendMessage(q)}
                className="block w-full text-left text-sm p-2 rounded-md border border-dashed hover:bg-muted/50 transition-colors"
              >
                {q}
              </button>
            ))}
          </div>
        )}

        {messages.map((msg) => (
          <div key={msg.id} className={`mb-4 flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
            <div className={`max-w-[85%] rounded-lg p-3 text-sm ${
              msg.role === "user"
                ? "bg-primary text-primary-foreground"
                : "bg-muted"
            }`}>
              {msg.loading
                ? <Loader2 className="h-4 w-4 animate-spin" />
                : <div className="whitespace-pre-wrap">{msg.content}</div>
              }
            </div>
          </div>
        ))}
        <div ref={scrollRef} />
      </ScrollArea>

      {/* Input */}
      <div className="flex gap-2 p-4 border-t">
        <Input
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === "Enter" && !e.shiftKey && sendMessage(input)}
          placeholder="Interroga il CRM... (es: 'lead legali con score > 60')"
          disabled={loading}
          className="text-sm"
        />
        <Button
          size="icon"
          onClick={() => sendMessage(input)}
          disabled={loading || !input.trim()}
        >
          {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
        </Button>
      </div>
    </div>
  )
}
```

### Nuovi componenti shadcn/ui da installare

```bash
npx shadcn@latest add progress
npx shadcn@latest add chart          # Wrapper Recharts ufficiale shadcn
npx shadcn@latest add collapsible
npx shadcn@latest add alert
npx shadcn@latest add skeleton
```

---

## 16. Firestore rules — aggiornamento Fase 3

```js
// Aggiungere alle rules esistenti (Fase 1 + 2):

match /call_recordings/{callId} {
  allow read: if isSales();
  allow create, update: if isSales();
  allow delete: if isAdmin();
}

match /call_insights/{callId} {
  allow read: if isSales();
  allow create, update: if false;  // Solo backend AI worker
}

// Blockchain records — append-only, solo lettura per il team
match /blockchain_records/{recordId} {
  allow read: if isSales();
  allow create: if false;           // Solo backend via Admin SDK
  allow update, delete: if false;   // IMMUTABILE — mai modificare
}

match /ai_suggestions/{suggId} {
  allow read: if isSales();
  allow update: if isSales();       // Per feedback (wasUsed, rating)
  allow create, delete: if false;   // Solo backend
}

match /accounts/{accountId} {
  allow read: if isSales();
  allow create, update: if isSales();
  allow delete: if isAdmin();

  match /health_scores/{scoreId} {
    allow read: if isSales();
    allow create: if false;         // Solo CS worker
    allow update, delete: if false;
  }
}

match /nps_surveys/{surveyId} {
  allow read: if isSales();
  allow create: if false;           // Solo scheduler
  allow update: if true;            // Risposta NPS pubblica (token-based)
}

// API keys — solo admin le gestisce
match /api_keys/{keyId} {
  allow read: if isAdmin();
  allow write: if isAdmin();
}
```

---

## 17. CI/CD — aggiornamento Fase 3

### Nuovi Cloud Run services

```bash
# Build e deploy 4 nuovi workers Fase 3
WORKERS_F3=("ai-worker" "blockchain-worker" "analytics-worker" "cs-worker")

for WORKER in "${WORKERS_F3[@]}"; do
  IMAGE="europe-west1-docker.pkg.dev/$PROJECT_ID/crm/${WORKER}:latest"

  gcloud builds submit ./backend/workers/${WORKER//-/_} --tag=$IMAGE

  gcloud run deploy crm-$WORKER \
    --image=$IMAGE \
    --region=europe-west1 \
    --no-allow-unauthenticated \
    --service-account=crm-ai-worker@$PROJECT_ID.iam.gserviceaccount.com \
    --memory=1Gi \
    --cpu=2 \
    --min-instances=0 \
    --max-instances=5 \
    --concurrency=5 \
    --timeout=300   # 5 min per job AI lunghi
done

# Nuovi Pub/Sub topics Fase 3
gcloud pubsub topics create crm.ai.events \
  --message-retention-duration=7d

gcloud pubsub topics create crm.blockchain.events \
  --message-retention-duration=30d   # Più lungo per audit

# Nuovi Cloud Scheduler Fase 3
gcloud scheduler jobs create http crm-bigquery-sync \
  --location=europe-west1 \
  --schedule="0 1 * * *" \
  --uri="https://crm-scheduler-HASH-ew.a.run.app/scheduler/bigquery-sync" \
  --oidc-service-account-email="crm-ai-worker@$PROJECT_ID.iam.gserviceaccount.com" \
  --time-zone="Europe/Rome"

gcloud scheduler jobs create http crm-forecast-refresh \
  --location=europe-west1 \
  --schedule="0 6 * * 1" \
  --uri="https://crm-scheduler-HASH-ew.a.run.app/scheduler/forecast-refresh" \
  --oidc-service-account-email="crm-ai-worker@$PROJECT_ID.iam.gserviceaccount.com" \
  --time-zone="Europe/Rome"

gcloud scheduler jobs create http crm-churn-check \
  --location=europe-west1 \
  --schedule="0 9 * * *" \
  --uri="https://crm-scheduler-HASH-ew.a.run.app/scheduler/churn-check" \
  --oidc-service-account-email="crm-ai-worker@$PROJECT_ID.iam.gserviceaccount.com" \
  --time-zone="Europe/Rome"

gcloud scheduler jobs create http crm-nps-send \
  --location=europe-west1 \
  --schedule="0 10 * * *" \
  --uri="https://crm-scheduler-HASH-ew.a.run.app/scheduler/nps-send" \
  --oidc-service-account-email="crm-ai-worker@$PROJECT_ID.iam.gserviceaccount.com" \
  --time-zone="Europe/Rome"
```

### Nuovi secret in Secret Manager

```bash
gcloud secrets create SIGNSISURE_API_URL \
  --replication-policy=user-managed --locations=europe-west1

gcloud secrets create SIGNSISURE_API_KEY \
  --replication-policy=user-managed --locations=europe-west1

gcloud secrets create VERTEX_INDEX_ENDPOINT_ID \
  --replication-policy=user-managed --locations=europe-west1

gcloud secrets create VERTEX_DEPLOYED_INDEX_ID \
  --replication-policy=user-managed --locations=europe-west1

gcloud secrets create WEEKLY_REPORT_RECIPIENTS \
  --replication-policy=user-managed --locations=europe-west1
# Valore: "ceo@aichainsolutions.net,cmo@aichainsolutions.net"
```

---

## 18. Costi stimati Fase 3

```
Scenario: 500 lead, 50 AI queries/mese, 10 call trascritte/mese, 100 clienti attivi

Vertex AI (europe-west4):
  Gemini 1.5 Pro — email writer + report:
    ~100K token input + 50K token output/mese      → €5–15
  Text Embedding — indicizzazione:
    ~500K token/mese (aggiornamenti incrementali)  → €0.05
  Matching Engine — vector search:
    ~50 query/mese, indice < 100K datapoints       → €15–30 (nodo dedicato)
    ⚠️  NOTA: Matching Engine ha costo fisso di
    istanza (€0.60/ora). Valuta streaming index
    (più economico) per Fase 3 iniziale.

Cloud Speech-to-Text v2:
  10 call × 30 min = 300 minuti/mese
  Chirp model: €0.016/min                          → €4.80

BigQuery (EU):
  Storage: < 10GB dati analitici                   → €0.20
  Query: ~100 query/mese × avg 1GB processed       → €0.50
  ML training: 1 volta/mese × 100MB dataset        → €0.05

Nuovi Cloud Run workers (Fase 3):
  AI worker (1Gi RAM, 2 CPU): ~100 invocazioni     → €3–8

COSTO AGGIUNTIVO FASE 3: €30–60/mese
─────────────────────────────────────────────────
TOTALE CUMULATIVO FASE 1 + 2 + 3: €55–150/mese

⚠️ Voci da monitorare:
- Matching Engine: costa anche a riposo (nodo fisso)
  Alternativa economica: Vertex AI Vector Search (preview)
  o pgvector su Cloud SQL (€15/mese fisso, più economico)
- Gemini API: scalare con il numero di AI queries
  — mettere rate limit per utente nel CRM
```

---

## 19. Checklist sviluppatore

### Prerequisiti Fase 3

- [ ] Fase 1 + Fase 2 in produzione e stabili
- [ ] BigQuery dataset `aichain_crm_analytics` creato in regione EU
- [ ] Vertex AI API abilitata sul progetto GCP
- [ ] Account SignSisure API configurato e testato
- [ ] Service account `crm-ai-worker` con permessi corretti

### Sprint 1 — settimane 1–3: BigQuery + Analytics

- [ ] Schema tabelle BigQuery create (4 tabelle + 4 view SQL)
- [ ] `bigquery_service.py` — streaming insert + nightly snapshot
- [ ] Cloud Scheduler `crm-bigquery-sync` — nightly sync alle 01:00
- [ ] Test snapshot: 100 lead → BigQuery → query di verifica
- [ ] View SQL: conversion_funnel, revenue_by_source, email_engagement
- [ ] Frontend: `analytics/page.tsx` aggiornato con BigQuery data
- [ ] Frontend: `forecasting/page.tsx` con grafici Recharts
- [ ] `forecast_service.py` — pipeline weighting + narrative LLM
- [ ] Cloud Scheduler `crm-forecast-refresh` — ogni lunedì
- [ ] Report CEO/CMO: template + Cloud Scheduler + test invio

### Sprint 2 — settimane 4–6: ZenTratto RAG + AI Features

- [ ] Vertex AI Matching Engine index creato (europe-west4)
- [ ] `embed_leads.py` — script one-shot per indicizzare lead esistenti
- [ ] `rag_service.py` — embed_text, query_crm, index_lead_data
- [ ] Router `/api/v1/ai/query` — streaming SSE
- [ ] Frontend: `CrmChatAssistant` con SSE streaming
- [ ] Test RAG: 10 query diverse → risultati pertinenti verificati manualmente
- [ ] `gemini_service.py` — email_writer con tutti i 4 template
- [ ] Router `/api/v1/ai/email-draft` + frontend drawer email
- [ ] Router `/api/v1/ai/call-prep` + frontend button sulla scheda lead
- [ ] Cloud Task: `index-lead` — indicizzazione incrementale dopo update

### Sprint 3 — settimane 7–9: Blockchain + Call Analysis

- [ ] `signsisure_service.py` — notarize, notarize_gdpr_consent, notarize_deal_closed
- [ ] `blockchain_worker` Cloud Run — subscribe `crm.blockchain.events`
- [ ] Test blockchain: consent GDPR → hash → SignSisure → record in Firestore
- [ ] Aggiornamento `gdpr_service.py` — trigger notarizzazione automatica
- [ ] `speech_service.py` — transcribe_call_audio con Cloud Speech v2
- [ ] `call_analysis_service.py` — analyze_call con Gemini
- [ ] `ai_worker` Cloud Run — handlers per trascrizione + analisi
- [ ] Frontend: `calls/page.tsx` — upload recording + viewer trascrizione
- [ ] Highlight transcript con word-level timing
- [ ] Test end-to-end: upload audio → trascrizione → analisi → CRM update

### Sprint 4 — settimane 10–12: CS + API Pubblica + ML Scoring

- [ ] BigQuery ML model `lead_conversion_model` addestrato (min 100 lead storici)
- [ ] `scoring_service.py` v3 — ML probability da BigQuery
- [ ] Frontend: badge "AI Score" sulla scheda lead con spiegazione fattori
- [ ] `cs_service.py` — health score, NPS, churn, upsell
- [ ] `accounts` collection Firestore + `customer-success/page.tsx`
- [ ] Cloud Scheduler: NPS a 30/90 giorni, churn check giornaliero
- [ ] Endpoint NPS pubblico `/nps/{token}` per risposta one-click
- [ ] API pubblica: `/v1/leads` CRUD + `/v1/leads/:id/activities`
- [ ] `api_key_service.py` — create_api_key + verify_api_key
- [ ] Frontend: `developer/page.tsx` — gestione API key + doc inline
- [ ] Rate limiting per API key (slowapi per chiave, non per IP)
- [ ] Test integrazione: chiave API → crea lead → vedi nel CRM
- [ ] Security final review: tutte le rule Firestore, OIDC worker, API key scopes
- [ ] Load test: 100 query AI in parallelo → latenza accettabile
- [ ] Documentazione OpenAPI completata per API pubblica
- [ ] Handoff QA completo + runbook operativo

---

> **Il CRM è ora un prodotto.** L'API pubblica di Fase 3 è il punto di ingresso
> per la quarta fase non documentata: **commercializzazione del CRM** come prodotto
> verticale per studi legali e finance — posizionato come "l'unico CRM con
> blockchain audit trail nativo e AI RAG su documenti interni."

---

*AiChain Solutions — CTO Office · Fase 3 Intelligence · Maggio 2026*
*Stack: FastAPI · Firebase · Vertex AI (europe-west4) · BigQuery EU · SignSisure · GCP europe-west1*
