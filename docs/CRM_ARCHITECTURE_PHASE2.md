# AiChain CRM — Specifiche Tecniche Fase 2
> **Automation: Email Sequences · Lead Scoring · WhatsApp · Workflow Engine**
> **Stack: FastAPI · Firebase · Cloud Pub/Sub · Cloud Scheduler · GCP europe-west1**
> Versione: 1.0 · Prerequisito: Fase 1 completata · Autore: AiChain Solutions CTO

---

## Indice

1. [Panoramica architetturale](#1-panoramica-architetturale)
2. [Nuovi servizi GCP](#2-nuovi-servizi-gcp)
3. [Struttura repository — delta da Fase 1](#3-struttura-repository--delta-da-fase-1)
4. [Firestore — nuove collezioni](#4-firestore--nuove-collezioni)
5. [Event bus — Cloud Pub/Sub](#5-event-bus--cloud-pubsub)
6. [Email sequences — drip campaigns](#6-email-sequences--drip-campaigns)
7. [Email tracking — open & click](#7-email-tracking--open--click)
8. [Template engine](#8-template-engine)
9. [Workflow builder](#9-workflow-builder)
10. [Lead scoring avanzato](#10-lead-scoring-avanzato)
11. [Visitor tracking](#11-visitor-tracking)
12. [Segmentazione dinamica](#12-segmentazione-dinamica)
13. [WhatsApp Business API](#13-whatsapp-business-api)
14. [Inbox unificata — real-time](#14-inbox-unificata--real-time)
15. [Preventivi & offerte PDF](#15-preventivi--offerte-pdf)
16. [Cloud Scheduler — job periodici](#16-cloud-scheduler--job-periodici)
17. [Frontend — nuovi componenti](#17-frontend--nuovi-componenti)
18. [Firestore rules — aggiornamento](#18-firestore-rules--aggiornamento)
19. [CI/CD — aggiornamento](#19-cicd--aggiornamento)
20. [Costi stimati Fase 2](#20-costi-stimati-fase-2)
21. [Checklist sviluppatore](#21-checklist-sviluppatore)

---

## 1. Panoramica architetturale

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      GOOGLE CLOUD PLATFORM — europe-west1               │
│                                                                         │
│  ┌────────────────┐          ┌─────────────────────────────────────┐   │
│  │ Cloud Run      │          │  Cloud Run — Backend FastAPI        │   │
│  │ Next.js CRM    │◄────────►│  + nuovi router Fase 2             │   │
│  └────────────────┘          └──────────────┬──────────────────────┘   │
│                                             │                           │
│         ┌───────────────────────────────────┼──────────────────┐       │
│         │                                   │                  │       │
│  ┌──────▼──────────┐             ┌──────────▼──────┐   ┌───────▼────┐ │
│  │  Cloud Pub/Sub  │             │   Firebase       │   │  Cloud     │ │
│  │  Event Bus      │             │   Firestore      │   │  Scheduler │ │
│  │                 │             │   Auth · Storage │   │  Cron jobs │ │
│  │  Topics:        │             │   Realtime DB    │   │            │ │
│  │  crm.lead.*     │             │   (inbox RT)     │   │  5 job     │ │
│  │  crm.email.*    │             └──────────────────┘   └────────────┘ │
│  │  crm.workflow.* │                                                    │
│  │  crm.score.*    │                                                    │
│  └──────┬──────────┘                                                    │
│         │  Subscribe                                                     │
│  ┌──────▼──────────────────────────────────────────────────────┐       │
│  │              Cloud Run — Workers (Pub/Sub push)              │       │
│  │                                                             │       │
│  │  WorkflowWorker  ScoringWorker  SequenceWorker  InboxWorker │       │
│  │  (stateless, scala a 0 quando non ci sono eventi)           │       │
│  └─────────────────────────────────────────────────────────────┘       │
│                                                                         │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────────┐ │
│  │  Cloud Tasks     │  │  Secret Manager  │  │  Artifact Registry   │ │
│  │  (da Fase 1)     │  │  + nuovi secret  │  │  + nuove immagini    │ │
│  └──────────────────┘  └──────────────────┘  └──────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
         │                              │                    │
  ┌──────▼──────┐              ┌────────▼──────┐    ┌───────▼──────────┐
  │  Resend EU  │              │  Meta Cloud   │    │  Website         │
  │  Email API  │              │  WhatsApp     │    │  aichainsolutions │
  │  Frankfurt  │              │  Business API │    │  Visitor tracking│
  └─────────────┘              └───────────────┘    └──────────────────┘
```

### Principio architetturale Fase 2: Event-Driven

In Fase 1 ogni azione era **sincrona** (request → response) o via **Cloud Tasks** (job one-shot).

In Fase 2 adottiamo un **event bus** (Cloud Pub/Sub) che disaccoppia completamente i produttori di eventi dai consumatori:

```
Evento accade          →  Pub/Sub topic   →  1+ subscriber reagiscono
─────────────────────────────────────────────────────────────────────
lead.status_changed    →  crm.lead.events → [WorkflowWorker, ScoringWorker]
email.opened           →  crm.email.events→ [ScoringWorker, SequenceWorker]
form.submitted         →  crm.lead.events → [WorkflowWorker, SequenceWorker]
whatsapp.received      →  crm.inbox.events→ [InboxWorker, WorkflowWorker]
```

**Vantaggi concreti:**
- Aggiungere un nuovo subscriber non richiede modifiche al produttore
- Ogni worker scala indipendentemente
- Se un worker è giù, i messaggi rimangono in coda (nessun dato perso)
- Audit trail naturale: ogni evento è loggato in Pub/Sub

---

## 2. Nuovi servizi GCP

### Abilitazione servizi

```bash
gcloud services enable \
  pubsub.googleapis.com \
  cloudscheduler.googleapis.com \
  bigquery.googleapis.com
```

### Cloud Pub/Sub — setup topics e subscriptions

```bash
# ── Topics ──────────────────────────────────────────────────────
gcloud pubsub topics create crm.lead.events      --message-retention-duration=7d
gcloud pubsub topics create crm.email.events     --message-retention-duration=7d
gcloud pubsub topics create crm.workflow.events  --message-retention-duration=7d
gcloud pubsub topics create crm.score.events     --message-retention-duration=3d
gcloud pubsub topics create crm.inbox.events     --message-retention-duration=7d

# ── Subscriptions (push verso Cloud Run workers) ─────────────────
# WorkflowWorker: riceve lead + email + inbox events
gcloud pubsub subscriptions create workflow-worker-sub \
  --topic=crm.lead.events \
  --push-endpoint=https://crm-workflow-worker-HASH-ew.a.run.app/pubsub/lead \
  --push-auth-service-account=crm-workers@$PROJECT_ID.iam.gserviceaccount.com \
  --ack-deadline=60 \
  --message-retention-duration=7d \
  --retry-policy-minimum-backoff=10s \
  --retry-policy-maximum-backoff=600s

gcloud pubsub subscriptions create sequence-worker-sub \
  --topic=crm.email.events \
  --push-endpoint=https://crm-sequence-worker-HASH-ew.a.run.app/pubsub/email \
  --push-auth-service-account=crm-workers@$PROJECT_ID.iam.gserviceaccount.com \
  --ack-deadline=60

gcloud pubsub subscriptions create scoring-worker-sub \
  --topic=crm.score.events \
  --push-endpoint=https://crm-scoring-worker-HASH-ew.a.run.app/pubsub/score \
  --push-auth-service-account=crm-workers@$PROJECT_ID.iam.gserviceaccount.com \
  --ack-deadline=30

gcloud pubsub subscriptions create inbox-worker-sub \
  --topic=crm.inbox.events \
  --push-endpoint=https://crm-inbox-worker-HASH-ew.a.run.app/pubsub/inbox \
  --push-auth-service-account=crm-workers@$PROJECT_ID.iam.gserviceaccount.com \
  --ack-deadline=30
```

### Service account per i worker

```bash
# SA dedicato per i worker (principio least privilege)
gcloud iam service-accounts create crm-workers \
  --display-name="CRM Workers Service Account"

# Permessi: solo lettura/scrittura Firestore + Pub/Sub publish
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member=serviceAccount:crm-workers@$PROJECT_ID.iam.gserviceaccount.com \
  --role=roles/datastore.user

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member=serviceAccount:crm-workers@$PROJECT_ID.iam.gserviceaccount.com \
  --role=roles/pubsub.publisher

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member=serviceAccount:crm-workers@$PROJECT_ID.iam.gserviceaccount.com \
  --role=roles/secretmanager.secretAccessor
```

---

## 3. Struttura repository — delta da Fase 1

```
aichain-crm/
├── backend/
│   └── app/
│       ├── routers/
│       │   ├── [FASE 1 — invariati]
│       │   ├── sequences.py          ✨ NUOVO — gestione sequenze email
│       │   ├── templates.py          ✨ NUOVO — template email
│       │   ├── workflows.py          ✨ NUOVO — workflow builder API
│       │   ├── segments.py           ✨ NUOVO — segmenti dinamici
│       │   ├── whatsapp.py           ✨ NUOVO — webhook + send WhatsApp
│       │   ├── inbox.py              ✨ NUOVO — inbox unificata
│       │   ├── proposals.py          ✨ NUOVO — preventivi PDF
│       │   └── tracking.py           ✨ NUOVO — open pixel + click redirect
│       │
│       ├── services/
│       │   ├── [FASE 1 — invariati]
│       │   ├── pubsub_service.py     ✨ NUOVO — publish eventi
│       │   ├── sequence_service.py   ✨ NUOVO — drip logic
│       │   ├── template_service.py   ✨ NUOVO — render template + variabili
│       │   ├── workflow_service.py   ✨ NUOVO — execute workflow
│       │   ├── segment_service.py    ✨ NUOVO — evaluate segmenti
│       │   ├── whatsapp_service.py   ✨ NUOVO — Meta Cloud API
│       │   ├── pdf_service.py        ✨ NUOVO — generazione preventivi
│       │   └── scoring_service.py    🔄 AGGIORNATO — scoring v2
│       │
│       ├── workers/                  ✨ NUOVO — app separate per ogni worker
│       │   ├── workflow_worker/
│       │   │   ├── main.py           FastAPI app del WorkflowWorker
│       │   │   ├── handlers.py       Handler per ogni tipo di evento
│       │   │   ├── Dockerfile
│       │   │   └── requirements.txt
│       │   ├── sequence_worker/
│       │   │   ├── main.py
│       │   │   ├── handlers.py
│       │   │   ├── Dockerfile
│       │   │   └── requirements.txt
│       │   ├── scoring_worker/
│       │   │   ├── main.py
│       │   │   └── Dockerfile
│       │   └── inbox_worker/
│       │       ├── main.py
│       │       └── Dockerfile
│       │
│       └── scheduler_handlers/      ✨ NUOVO — endpoint per Cloud Scheduler
│           ├── main.py
│           ├── sequence_tick.py     "Avanza le sequenze ogni ora"
│           ├── segment_refresh.py   "Ricalcola segmenti ogni notte"
│           ├── score_decay.py       "Score decay settimanale"
│           └── Dockerfile
│
├── frontend/
│   └── app/crm/
│       ├── [FASE 1 — invariati]
│       ├── sequences/page.tsx        ✨ NUOVO
│       ├── templates/page.tsx        ✨ NUOVO
│       ├── workflows/page.tsx        ✨ NUOVO
│       ├── segments/page.tsx         ✨ NUOVO
│       ├── inbox/page.tsx            ✨ NUOVO
│       └── proposals/page.tsx        ✨ NUOVO
│
├── visitor-tracker/                  ✨ NUOVO — snippet JS per il sito
│   ├── tracker.js                    Script leggero da includere nel sito
│   └── tracker.min.js                Versione minificata (< 3KB)
│
└── docker-compose.yml                🔄 AGGIORNATO — 4 worker aggiuntivi
```

---

## 4. Firestore — nuove collezioni

### Nuove collezioni Fase 2

```
firestore-root/
├── [FASE 1 — invariate]
│
├── email_templates/{templateId}       ✨ Template email riutilizzabili
├── sequences/{sequenceId}             ✨ Definizione sequenza drip
│   └── steps/{stepId}                 ✨ Singolo step della sequenza
├── sequence_enrollments/{enrollId}    ✨ Lead iscritti a una sequenza
├── email_sends/{sendId}               ✨ Ogni email inviata (tracking)
├── workflows/{workflowId}             ✨ Definizione workflow automazione
│   └── conditions/{conditionId}       ✨ Condizioni if/then
├── segments/{segmentId}               ✨ Segmenti dinamici
├── segment_memberships/{membId}       ✨ Lead appartenenti a segmenti
├── conversations/{convId}             ✨ Thread conversazione (email/WA)
│   └── messages/{messageId}           ✨ Messaggi nella conversazione
├── whatsapp_templates/{tplId}         ✨ Template WhatsApp approvati Meta
└── proposals/{proposalId}             ✨ Preventivi generati
```

### Schema documenti nuovi

#### `email_templates/{templateId}`

```typescript
{
  name:         string,           // Nome interno: "Benvenuto Playbook"
  subject:      string,           // "{{firstName}}, ecco il tuo playbook"
  bodyHtml:     string,           // HTML con variabili {{variable}}
  bodyText:     string,           // Plain text fallback
  category:     "welcome" | "followup" | "nurture" | "proposal" | "reminder",
  variables:    string[],         // ["firstName","companyName","roiEstimate"]
  previewText:  string | null,    // Testo anteprima in client email
  fromName:     string,           // "Marco da AiChain" o "AiChain Solutions"
  isActive:     boolean,
  createdBy:    string,           // uid
  createdAt:    Timestamp,
  updatedAt:    Timestamp,
}
```

#### `sequences/{sequenceId}`

```typescript
{
  name:         string,           // "Nurturing Playbook Download"
  description:  string | null,
  trigger:      "playbook_download" | "assessment_completed" | "booking_created" |
                "manual" | "stage_changed" | "score_threshold",
  triggerConfig: {
                  // Per stage_changed: { fromStage, toStage }
                  // Per score_threshold: { minScore, maxScore }
                },
  isActive:     boolean,
  enrollOnce:   boolean,          // true = un lead si iscrive una sola volta
  stopOnReply:  boolean,          // true = ferma sequenza se risponde
  stopOnConvert: boolean,         // true = ferma se diventa "won"
  totalSteps:   number,
  createdBy:    string,
  createdAt:    Timestamp,
  updatedAt:    Timestamp,
}
```

#### `sequences/{sequenceId}/steps/{stepId}`

```typescript
{
  stepNumber:   number,           // 1, 2, 3...
  delayDays:    number,           // Giorni dopo lo step precedente (0 = immediato)
  delayHours:   number,           // Ore aggiuntive
  sendAt:       "09:00" | "14:00" | string, // Ora locale preferita di invio
  channel:      "email" | "whatsapp" | "task",
  templateId:   string,           // Riferimento a email_templates o whatsapp_templates
  // Se channel = "task":
  taskConfig: {
    title:    string,             // "Chiamare {{firstName}}"
    type:     string,
    priority: string,
    assignTo: "lead_owner" | string, // uid specifico
  },
  condition: {                    // Invia SOLO SE...
    type:     "always" | "not_opened_prev" | "opened_prev" | "score_above" | "score_below",
    value:    number | null,
  } | null,
  createdAt:    Timestamp,
}
```

#### `sequence_enrollments/{enrollId}`

```typescript
{
  leadId:       string,
  sequenceId:   string,
  currentStep:  number,           // Step attuale (0 = non ancora iniziato)
  totalSteps:   number,
  status:       "active" | "paused" | "completed" | "stopped" | "bounced",
  stopReason:   "replied" | "converted" | "unsubscribed" | "manual" | null,
  enrolledAt:   Timestamp,
  nextSendAt:   Timestamp | null, // Quando inviare il prossimo step
  completedAt:  Timestamp | null,
  // Stats
  emailsSent:   number,
  emailsOpened: number,
  linksClicked: number,
}
```

#### `email_sends/{sendId}`

```typescript
{
  // Ogni email inviata ha un record qui (tracking)
  leadId:       string,
  sequenceId:   string | null,    // null se email manuale
  stepId:       string | null,
  templateId:   string | null,
  resendId:     string,           // ID univoco di Resend
  to:           string,           // Email destinatario
  subject:      string,
  status:       "sent" | "delivered" | "opened" | "clicked" | "bounced" | "complained",
  // Tracking
  openedAt:     Timestamp | null,
  openCount:    number,
  clickedAt:    Timestamp | null,
  clickCount:   number,
  bouncedAt:    Timestamp | null,
  // Per open tracking
  trackingPixelId: string,        // UUID usato nell'URL del pixel
  // Per click tracking — mappa {link_originale: link_tracking}
  trackedLinks: Record<string, string>,
  createdAt:    Timestamp,
}
```

#### `workflows/{workflowId}`

```typescript
{
  name:         string,           // "Auto-assegna studio legale"
  description:  string | null,
  isActive:     boolean,
  trigger: {
    event:      "lead_created" | "lead_updated" | "stage_changed" |
                "score_changed" | "email_opened" | "form_submitted" |
                "booking_created" | "whatsapp_received",
    filters:    Array<{
      field:    string,           // "industry" | "leadScore" | "source"
      operator: "==" | "!=" | ">" | "<" | ">=" | "<=" | "in" | "contains",
      value:    unknown,
    }>,
  },
  actions:      Array<{
    type:       "assign_lead" | "change_stage" | "add_tag" | "enroll_sequence" |
                "create_task" | "send_email" | "send_whatsapp" | "webhook",
    config:     Record<string, unknown>,
    // Esempi:
    // assign_lead:    { assignTo: "uid_or_round_robin" }
    // change_stage:   { stage: "qualified" }
    // enroll_sequence:{ sequenceId: "xxx" }
    // create_task:    { title, type, dueInDays, assignTo }
    // send_email:     { templateId }
    // webhook:        { url, method, headers, body }
  }>,
  executionCount: number,         // Contatore esecuzioni (update atomico)
  createdBy:    string,
  createdAt:    Timestamp,
  updatedAt:    Timestamp,
}
```

#### `segments/{segmentId}`

```typescript
{
  name:         string,           // "Studio Legale — Score Alto"
  description:  string | null,
  color:        string,           // Hex colore UI: "#7F77DD"
  isActive:     boolean,
  isDynamic:    boolean,          // true = ricalcolato automaticamente
  rules: {
    operator:   "AND" | "OR",
    conditions: Array<{
      field:    string,           // "industry" | "leadScore" | "status" | "source"
      operator: "==" | "!=" | ">" | "<" | "in" | "not_in" | "contains",
      value:    unknown,
    }>,
  },
  memberCount:  number,           // Aggiornato da Cloud Scheduler
  lastEvaluatedAt: Timestamp | null,
  createdBy:    string,
  createdAt:    Timestamp,
  updatedAt:    Timestamp,
}
```

#### `conversations/{convId}`

```typescript
{
  leadId:       string,
  channel:      "email" | "whatsapp",
  status:       "open" | "resolved" | "waiting",
  assignedTo:   string | null,    // uid
  subject:      string | null,    // Solo per email
  lastMessageAt: Timestamp,
  lastMessagePreview: string,     // Primi 100 caratteri
  unreadCount:  number,           // Per il team
  // WhatsApp specifico
  whatsappPhone: string | null,
  createdAt:    Timestamp,
  updatedAt:    Timestamp,
}
```

#### `conversations/{convId}/messages/{messageId}`

```typescript
{
  convId:       string,
  direction:    "inbound" | "outbound",
  channel:      "email" | "whatsapp",
  fromAddress:  string,           // Email o phone
  toAddress:    string,
  body:         string,           // Testo del messaggio
  bodyHtml:     string | null,    // Solo email
  attachments:  Array<{
    name:       string,
    url:        string,           // Firebase Storage URL
    mimeType:   string,
    sizeBytes:  number,
  }>,
  status:       "sent" | "delivered" | "read" | "failed",
  // WhatsApp
  whatsappMessageId: string | null,
  // Email
  resendId:         string | null,
  emailSendId:      string | null,
  sentBy:       string | null,    // uid se outbound manuale
  createdAt:    Timestamp,
}
```

#### `proposals/{proposalId}`

```typescript
{
  leadId:       string,
  dealId:       string | null,
  createdBy:    string,           // uid
  title:        string,
  status:       "draft" | "sent" | "viewed" | "accepted" | "rejected" | "expired",
  // Contenuto
  items:        Array<{
    product:    string,
    description: string,
    quantity:   number,
    unitPrice:  number,
    discount:   number,           // Percentuale 0-100
    total:      number,
  }>,
  subtotal:     number,
  discount:     number,
  tax:          number,
  total:        number,
  currency:     "EUR",
  validUntil:   Timestamp,
  notes:        string | null,
  // File
  pdfUrl:       string | null,    // Firebase Storage URL
  pdfPath:      string | null,    // Storage path
  // Tracking
  viewedAt:     Timestamp | null,
  viewCount:    number,
  trackingToken: string,          // Token per tracciare apertura link
  // Firma (Fase 3 — SignSisure)
  signatureStatus: "none" | "requested" | "signed",
  signedAt:     Timestamp | null,
  createdAt:    Timestamp,
  updatedAt:    Timestamp,
}
```

---

## 5. Event bus — Cloud Pub/Sub

### `backend/app/services/pubsub_service.py`

```python
"""
Publisher centralizzato per tutti gli eventi CRM.
Ogni modulo pubblica qui — non conosce i subscriber.
"""
import json
import base64
from google.cloud import pubsub_v1
from datetime import datetime, timezone
from app.config import settings
from typing import Any

publisher = pubsub_v1.PublisherClient()

def _topic_path(topic_name: str) -> str:
    return publisher.topic_path(settings.FIREBASE_PROJECT_ID, topic_name)

async def publish_event(topic: str, event_type: str, payload: dict[str, Any]):
    """
    Pubblica un evento su Pub/Sub.

    Args:
        topic: nome del topic (es: "crm.lead.events")
        event_type: tipo evento (es: "lead.stage_changed")
        payload: dati dell'evento

    Il messaggio include sempre:
      - event_type
      - occurred_at (ISO UTC)
      - il payload specifico dell'evento
    """
    message = {
        "event_type":  event_type,
        "occurred_at": datetime.now(timezone.utc).isoformat(),
        **payload,
    }
    data = json.dumps(message).encode("utf-8")

    future = publisher.publish(
        _topic_path(topic),
        data=data,
        # Attributi usati per filtrare nei subscriber
        event_type=event_type,
    )
    # Non aspettiamo il future — fire and forget
    # Gli errori sono gestiti dal retry automatico di Pub/Sub

# ── Helper per ogni dominio ──────────────────────────────────────

async def emit_lead_event(event_type: str, lead_id: str, extra: dict = {}):
    await publish_event("crm.lead.events", event_type, {
        "lead_id": lead_id, **extra
    })

async def emit_email_event(event_type: str, email_send_id: str, lead_id: str, extra: dict = {}):
    await publish_event("crm.email.events", event_type, {
        "email_send_id": email_send_id,
        "lead_id": lead_id,
        **extra,
    })

async def emit_score_event(lead_id: str, old_score: int, new_score: int):
    await publish_event("crm.score.events", "score.updated", {
        "lead_id":   lead_id,
        "old_score": old_score,
        "new_score": new_score,
    })

async def emit_inbox_event(event_type: str, conv_id: str, lead_id: str, channel: str):
    await publish_event("crm.inbox.events", event_type, {
        "conversation_id": conv_id,
        "lead_id":         lead_id,
        "channel":         channel,
    })
```

### Aggiornamento `lead_service.py` — emette eventi

```python
# Nel metodo update_stage() di LeadService — AGGIORNATO
async def update_stage(self, lead_id: str, data: LeadStageUpdate, updated_by: str):
    old_lead = await get_document(self.db, "leads", lead_id)
    old_stage = old_lead.get("pipelineStage")

    # Aggiorna Firestore
    updated = await update_document(self.db, "leads", lead_id, {
        "pipelineStage": data.stage,
        "status": data.stage,
    })

    # Logga activity (da Fase 1)
    await append_activity(self.db, lead_id, {
        "type":   "stage_changed",
        "userId": updated_by,
        "title":  f"Spostato da {old_stage} a {data.stage}",
        "metadata": {"from": old_stage, "to": data.stage},
    })

    # ✨ NUOVO Fase 2 — pubblica evento per workflow e scoring
    await emit_lead_event("lead.stage_changed", lead_id, {
        "from_stage":  old_stage,
        "to_stage":    data.stage,
        "updated_by":  updated_by,
    })

    return updated
```

---

## 6. Email sequences — drip campaigns

### `backend/app/services/sequence_service.py`

```python
"""
Gestione sequenze drip email.
- Iscrizione lead a una sequenza
- Calcolo next_send_at per ogni step
- Esecuzione step al momento giusto (chiamato da Cloud Scheduler ogni ora)
"""
from datetime import datetime, timezone, timedelta
from typing import Optional
from google.cloud.firestore_v1 import AsyncClient, FieldFilter, Increment
from app.services.firestore_service import create_document, update_document, new_id, utcnow
from app.services.template_service import render_template
from app.services.email_service import send_email
from app.services.pubsub_service import emit_email_event
import pytz

ITALY_TZ = pytz.timezone("Europe/Rome")

async def enroll_lead(
    db: AsyncClient,
    lead_id: str,
    sequence_id: str,
    trigger_source: str = "manual",
) -> Optional[dict]:
    """
    Iscrive un lead a una sequenza.
    Se la sequenza ha enrollOnce=True e il lead è già iscritto, skippa.
    """
    seq_doc = await db.collection("sequences").document(sequence_id).get()
    if not seq_doc.exists:
        raise ValueError(f"Sequenza {sequence_id} non trovata")

    seq = seq_doc.to_dict()
    if not seq.get("isActive"):
        return None

    # Verifica enrollOnce
    if seq.get("enrollOnce"):
        existing = await db.collection("sequence_enrollments")\
            .where(filter=FieldFilter("leadId", "==", lead_id))\
            .where(filter=FieldFilter("sequenceId", "==", sequence_id))\
            .limit(1).get()
        if list(existing):
            return None  # Già iscritto

    # Recupera primo step per calcolare nextSendAt
    steps = await db.collection("sequences").document(sequence_id)\
        .collection("steps")\
        .order_by("stepNumber")\
        .limit(1).get()

    first_step = steps[0].to_dict() if steps else None
    next_send_at = _calculate_send_time(
        delay_days=first_step.get("delayDays", 0) if first_step else 0,
        delay_hours=first_step.get("delayHours", 0) if first_step else 0,
        preferred_hour=first_step.get("sendAt", "09:00") if first_step else "09:00",
    )

    enrollment = await create_document(db, "sequence_enrollments", {
        "leadId":       lead_id,
        "sequenceId":   sequence_id,
        "currentStep":  0,
        "totalSteps":   seq.get("totalSteps", 0),
        "status":       "active",
        "stopReason":   None,
        "nextSendAt":   next_send_at,
        "enrolledAt":   utcnow(),
        "completedAt":  None,
        "emailsSent":   0,
        "emailsOpened": 0,
        "linksClicked": 0,
        "triggerSource": trigger_source,
    })
    return enrollment

def _calculate_send_time(
    delay_days: int,
    delay_hours: int,
    preferred_hour: str,
    from_time: Optional[datetime] = None,
) -> datetime:
    """
    Calcola il momento esatto di invio rispettando:
    - delay_days e delay_hours dallo step precedente
    - preferred_hour (es "09:00") in timezone Europe/Rome
    - No invio nel weekend (spostato a lunedì se sabato/domenica)
    """
    base = from_time or datetime.now(timezone.utc)
    target = base + timedelta(days=delay_days, hours=delay_hours)

    # Imposta ora preferita in timezone italiana
    hour, minute = map(int, preferred_hour.split(":"))
    target_it = target.astimezone(ITALY_TZ).replace(
        hour=hour, minute=minute, second=0, microsecond=0
    )

    # Sposta al lunedì se weekend
    if target_it.weekday() == 5:   # Sabato
        target_it += timedelta(days=2)
    elif target_it.weekday() == 6:  # Domenica
        target_it += timedelta(days=1)

    return target_it.astimezone(timezone.utc)

async def process_due_enrollments(db: AsyncClient):
    """
    Chiamato ogni ora da Cloud Scheduler.
    Trova enrollment con nextSendAt <= adesso e processa il prossimo step.
    """
    now = utcnow()
    due = await db.collection("sequence_enrollments")\
        .where(filter=FieldFilter("status", "==", "active"))\
        .where(filter=FieldFilter("nextSendAt", "<=", now))\
        .limit(100).get()  # Batch di 100 per run

    for enrollment_snap in due:
        enrollment = {"id": enrollment_snap.id, **enrollment_snap.to_dict()}
        try:
            await _process_enrollment_step(db, enrollment)
        except Exception as e:
            # Log errore ma continua con gli altri
            import logging
            logging.error(f"Errore step enrollment {enrollment['id']}: {e}")

async def _process_enrollment_step(db: AsyncClient, enrollment: dict):
    seq_id    = enrollment["sequenceId"]
    lead_id   = enrollment["leadId"]
    next_step = enrollment["currentStep"] + 1

    # Recupera step
    step_snap = await db.collection("sequences").document(seq_id)\
        .collection("steps")\
        .where(filter=FieldFilter("stepNumber", "==", next_step))\
        .limit(1).get()

    if not step_snap:
        # Sequenza completata
        await update_document(db, "sequence_enrollments", enrollment["id"], {
            "status":      "completed",
            "completedAt": utcnow(),
            "nextSendAt":  None,
        })
        return

    step = step_snap[0].to_dict()

    # Verifica condizione step
    if not await _check_step_condition(db, step, enrollment):
        # Skippa step ma continua alla successiva
        await _advance_to_next_step(db, enrollment, step, skipped=True)
        return

    # Esegui step in base al canale
    if step["channel"] == "email":
        await _send_sequence_email(db, enrollment, step)
    elif step["channel"] == "whatsapp":
        await _send_sequence_whatsapp(db, enrollment, step)
    elif step["channel"] == "task":
        await _create_sequence_task(db, enrollment, step)

    await _advance_to_next_step(db, enrollment, step)

async def _check_step_condition(db: AsyncClient, step: dict, enrollment: dict) -> bool:
    cond = step.get("condition")
    if not cond or cond["type"] == "always":
        return True

    if cond["type"] == "not_opened_prev":
        # Non inviare se ha aperto la email precedente
        return enrollment.get("emailsOpened", 0) == 0

    if cond["type"] == "score_above":
        lead = await db.collection("leads").document(enrollment["leadId"]).get()
        score = lead.to_dict().get("leadScore", 0)
        return score >= cond["value"]

    return True

async def _send_sequence_email(db: AsyncClient, enrollment: dict, step: dict):
    lead = await db.collection("leads").document(enrollment["leadId"]).get()
    lead_data = lead.to_dict()

    # Render template con variabili lead
    from app.services.template_service import render_template
    template = await db.collection("email_templates").document(step["templateId"]).get()
    tpl = template.to_dict()

    rendered = render_template(tpl["bodyHtml"], lead_data)
    subject  = render_template(tpl["subject"], lead_data)

    # Invia via Resend EU + traccia pixel e link
    from app.services.email_service import send_tracked_email
    email_send = await send_tracked_email(
        db=db,
        to=lead_data["email"],
        subject=subject,
        html=rendered,
        lead_id=enrollment["leadId"],
        sequence_id=enrollment["sequenceId"],
        step_id=step.get("id"),
        template_id=step["templateId"],
    )

    # Aggiorna contatore
    await db.collection("sequence_enrollments").document(enrollment["id"]).update({
        "emailsSent": Increment(1),
    })
```

---

## 7. Email tracking — open & click

### `backend/app/routers/tracking.py`

```python
"""
Endpoint pubblici (no auth) per tracking email.
- GET /track/open/{pixel_id}   → 1x1 pixel trasparente
- GET /track/click/{link_id}   → redirect + log click
"""
from fastapi import APIRouter, Response, Request
from fastapi.responses import RedirectResponse
from app.firebase_admin import db
from app.services.pubsub_service import emit_email_event
from app.services.firestore_service import utcnow
from google.cloud.firestore_v1 import FieldFilter, Increment
import base64

router = APIRouter()

# 1x1 pixel GIF trasparente (minimo overhead)
TRACKING_PIXEL = base64.b64decode(
    "R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"
)

@router.get("/open/{pixel_id}", include_in_schema=False)
async def track_open(pixel_id: str, request: Request):
    """
    Chiamato quando il client email carica le immagini.
    Restituisce pixel trasparente 1x1 — registra apertura.
    """
    # Trova email_send dal tracking pixel id
    sends = await db.collection("email_sends")\
        .where(filter=FieldFilter("trackingPixelId", "==", pixel_id))\
        .limit(1).get()

    if sends:
        snap   = sends[0]
        send   = snap.to_dict()
        now    = utcnow()

        updates = {
            "openCount":  Increment(1),
            "status":     "opened",
        }
        if not send.get("openedAt"):
            updates["openedAt"] = now

        await snap.reference.update(updates)

        # Pubblica evento per workflow e scoring
        await emit_email_event(
            "email.opened",
            email_send_id=snap.id,
            lead_id=send["leadId"],
            extra={"is_first_open": not send.get("openedAt")},
        )

    return Response(
        content=TRACKING_PIXEL,
        media_type="image/gif",
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate",
            "Pragma":        "no-cache",
        }
    )

@router.get("/click/{link_id}", include_in_schema=False)
async def track_click(link_id: str, request: Request):
    """
    Ogni link nell'email viene sostituito con questo URL.
    Registra il click e fa redirect all'URL originale.
    """
    # Cerca il link_id in email_sends.trackedLinks
    # trackedLinks è una map: { link_id: original_url }
    sends = await db.collection("email_sends")\
        .where(filter=FieldFilter(f"trackedLinks.{link_id}", "!=", None))\
        .limit(1).get()

    original_url = "https://www.aichainsolutions.net"  # fallback

    if sends:
        snap   = sends[0]
        send   = snap.to_dict()
        original_url = send["trackedLinks"].get(link_id, original_url)
        now    = utcnow()

        updates = {"clickCount": Increment(1), "status": "clicked"}
        if not send.get("clickedAt"):
            updates["clickedAt"] = now

        await snap.reference.update(updates)

        await emit_email_event(
            "email.clicked",
            email_send_id=snap.id,
            lead_id=send["leadId"],
            extra={"link_id": link_id, "original_url": original_url},
        )

    return RedirectResponse(url=original_url, status_code=302)
```

### `backend/app/services/email_service.py` — send con tracking

```python
import re
import uuid
import resend
from app.config import settings
from app.services.firestore_service import create_document, utcnow, new_id

resend.api_key = settings.RESEND_API_KEY
RESEND_EU_BASE = "https://api.eu.resend.com"  # Endpoint EU — dati restano in Europa

TRACKING_BASE = "https://crm.aichainsolutions.net/track"

def _inject_tracking_pixel(html: str, pixel_id: str) -> str:
    """Inietta il pixel di tracking prima del tag </body>"""
    pixel_tag = f'<img src="{TRACKING_BASE}/open/{pixel_id}" width="1" height="1" style="display:none" aria-hidden="true" />'
    return html.replace("</body>", f"{pixel_tag}</body>") if "</body>" in html else html + pixel_tag

def _replace_links(html: str) -> tuple[str, dict[str, str]]:
    """
    Sostituisce ogni href con un link di tracking.
    Ritorna HTML modificato + mappa { link_id: original_url }
    """
    tracked_links: dict[str, str] = {}
    link_pattern = re.compile(r'href="(https?://[^"]+)"', re.IGNORECASE)

    def replace_link(match: re.Match) -> str:
        original_url = match.group(1)
        # Non tracciare il pixel stesso o link di disiscrizione
        if "/track/" in original_url or "unsubscribe" in original_url:
            return match.group(0)
        link_id = new_id()
        tracked_links[link_id] = original_url
        return f'href="{TRACKING_BASE}/click/{link_id}"'

    modified_html = link_pattern.sub(replace_link, html)
    return modified_html, tracked_links

async def send_tracked_email(
    db,
    to: str,
    subject: str,
    html: str,
    lead_id: str,
    sequence_id: str = None,
    step_id: str = None,
    template_id: str = None,
) -> dict:
    """
    Invia email tramite Resend EU e crea record di tracking in Firestore.
    """
    pixel_id = new_id()
    html_with_pixel = _inject_tracking_pixel(html, pixel_id)
    html_with_links, tracked_links = _replace_links(html_with_pixel)

    # Invia via Resend (endpoint EU)
    response = resend.Emails.send({
        "from":    f"{settings.EMAIL_FROM_NAME} <{settings.EMAIL_FROM}>",
        "to":      [to],
        "subject": subject,
        "html":    html_with_links,
    })

    # Crea record tracking in Firestore
    email_send = await create_document(db, "email_sends", {
        "leadId":          lead_id,
        "sequenceId":      sequence_id,
        "stepId":          step_id,
        "templateId":      template_id,
        "resendId":        response["id"],
        "to":              to,
        "subject":         subject,
        "status":          "sent",
        "openedAt":        None,
        "openCount":       0,
        "clickedAt":       None,
        "clickCount":      0,
        "bouncedAt":       None,
        "trackingPixelId": pixel_id,
        "trackedLinks":    tracked_links,
    })

    return email_send
```

---

## 8. Template engine

### `backend/app/services/template_service.py`

```python
"""
Render di template email con variabili lead.
Usa Jinja2-like syntax: {{variableName}}
"""
import re
from typing import Any

# Variabili disponibili nei template e loro fonte
TEMPLATE_VARIABLES = {
    "firstName":      lambda l: l.get("firstName", ""),
    "lastName":       lambda l: l.get("lastName", ""),
    "fullName":       lambda l: f"{l.get('firstName','')} {l.get('lastName','')}".strip(),
    "companyName":    lambda l: l.get("companyName", "la tua azienda"),
    "roleTitle":      lambda l: l.get("roleTitle", ""),
    "industry":       lambda l: _industry_label(l.get("industry")),
    "leadScore":      lambda l: str(l.get("leadScore", 0)),
    "roiEstimate":    lambda l: _estimate_roi(l),   # Calcolo automatico
    "hoursSaved":     lambda l: _estimate_hours(l), # Stima ore risparmiate
    "assessmentUrl":  lambda l: "https://www.aichainsolutions.net/ai-readiness-assessment",
    "bookingUrl":     lambda l: "https://calendar.aichainsolutions.net",
    "unsubscribeUrl": lambda l: f"https://crm.aichainsolutions.net/unsubscribe/{l.get('id','')}",
}

def render_template(template_str: str, lead_data: dict[str, Any]) -> str:
    """
    Sostituisce {{variableName}} con il valore corrispondente del lead.
    Variabili non riconosciute vengono lasciate invariate (non crashano).
    """
    def replace_var(match: re.Match) -> str:
        var_name = match.group(1).strip()
        if var_name in TEMPLATE_VARIABLES:
            try:
                return str(TEMPLATE_VARIABLES[var_name](lead_data))
            except Exception:
                return ""
        return match.group(0)  # Lascia invariato se variabile sconosciuta

    return re.sub(r"\{\{(\w+)\}\}", replace_var, template_str)

def _industry_label(industry: str | None) -> str:
    labels = {
        "legal":         "studi legali",
        "finance":       "finance",
        "manufacturing": "manifattura",
        "insurance":     "assicurazioni",
    }
    return labels.get(industry or "", "aziende")

def _estimate_roi(lead: dict) -> str:
    """Calcola ROI stimato in base alle dimensioni dell'azienda"""
    size = lead.get("companySize", "")
    roi_map = {
        "1-10":    "€8.000",
        "11-50":   "€24.000",
        "51-200":  "€72.000",
        "201-500": "€180.000",
        "500+":    "€400.000+",
    }
    return roi_map.get(size, "significativo")

def _estimate_hours(lead: dict) -> str:
    """Stima ore risparmiate mensili"""
    size = lead.get("companySize", "")
    hours_map = {
        "1-10":    "40",
        "11-50":   "160",
        "51-200":  "480",
        "201-500": "1.200",
        "500+":    "3.000+",
    }
    return hours_map.get(size, "centinaia di")

def extract_variables(template_str: str) -> list[str]:
    """Estrae lista variabili usate in un template (per UI editor)"""
    matches = re.findall(r"\{\{(\w+)\}\}", template_str)
    return list(set(matches))
```

---

## 9. Workflow builder

### `backend/workers/workflow_worker/handlers.py`

```python
"""
WorkflowWorker — riceve eventi da Pub/Sub e valuta i workflow attivi.
Ogni evento passa attraverso tutti i workflow attivi con trigger compatibile.
"""
import json
import base64
from fastapi import APIRouter, Request
from google.cloud.firestore_v1 import FieldFilter, Increment
from app.firebase_admin import db
from app.services import sequence_service, email_service
from app.services.firestore_service import create_document, update_document, utcnow, new_id

router = APIRouter()

@router.post("/pubsub/lead")
async def handle_lead_event(request: Request):
    """Riceve eventi crm.lead.events da Pub/Sub"""
    envelope = await request.json()
    message = json.loads(base64.b64decode(envelope["message"]["data"]))

    event_type = message["event_type"]
    lead_id    = message["lead_id"]

    # Trova workflow con trigger compatibile
    await _evaluate_workflows(event_type, lead_id, message)
    return {"status": "ok"}

@router.post("/pubsub/email")
async def handle_email_event(request: Request):
    """Riceve eventi crm.email.events — aggiorna scoring e sequenze"""
    envelope = await request.json()
    message = json.loads(base64.b64decode(envelope["message"]["data"]))

    event_type    = message["event_type"]
    lead_id       = message["lead_id"]
    email_send_id = message["email_send_id"]

    # Aggiorna scoring per apertura/click email
    await _evaluate_workflows(event_type, lead_id, message)

    # Controlla se fermare la sequenza (es: ha risposto)
    if event_type == "email.replied":
        await _stop_active_sequences(lead_id, "replied")

    return {"status": "ok"}

async def _evaluate_workflows(event_type: str, lead_id: str, context: dict):
    """
    Valuta tutti i workflow attivi con trigger compatibile.
    Esegue le azioni se le condizioni sono soddisfatte.
    """
    # Recupera lead
    lead_snap = await db.collection("leads").document(lead_id).get()
    if not lead_snap.exists:
        return
    lead = {"id": lead_id, **lead_snap.to_dict()}

    # Trova workflow con questo trigger
    # Nota: Firestore non supporta query su array nested complessi —
    # usiamo un campo "triggerEvent" flat per l'indice
    workflows = await db.collection("workflows")\
        .where(filter=FieldFilter("isActive", "==", True))\
        .where(filter=FieldFilter("trigger.event", "==", _normalize_trigger(event_type)))\
        .get()

    for wf_snap in workflows:
        wf = {"id": wf_snap.id, **wf_snap.to_dict()}

        # Valuta filtri del trigger
        if not _evaluate_filters(lead, wf["trigger"].get("filters", []), context):
            continue

        # Esegui azioni
        await _execute_actions(lead, wf["actions"], context)

        # Incrementa contatore esecuzioni
        await wf_snap.reference.update({"executionCount": Increment(1)})

def _normalize_trigger(event_type: str) -> str:
    """Mappa event_type Pub/Sub → trigger nome workflow"""
    mapping = {
        "lead.stage_changed":  "stage_changed",
        "lead.created":        "lead_created",
        "lead.updated":        "lead_updated",
        "email.opened":        "email_opened",
        "email.clicked":       "email_clicked",
        "form.submitted":      "form_submitted",
        "score.updated":       "score_changed",
        "booking.created":     "booking_created",
        "whatsapp.received":   "whatsapp_received",
    }
    return mapping.get(event_type, event_type)

def _evaluate_filters(lead: dict, filters: list, context: dict) -> bool:
    """Valuta tutti i filtri del trigger — devono essere tutti veri (AND)"""
    for f in filters:
        field    = f["field"]
        operator = f["operator"]
        value    = f["value"]

        # Supporta campi nested con dot notation: "utm.source"
        lead_value = lead
        for key in field.split("."):
            if isinstance(lead_value, dict):
                lead_value = lead_value.get(key)
            else:
                lead_value = None
                break

        if not _compare(lead_value, operator, value):
            return False
    return True

def _compare(actual, operator: str, expected) -> bool:
    if actual is None:
        return operator in ("!=", "not_in")
    ops = {
        "==":       lambda a, b: a == b,
        "!=":       lambda a, b: a != b,
        ">":        lambda a, b: a > b,
        "<":        lambda a, b: a < b,
        ">=":       lambda a, b: a >= b,
        "<=":       lambda a, b: a <= b,
        "in":       lambda a, b: a in b,
        "not_in":   lambda a, b: a not in b,
        "contains": lambda a, b: b in str(a),
    }
    return ops.get(operator, lambda a, b: False)(actual, expected)

async def _execute_actions(lead: dict, actions: list, context: dict):
    """Esegue le azioni del workflow in sequenza"""
    for action in actions:
        action_type = action["type"]
        cfg         = action.get("config", {})

        if action_type == "assign_lead":
            assign_to = cfg.get("assignTo")
            if assign_to == "round_robin":
                assign_to = await _get_round_robin_assignee(db)
            await db.collection("leads").document(lead["id"]).update({
                "assignedTo": assign_to, "updatedAt": utcnow()
            })

        elif action_type == "change_stage":
            await db.collection("leads").document(lead["id"]).update({
                "pipelineStage": cfg["stage"],
                "status":        cfg["stage"],
                "updatedAt":     utcnow(),
            })

        elif action_type == "add_tag":
            from google.cloud.firestore_v1 import ArrayUnion
            await db.collection("leads").document(lead["id"]).update({
                "tags": ArrayUnion([cfg["tag"]])
            })

        elif action_type == "enroll_sequence":
            await sequence_service.enroll_lead(
                db, lead["id"], cfg["sequenceId"], trigger_source="workflow"
            )

        elif action_type == "create_task":
            from datetime import timedelta
            due = utcnow() + timedelta(days=cfg.get("dueInDays", 1))
            await create_document(db, f"leads/{lead['id']}/tasks", {
                "leadId":      lead["id"],
                "assignedTo":  cfg.get("assignTo", lead.get("assignedTo")),
                "createdBy":   "system",
                "title":       cfg["title"].replace("{{firstName}}", lead.get("firstName", "")),
                "type":        cfg.get("type", "followup"),
                "priority":    cfg.get("priority", "medium"),
                "dueDate":     due,
                "completedAt": None,
            })

        elif action_type == "send_email":
            template = await db.collection("email_templates").document(cfg["templateId"]).get()
            tpl = template.to_dict()
            rendered = render_template(tpl["bodyHtml"], lead)
            subject  = render_template(tpl["subject"], lead)
            await email_service.send_tracked_email(
                db, to=lead["email"], subject=subject, html=rendered,
                lead_id=lead["id"], template_id=cfg["templateId"],
            )

        elif action_type == "webhook":
            import httpx
            async with httpx.AsyncClient(timeout=10) as client:
                await client.request(
                    method=cfg.get("method", "POST"),
                    url=cfg["url"],
                    headers=cfg.get("headers", {}),
                    json={**cfg.get("body", {}), "lead_id": lead["id"]},
                )
```

---

## 10. Lead scoring avanzato

### `backend/app/services/scoring_service.py` — v2

```python
"""
Scoring Engine v2 — Fase 2
Aggiunge: decay temporale, behavioral momentum, email engagement score.
"""
from datetime import datetime, timezone, timedelta
from google.cloud.firestore_v1 import AsyncClient, FieldFilter
from app.services.firestore_service import utcnow
from app.services.pubsub_service import emit_score_event

# ── Punteggi base per azione ─────────────────────────────────
ACTION_WEIGHTS = {
    # Form & contenuti
    "form_submitted":        10,
    "playbook_download":     15,
    "assessment":            20,
    "trial_request":         25,
    # Email engagement
    "email_opened":           8,
    "email_clicked":         12,
    "email_replied":         30,   # Alto valore — risposta diretta
    # Navigazione sito
    "page_visited":           3,
    "pricing_page":          15,
    "demo_page":             10,
    "case_study_page":        8,
    # Call & booking
    "booking_created":       25,
    "booking_attended":      35,
    "demo_completed":        40,
    # WhatsApp
    "whatsapp_replied":      20,
}

# ── Profilo demografico ───────────────────────────────────────
PROFILE_WEIGHTS = {
    "seniority": {"c_level": 30, "director": 20, "manager": 10, "staff": 5},
    "industry":  {"legal": 20, "finance": 20, "insurance": 15, "manufacturing": 10, "other": 0},
    "size":      {"500+": 20, "201-500": 15, "51-200": 12, "11-50": 5, "1-10": 0},
}

# ── Decay: le azioni vecchie valgono meno ────────────────────
DECAY_HALF_LIFE_DAYS = 30  # Dopo 30 giorni, l'azione vale il 50%

def _apply_decay(score: float, event_date: datetime) -> float:
    """Decay esponenziale: punteggio si dimezza ogni DECAY_HALF_LIFE_DAYS giorni"""
    now      = datetime.now(timezone.utc)
    age_days = max(0, (now - event_date).days)
    factor   = 0.5 ** (age_days / DECAY_HALF_LIFE_DAYS)
    return score * factor

async def calculate_lead_score_v2(lead_id: str, db: AsyncClient) -> int:
    """
    Calcola score v2 con:
    1. Punteggio demografico (statico)
    2. Punteggio comportamentale con decay temporale
    3. Email engagement momentum (ultime 7 giorni)
    """
    lead_snap = await db.collection("leads").document(lead_id).get()
    if not lead_snap.exists:
        return 0

    lead  = lead_snap.to_dict()
    score = 0.0
    old_score = lead.get("leadScore", 0)

    # ── 1. Punteggio demografico (no decay) ─────────────────
    score += PROFILE_WEIGHTS["seniority"].get(lead.get("roleSeniority", ""), 0)
    score += PROFILE_WEIGHTS["industry"].get(lead.get("industry", ""), 0)
    score += PROFILE_WEIGHTS["size"].get(lead.get("companySize", ""), 0)

    # ── 2. Punteggio comportamentale con decay ───────────────
    activities = await db.collection("leads").document(lead_id)\
        .collection("activities")\
        .order_by("createdAt", direction="DESCENDING")\
        .limit(200).get()

    for act_snap in activities:
        act       = act_snap.to_dict()
        act_type  = act.get("type", "")
        act_time  = act.get("createdAt")

        # Gestisce pagine ad alto intento
        if act_type == "page_visited":
            url = (act.get("metadata") or {}).get("url", "")
            if "pricing" in url or "prezzi" in url:
                act_type = "pricing_page"
            elif "/demo" in url:
                act_type = "demo_page"
            elif "case-stud" in url or "testimon" in url:
                act_type = "case_study_page"

        base = ACTION_WEIGHTS.get(act_type, 0)
        if base > 0 and act_time:
            score += _apply_decay(base, act_time.replace(tzinfo=timezone.utc)
                                  if act_time.tzinfo is None else act_time)

    # ── 3. Email engagement momentum (bonus ultime 2 settimane) ──
    cutoff = utcnow() - timedelta(days=14)
    recent_emails = await db.collection("email_sends")\
        .where(filter=FieldFilter("leadId", "==", lead_id))\
        .where(filter=FieldFilter("createdAt", ">=", cutoff))\
        .get()

    recent_opens  = sum(1 for e in recent_emails if e.to_dict().get("openedAt"))
    recent_clicks = sum(1 for e in recent_emails if e.to_dict().get("clickedAt"))

    if recent_opens >= 3:   score += 15   # Molto attivo nelle ultime 2 settimane
    elif recent_opens >= 1: score += 8
    if recent_clicks >= 2:  score += 10

    # Normalizza 0–100
    final_score = min(100, int(score))

    # Persisti e pubblica evento se cambiato
    if final_score != old_score:
        await db.collection("leads").document(lead_id).update({
            "leadScore":   final_score,
            "isQualified": final_score >= 60,
            "updatedAt":   utcnow(),
        })
        await emit_score_event(lead_id, old_score, final_score)

    return final_score
```

---

## 11. Visitor tracking

### `visitor-tracker/tracker.js`

```javascript
/**
 * AiChain CRM Visitor Tracker
 * Script leggero (<3KB gzipped) da includere nel sito aichainsolutions.net
 * Identifica visitatori noti e traccia page views nel CRM.
 *
 * Uso: <script src="https://crm.aichainsolutions.net/tracker.js" async></script>
 */
(function() {
  'use strict';

  const CRM_ENDPOINT = 'https://crm-backend-HASH-ew.a.run.app/api/v1/tracking/pageview';
  const COOKIE_KEY   = 'aichain_vid';
  const SESSION_KEY  = 'aichain_session';

  // Recupera o crea visitor ID (persistente in cookie)
  function getVisitorId() {
    const existing = getCookie(COOKIE_KEY);
    if (existing) return existing;
    const vid = crypto.randomUUID ? crypto.randomUUID() : Math.random().toString(36).slice(2);
    setCookie(COOKIE_KEY, vid, 365);
    return vid;
  }

  // Recupera email dal localStorage (impostata dopo submit form)
  function getKnownEmail() {
    try { return localStorage.getItem('aichain_lead_email') || null; }
    catch(e) { return null; }
  }

  // Tempo sulla pagina
  let pageStartTime = Date.now();

  function trackPageView() {
    const payload = {
      visitor_id:   getVisitorId(),
      email:        getKnownEmail(),          // null se visitatore anonimo
      url:          window.location.href,
      title:        document.title,
      referrer:     document.referrer,
      utm: {
        source:   getUrlParam('utm_source'),
        medium:   getUrlParam('utm_medium'),
        campaign: getUrlParam('utm_campaign'),
        content:  getUrlParam('utm_content'),
      },
      screen: {
        width:  screen.width,
        height: screen.height,
      },
      occurred_at: new Date().toISOString(),
    };

    // Fire-and-forget — non blocca il sito
    if (navigator.sendBeacon) {
      navigator.sendBeacon(CRM_ENDPOINT, JSON.stringify(payload));
    } else {
      fetch(CRM_ENDPOINT, {
        method:  'POST',
        body:    JSON.stringify(payload),
        headers: { 'Content-Type': 'application/json' },
        keepalive: true,
      }).catch(() => {});
    }
  }

  // Traccia durata alla navigazione via
  window.addEventListener('visibilitychange', function() {
    if (document.visibilityState === 'hidden') {
      const duration = Math.round((Date.now() - pageStartTime) / 1000);
      if (duration > 3) {  // Ignora bounce < 3s
        navigator.sendBeacon(CRM_ENDPOINT + '/duration', JSON.stringify({
          visitor_id:       getVisitorId(),
          url:              window.location.href,
          duration_seconds: duration,
        }));
      }
    }
  });

  // Esegui al caricamento
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', trackPageView);
  } else {
    trackPageView();
  }

  // Helper
  function getUrlParam(name) {
    return new URLSearchParams(window.location.search).get(name);
  }
  function getCookie(name) {
    const match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'));
    return match ? match[2] : null;
  }
  function setCookie(name, value, days) {
    const expires = new Date(Date.now() + days * 864e5).toUTCString();
    document.cookie = name + '=' + value + '; expires=' + expires + '; path=/; SameSite=Lax';
  }
})();
```

### `backend/app/routers/tracking.py` — pageview endpoint

```python
@router.post("/pageview")
async def track_pageview(request: Request):
    """
    Riceve page views dal visitor tracker JS.
    Se email è presente → logga activity sul lead noto.
    Se solo visitor_id → salva in session anonima (per matching futuro).
    """
    data = await request.json()
    email      = data.get("email")
    visitor_id = data.get("visitor_id")
    url        = data.get("url", "")

    if email:
        # Trova lead per email
        leads = await db.collection("leads")\
            .where(filter=FieldFilter("email", "==", email))\
            .where(filter=FieldFilter("deletedAt", "==", None))\
            .limit(1).get()

        if leads:
            lead_id = leads[0].id
            activity_type = "page_visited"

            # Aggiungi metadata pagina con intent score
            await append_activity(db, lead_id, {
                "type":   activity_type,
                "userId": None,  # Automatico
                "title":  f"Visitato: {data.get('title', url)}",
                "metadata": {
                    "url":      url,
                    "referrer": data.get("referrer"),
                    "utm":      data.get("utm", {}),
                },
            })

            # Pubblica evento per scoring
            await publish_event("crm.score.events", "page.visited", {
                "lead_id": lead_id,
                "url":     url,
            })

    return Response(status_code=204)
```

---

## 12. Segmentazione dinamica

### `backend/app/services/segment_service.py`

```python
"""
Segmenti dinamici — ricalcolati ogni notte da Cloud Scheduler.
Ogni segmento ha regole (field, operator, value) valutate su tutti i lead attivi.
"""
from google.cloud.firestore_v1 import AsyncClient, FieldFilter
from app.services.firestore_service import update_document, utcnow, new_id

async def evaluate_all_segments(db: AsyncClient):
    """
    Chiamato da Cloud Scheduler ogni notte alle 02:00.
    Aggiorna le membership di tutti i segmenti attivi.
    """
    segments = await db.collection("segments")\
        .where(filter=FieldFilter("isActive", "==", True))\
        .where(filter=FieldFilter("isDynamic", "==", True))\
        .get()

    for seg_snap in segments:
        seg = {"id": seg_snap.id, **seg_snap.to_dict()}
        member_ids = await _evaluate_segment(db, seg)

        # Aggiorna memberships (batch write)
        batch = db.batch()
        await _sync_memberships(db, batch, seg["id"], member_ids)

        await update_document(db, "segments", seg["id"], {
            "memberCount":     len(member_ids),
            "lastEvaluatedAt": utcnow(),
        })

async def _evaluate_segment(db: AsyncClient, segment: dict) -> list[str]:
    """Ritorna lista di lead_id che appartengono al segmento"""
    rules    = segment.get("rules", {})
    operator = rules.get("operator", "AND")
    conditions = rules.get("conditions", [])

    if not conditions:
        return []

    # Costruisce query Firestore per la prima condizione (le altre vengono filtrate in Python)
    # Firestore supporta max 1 disuguaglianza (<, >, <=, >=) per query
    # Per logica complessa usiamo la prima condizione come filtro Firestore
    # e le altre le valutiamo in Python
    query = db.collection("leads")\
        .where(filter=FieldFilter("deletedAt", "==", None))

    first_cond = conditions[0]
    if first_cond["operator"] == "==":
        query = query.where(
            filter=FieldFilter(first_cond["field"], "==", first_cond["value"])
        )

    leads = await query.get()
    result = []

    for lead_snap in leads:
        lead = {"id": lead_snap.id, **lead_snap.to_dict()}

        if operator == "AND":
            matches = all(_eval_condition(lead, c) for c in conditions)
        else:  # OR
            matches = any(_eval_condition(lead, c) for c in conditions)

        if matches:
            result.append(lead["id"])

    return result

def _eval_condition(lead: dict, condition: dict) -> bool:
    field    = condition["field"]
    operator = condition["operator"]
    value    = condition["value"]

    # Supporta dot notation per campi nested
    actual = lead
    for key in field.split("."):
        actual = actual.get(key) if isinstance(actual, dict) else None

    if actual is None:
        return operator in ("!=", "not_in")

    ops = {
        "==":     actual == value,
        "!=":     actual != value,
        ">":      actual > value,
        "<":      actual < value,
        ">=":     actual >= value,
        "<=":     actual <= value,
        "in":     actual in value,
        "not_in": actual not in value,
    }
    return ops.get(operator, False)
```

---

## 13. WhatsApp Business API

### Setup Meta Cloud API

```bash
# Prerequisiti:
# 1. Account Meta Business Manager verificato
# 2. WhatsApp Business Account (WABA) approvato
# 3. Numero di telefono business verificato
# 4. Template messaggi approvati da Meta

# Configura webhook endpoint in Meta Developer Dashboard:
# URL: https://crm-backend-HASH-ew.a.run.app/api/v1/whatsapp/webhook
# Verify Token: WHATSAPP_VERIFY_TOKEN (da Secret Manager)
```

### `backend/app/routers/whatsapp.py`

```python
from fastapi import APIRouter, Request, Response, HTTPException
from app.firebase_admin import db
from app.services.whatsapp_service import WhatsAppService
from app.services.firestore_service import create_document, update_document, utcnow, new_id
from app.services.pubsub_service import emit_inbox_event
from app.config import settings

router = APIRouter()

@router.get("/webhook")
async def verify_webhook(request: Request):
    """
    Meta verifica il webhook con questa request GET al momento della configurazione.
    """
    params = request.query_params
    if (params.get("hub.mode") == "subscribe" and
        params.get("hub.verify_token") == settings.WHATSAPP_VERIFY_TOKEN):
        return Response(content=params.get("hub.challenge"), media_type="text/plain")
    raise HTTPException(403, "Verifica webhook fallita")

@router.post("/webhook")
async def receive_whatsapp(request: Request):
    """
    Riceve tutti gli eventi WhatsApp da Meta (messaggi in entrata, status, ecc.)
    Risponde SEMPRE 200 subito — elaborazione in background.
    """
    payload = await request.json()

    # Processa in background
    import asyncio
    asyncio.create_task(_process_whatsapp_event(payload))

    return Response(status_code=200)  # Meta richiede risposta < 20s

async def _process_whatsapp_event(payload: dict):
    try:
        for entry in payload.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})

                # Messaggi in entrata
                for message in value.get("messages", []):
                    await _handle_inbound_message(message, value.get("contacts", []))

                # Status update (delivered, read, failed)
                for status in value.get("statuses", []):
                    await _handle_status_update(status)
    except Exception as e:
        import logging
        logging.error(f"Errore processing WhatsApp event: {e}")

async def _handle_inbound_message(message: dict, contacts: list):
    wa_id    = message.get("from")      # Numero WhatsApp mittente
    msg_id   = message.get("id")
    msg_type = message.get("type")      # "text" | "image" | "document" | ...

    # Estrai testo
    body = ""
    if msg_type == "text":
        body = message.get("text", {}).get("body", "")
    elif msg_type == "button":
        body = message.get("button", {}).get("text", "")

    # Trova o crea conversazione per questo numero
    conv = await _get_or_create_conversation(wa_id, contacts)

    # Crea messaggio
    await db.collection("conversations").document(conv["id"])\
        .collection("messages").document(new_id()).set({
        "convId":            conv["id"],
        "direction":         "inbound",
        "channel":           "whatsapp",
        "fromAddress":       wa_id,
        "toAddress":         settings.WHATSAPP_PHONE_NUMBER,
        "body":              body,
        "bodyHtml":          None,
        "attachments":       [],
        "status":            "delivered",
        "whatsappMessageId": msg_id,
        "resendId":          None,
        "emailSendId":       None,
        "sentBy":            None,
        "createdAt":         utcnow(),
    })

    # Aggiorna conversazione
    await db.collection("conversations").document(conv["id"]).update({
        "lastMessageAt":      utcnow(),
        "lastMessagePreview": body[:100],
        "unreadCount":        __import__('google.cloud.firestore_v1', fromlist=['Increment']).Increment(1),
        "status":             "open",
    })

    # Pubblica evento per workflow
    await emit_inbox_event("whatsapp.received", conv["id"], conv["leadId"], "whatsapp")

async def _get_or_create_conversation(wa_phone: str, contacts: list) -> dict:
    """Trova conversazione esistente per numero WhatsApp o ne crea una nuova"""
    existing = await db.collection("conversations")\
        .where(filter=FieldFilter("whatsappPhone", "==", wa_phone))\
        .where(filter=FieldFilter("channel", "==", "whatsapp"))\
        .limit(1).get()

    if existing:
        return {"id": existing[0].id, **existing[0].to_dict()}

    # Cerca lead per numero telefono
    lead_id = None
    phone_clean = wa_phone.replace("+", "").replace(" ", "")
    leads = await db.collection("leads")\
        .where(filter=FieldFilter("phone", ">=", wa_phone))\
        .limit(1).get()
    if leads:
        lead_id = leads[0].id

    conv_name = contacts[0].get("profile", {}).get("name", wa_phone) if contacts else wa_phone

    return await create_document(db, "conversations", {
        "leadId":             lead_id,
        "channel":            "whatsapp",
        "status":             "open",
        "assignedTo":         None,
        "subject":            None,
        "lastMessageAt":      utcnow(),
        "lastMessagePreview": "",
        "unreadCount":        0,
        "whatsappPhone":      wa_phone,
        "contactName":        conv_name,
    })
```

### `backend/app/services/whatsapp_service.py`

```python
"""
Invio messaggi WhatsApp tramite Meta Cloud API.
Usa solo template pre-approvati — obbligatorio per primo contatto.
"""
import httpx
from app.config import settings

META_API_URL = f"https://graph.facebook.com/v20.0/{settings.WHATSAPP_PHONE_NUMBER_ID}"
HEADERS = {
    "Authorization": f"Bearer {settings.WHATSAPP_API_TOKEN}",
    "Content-Type":  "application/json",
}

class WhatsAppService:

    @staticmethod
    async def send_template(
        to_phone: str,
        template_name: str,
        language: str = "it",
        components: list = None,
    ) -> dict:
        """
        Invia template pre-approvato da Meta.
        Obbligatorio per il primo messaggio a un contatto.
        """
        payload = {
            "messaging_product": "whatsapp",
            "to":                to_phone,
            "type":              "template",
            "template": {
                "name":     template_name,
                "language": {"code": language},
                "components": components or [],
            }
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{META_API_URL}/messages",
                headers=HEADERS,
                json=payload,
                timeout=10,
            )
            response.raise_for_status()
            return response.json()

    @staticmethod
    async def send_text(to_phone: str, body: str) -> dict:
        """
        Invia testo libero — solo se la finestra di 24h è aperta
        (il contatto ha scritto nelle ultime 24h).
        """
        payload = {
            "messaging_product": "whatsapp",
            "to":                to_phone,
            "type":              "text",
            "text":              {"body": body},
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{META_API_URL}/messages",
                headers=HEADERS,
                json=payload,
                timeout=10,
            )
            response.raise_for_status()
            return response.json()

# ── Template predefiniti per Fase 2 ─────────────────────────────
# (devono essere approvati su Meta Business Manager prima dell'uso)

TEMPLATES = {
    "booking_reminder": {
        "name":       "crm_booking_reminder",
        "components": [
            {
                "type": "body",
                "parameters": [
                    {"type": "text", "text": "{{firstName}}"},
                    {"type": "text", "text": "{{date}}"},
                    {"type": "text", "text": "{{time}}"},
                ]
            }
        ]
    },
    "booking_confirm": {
        "name":       "crm_booking_confirm",
        "components": []
    },
    "demo_followup": {
        "name":       "crm_demo_followup",
        "components": []
    },
}
```

---

## 14. Inbox unificata — real-time

### Firebase Realtime Database per notifiche istantanee

```
# Struttura Realtime DB (separata da Firestore — per velocità real-time)
realtime-db-root/
└── inbox_notifications/
    └── {uid}/                    # uid del membro del team CRM
        └── {notification_id}/
            ├── type: "new_message" | "new_lead" | "score_alert"
            ├── convId: string
            ├── leadId: string
            ├── preview: string
            ├── channel: "email" | "whatsapp"
            └── createdAt: number (timestamp ms)
```

### `frontend/hooks/useInbox.ts`

```typescript
"use client"
import { useState, useEffect } from "react"
import { ref, onValue, query, orderByChild, limitToLast } from "firebase/database"
import { realtimeDb } from "@/lib/firebase"
import { useAuth } from "./useAuth"
import { useQuery } from "@tanstack/react-query"
import { api } from "@/lib/api"

export interface Conversation {
  id:                  string
  leadId:              string
  channel:             "email" | "whatsapp"
  status:              "open" | "resolved" | "waiting"
  lastMessageAt:       string
  lastMessagePreview:  string
  unreadCount:         number
  whatsappPhone:       string | null
  contactName:         string | null
}

export function useInboxNotifications() {
  const { user } = useAuth()
  const [notifications, setNotifications] = useState<any[]>([])
  const [unreadCount, setUnreadCount]     = useState(0)

  useEffect(() => {
    if (!user) return

    const notifRef = query(
      ref(realtimeDb, `inbox_notifications/${user.uid}`),
      orderByChild("createdAt"),
      limitToLast(20),
    )

    const unsub = onValue(notifRef, (snapshot) => {
      const data = snapshot.val()
      if (!data) {
        setNotifications([])
        setUnreadCount(0)
        return
      }
      const items = Object.entries(data)
        .map(([id, val]: any) => ({ id, ...val }))
        .sort((a, b) => b.createdAt - a.createdAt)

      setNotifications(items)
      setUnreadCount(items.filter(n => !n.readAt).length)
    })

    return unsub
  }, [user?.uid])

  return { notifications, unreadCount }
}

export function useConversations(channel?: "email" | "whatsapp") {
  return useQuery({
    queryKey: ["conversations", channel],
    queryFn: () => api.get("/inbox/conversations", { params: { channel } }).then(r => r.data),
    refetchInterval: 30_000,  // Polling ogni 30s come fallback al real-time
  })
}

export function useConversationMessages(convId: string) {
  return useQuery({
    queryKey: ["conversation", convId, "messages"],
    queryFn: () => api.get(`/inbox/conversations/${convId}/messages`).then(r => r.data),
    enabled: !!convId,
    staleTime: 5_000,
  })
}
```

---

## 15. Preventivi & offerte PDF

### `backend/app/services/pdf_service.py`

```python
"""
Generazione preventivi PDF con WeasyPrint.
Il PDF viene caricato su Firebase Storage e tracciato in Firestore.
"""
from weasyprint import HTML, CSS
from jinja2 import Environment, BaseLoader
from app.firebase_admin import bucket
from app.services.firestore_service import update_document, utcnow, new_id
from datetime import datetime, timezone
import io

PROPOSAL_HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="it">
<head>
  <meta charset="UTF-8">
  <style>
    @page { size: A4; margin: 2cm; }
    body   { font-family: 'Helvetica Neue', sans-serif; color: #111; font-size: 11pt; }
    .header { display: flex; justify-content: space-between; margin-bottom: 2cm; }
    .logo   { font-size: 20pt; font-weight: 700; color: #0047FF; }
    .meta   { text-align: right; color: #666; font-size: 9pt; }
    h1      { font-size: 18pt; margin: 1cm 0 0.5cm; }
    .client-box { background: #f8f8f8; padding: 1cm; border-radius: 4px; margin-bottom: 1cm; }
    table   { width: 100%; border-collapse: collapse; margin-bottom: 1cm; }
    th      { background: #0047FF; color: #fff; padding: 8px 12px; text-align: left; font-size: 9pt; }
    td      { padding: 8px 12px; border-bottom: 0.5pt solid #eee; font-size: 9pt; }
    .total-row td { font-weight: 700; font-size: 11pt; border-top: 1pt solid #111; }
    .footer { margin-top: 2cm; font-size: 8pt; color: #999; text-align: center; }
    .validity { color: #E24B4A; font-size: 9pt; margin-top: 0.5cm; }
  </style>
</head>
<body>
  <div class="header">
    <div class="logo">AiChain Solutions</div>
    <div class="meta">
      <div>Preventivo #{{ proposal.id[:8].upper() }}</div>
      <div>{{ proposal.createdAt.strftime('%d/%m/%Y') }}</div>
      <div>P.IVA IT06230770874</div>
    </div>
  </div>

  <div class="client-box">
    <strong>Destinatario:</strong><br>
    {{ lead.companyName }}<br>
    Att. {{ lead.firstName }} {{ lead.lastName }}<br>
    {{ lead.email }}
  </div>

  <h1>{{ proposal.title }}</h1>

  <table>
    <thead>
      <tr>
        <th style="width:40%">Prodotto / Servizio</th>
        <th style="width:30%">Descrizione</th>
        <th style="width:10%">Q.tà</th>
        <th style="width:10%">Prezzo unit.</th>
        <th style="width:10%">Totale</th>
      </tr>
    </thead>
    <tbody>
      {% for item in proposal.items %}
      <tr>
        <td>{{ item.product }}</td>
        <td>{{ item.description }}</td>
        <td>{{ item.quantity }}</td>
        <td>€ {{ "%.2f"|format(item.unitPrice) }}</td>
        <td>€ {{ "%.2f"|format(item.total) }}</td>
      </tr>
      {% endfor %}
    </tbody>
    <tfoot>
      {% if proposal.discount > 0 %}
      <tr><td colspan="4">Sconto</td><td>-€ {{ "%.2f"|format(proposal.discount) }}</td></tr>
      {% endif %}
      <tr><td colspan="4">Imponibile</td><td>€ {{ "%.2f"|format(proposal.subtotal) }}</td></tr>
      <tr><td colspan="4">IVA 22%</td><td>€ {{ "%.2f"|format(proposal.tax) }}</td></tr>
      <tr class="total-row"><td colspan="4">TOTALE</td><td>€ {{ "%.2f"|format(proposal.total) }}</td></tr>
    </tfoot>
  </table>

  {% if proposal.notes %}
  <p><strong>Note:</strong> {{ proposal.notes }}</p>
  {% endif %}

  <p class="validity">
    Offerta valida fino al {{ proposal.validUntil.strftime('%d/%m/%Y') }}
  </p>

  <div class="footer">
    AiChain Solutions · Via Vincenzo Giuffrida 203/A, 95128 Catania ·
    info@aichainsolutions.net · aichainsolutions.net
  </div>
</body>
</html>
"""

async def generate_proposal_pdf(proposal: dict, lead: dict) -> str:
    """
    Genera PDF preventivo, carica su Firebase Storage,
    ritorna URL pubblico del file.
    """
    # Render HTML
    env = Environment(loader=BaseLoader())
    template = env.from_string(PROPOSAL_HTML_TEMPLATE)

    # Converti Timestamp Firestore in datetime per Jinja
    proposal_copy = {**proposal}
    for key in ("createdAt", "validUntil"):
        ts = proposal_copy.get(key)
        if hasattr(ts, "timestamp"):
            proposal_copy[key] = datetime.fromtimestamp(ts.timestamp(), tz=timezone.utc)

    html_str = template.render(proposal=proposal_copy, lead=lead)

    # Genera PDF con WeasyPrint
    pdf_bytes = HTML(string=html_str).write_pdf()

    # Upload su Firebase Storage
    storage_path = f"proposals/{proposal['id']}/preventivo.pdf"
    blob = bucket.blob(storage_path)
    blob.upload_from_string(
        pdf_bytes,
        content_type="application/pdf",
    )
    blob.make_public()

    return blob.public_url, storage_path
```

---

## 16. Cloud Scheduler — job periodici

### Setup scheduler (5 job)

```bash
# 1. Sequence tick — avanza sequenze drip ogni ora (orari lavorativi)
gcloud scheduler jobs create http crm-sequence-tick \
  --location=europe-west1 \
  --schedule="0 8-20 * * 1-5" \
  --uri="https://crm-scheduler-HASH-ew.a.run.app/scheduler/sequence-tick" \
  --message-body='{"job":"sequence_tick"}' \
  --headers="Content-Type=application/json" \
  --oidc-service-account-email="crm-backend@$PROJECT_ID.iam.gserviceaccount.com" \
  --time-zone="Europe/Rome"

# 2. Segment refresh — ricalcola segmenti ogni notte
gcloud scheduler jobs create http crm-segment-refresh \
  --location=europe-west1 \
  --schedule="0 2 * * *" \
  --uri="https://crm-scheduler-HASH-ew.a.run.app/scheduler/segment-refresh" \
  --message-body='{"job":"segment_refresh"}' \
  --headers="Content-Type=application/json" \
  --oidc-service-account-email="crm-backend@$PROJECT_ID.iam.gserviceaccount.com" \
  --time-zone="Europe/Rome"

# 3. Score decay settimanale — riduce score dei lead inattivi
gcloud scheduler jobs create http crm-score-decay \
  --location=europe-west1 \
  --schedule="0 3 * * 1" \
  --uri="https://crm-scheduler-HASH-ew.a.run.app/scheduler/score-decay" \
  --message-body='{"job":"score_decay"}' \
  --headers="Content-Type=application/json" \
  --oidc-service-account-email="crm-backend@$PROJECT_ID.iam.gserviceaccount.com" \
  --time-zone="Europe/Rome"

# 4. Report settimanale CEO/CMO (ogni lunedì mattina)
gcloud scheduler jobs create http crm-weekly-report \
  --location=europe-west1 \
  --schedule="0 8 * * 1" \
  --uri="https://crm-scheduler-HASH-ew.a.run.app/scheduler/weekly-report" \
  --message-body='{"job":"weekly_report"}' \
  --headers="Content-Type=application/json" \
  --oidc-service-account-email="crm-backend@$PROJECT_ID.iam.gserviceaccount.com" \
  --time-zone="Europe/Rome"

# 5. Cleanup enrollment completati (ogni domenica notte)
gcloud scheduler jobs create http crm-enrollment-cleanup \
  --location=europe-west1 \
  --schedule="0 1 * * 0" \
  --uri="https://crm-scheduler-HASH-ew.a.run.app/scheduler/enrollment-cleanup" \
  --message-body='{"job":"enrollment_cleanup"}' \
  --headers="Content-Type=application/json" \
  --oidc-service-account-email="crm-backend@$PROJECT_ID.iam.gserviceaccount.com" \
  --time-zone="Europe/Rome"
```

### `backend/scheduler_handlers/main.py`

```python
from fastapi import FastAPI, Request, HTTPException
from app.services.sequence_service import process_due_enrollments
from app.services.segment_service import evaluate_all_segments
from app.services.scoring_service import apply_score_decay
from app.services.email_service import send_weekly_report
from app.firebase_admin import db

app = FastAPI(title="CRM Scheduler Handlers")

async def _verify_scheduler(request: Request):
    """Verifica che la call venga da Cloud Scheduler (OIDC)"""
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(403, "Non autorizzato")
    # Cloud Run verifica automaticamente il token OIDC se configurato

@app.post("/scheduler/sequence-tick")
async def sequence_tick(request: Request):
    await _verify_scheduler(request)
    processed = await process_due_enrollments(db)
    return {"processed": processed}

@app.post("/scheduler/segment-refresh")
async def segment_refresh(request: Request):
    await _verify_scheduler(request)
    await evaluate_all_segments(db)
    return {"status": "ok"}

@app.post("/scheduler/score-decay")
async def score_decay(request: Request):
    await _verify_scheduler(request)
    await apply_score_decay(db)
    return {"status": "ok"}

@app.post("/scheduler/weekly-report")
async def weekly_report(request: Request):
    await _verify_scheduler(request)
    await send_weekly_report(db)
    return {"status": "ok"}
```

---

## 17. Frontend — nuovi componenti

### Nuovi componenti shadcn/ui da installare per Fase 2

```bash
cd frontend

# Componenti shadcn aggiuntivi Fase 2
npx shadcn@latest add tabs
npx shadcn@latest add textarea
npx shadcn@latest add popover
npx shadcn@latest add dropdown-menu
npx shadcn@latest add scroll-area
npx shadcn@latest add resizable
npx shadcn@latest add toggle-group
npx shadcn@latest add command
npx shadcn@latest add calendar
npx shadcn@latest add date-picker
```

### Nuove pagine e componenti chiave

#### `app/crm/inbox/page.tsx` — struttura

```tsx
"use client"
import { ResizablePanelGroup, ResizablePanel, ResizableHandle } from "@/components/ui/resizable"
import { ConversationList } from "@/components/crm/inbox/ConversationList"
import { ConversationDetail } from "@/components/crm/inbox/ConversationDetail"
import { InboxFilters } from "@/components/crm/inbox/InboxFilters"
import { useConversations } from "@/hooks/useInbox"
import { useState } from "react"

export default function InboxPage() {
  const [selectedConvId, setSelectedConvId] = useState<string | null>(null)
  const [channelFilter, setChannelFilter]   = useState<"all" | "email" | "whatsapp">("all")

  const { data: conversations } = useConversations(
    channelFilter === "all" ? undefined : channelFilter
  )

  return (
    <div className="h-full flex flex-col">
      <InboxFilters
        activeChannel={channelFilter}
        onChannelChange={setChannelFilter}
      />

      <ResizablePanelGroup direction="horizontal" className="flex-1 rounded-lg border">
        <ResizablePanel defaultSize={35} minSize={25}>
          <ConversationList
            conversations={conversations?.items ?? []}
            selectedId={selectedConvId}
            onSelect={setSelectedConvId}
          />
        </ResizablePanel>

        <ResizableHandle />

        <ResizablePanel defaultSize={65}>
          {selectedConvId
            ? <ConversationDetail convId={selectedConvId} />
            : <div className="flex h-full items-center justify-center text-muted-foreground text-sm">
                Seleziona una conversazione
              </div>
          }
        </ResizablePanel>
      </ResizablePanelGroup>
    </div>
  )
}
```

#### `components/crm/sequences/SequenceBuilder.tsx` — struttura

```tsx
"use client"
import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Plus, Mail, MessageSquare, CheckSquare, ArrowDown } from "lucide-react"
import { SequenceStepCard } from "./SequenceStepCard"
import { AddStepDialog } from "./AddStepDialog"

interface Step {
  id:         string
  stepNumber: number
  channel:    "email" | "whatsapp" | "task"
  delayDays:  number
  templateId: string | null
  condition:  { type: string; value?: number } | null
}

const CHANNEL_ICONS = {
  email:    Mail,
  whatsapp: MessageSquare,
  task:     CheckSquare,
}

export function SequenceBuilder({ sequenceId }: { sequenceId: string }) {
  const [steps, setSteps]         = useState<Step[]>([])
  const [addingAfter, setAddingAfter] = useState<number | null>(null)

  return (
    <div className="max-w-2xl mx-auto space-y-0">
      {steps.map((step, index) => (
        <div key={step.id}>
          <SequenceStepCard
            step={step}
            stepNumber={index + 1}
            onUpdate={(updated) => {
              setSteps(steps.map(s => s.id === step.id ? updated : s))
            }}
            onDelete={() => setSteps(steps.filter(s => s.id !== step.id))}
          />
          {/* Connettore tra step */}
          <div className="flex flex-col items-center py-2">
            <ArrowDown className="h-4 w-4 text-muted-foreground" />
            <Button
              variant="ghost"
              size="sm"
              className="text-xs text-muted-foreground h-6"
              onClick={() => setAddingAfter(index)}
            >
              <Plus className="h-3 w-3 mr-1" /> Aggiungi step
            </Button>
          </div>
        </div>
      ))}

      {steps.length === 0 && (
        <Card className="border-dashed">
          <CardContent className="flex flex-col items-center justify-center py-12 gap-3">
            <p className="text-sm text-muted-foreground">Nessuno step — aggiungi il primo</p>
            <Button onClick={() => setAddingAfter(null)}>
              <Plus className="h-4 w-4 mr-2" /> Aggiungi step
            </Button>
          </CardContent>
        </Card>
      )}

      <AddStepDialog
        open={addingAfter !== null}
        onClose={() => setAddingAfter(null)}
        onAdd={(newStep) => {
          const insertAt = addingAfter !== null ? addingAfter + 1 : steps.length
          const updated  = [...steps]
          updated.splice(insertAt, 0, { ...newStep, id: crypto.randomUUID() })
          setSteps(updated.map((s, i) => ({ ...s, stepNumber: i + 1 })))
          setAddingAfter(null)
        }}
      />
    </div>
  )
}
```

---

## 18. Firestore rules — aggiornamento

Aggiungere alle rules esistenti:

```js
// Sequenze e template — read/write per sales, no delete per non-admin
match /email_templates/{tplId} {
  allow read: if isSales();
  allow create, update: if isSales();
  allow delete: if isAdmin();
}

match /sequences/{seqId} {
  allow read: if isSales();
  allow create, update: if isSales();
  allow delete: if isAdmin();

  match /steps/{stepId} {
    allow read, write: if isSales();
  }
}

match /sequence_enrollments/{enrollId} {
  allow read: if isSales();
  allow create: if isSales();
  allow update: if isSales();   // Per stop/pause manuale
  allow delete: if false;
}

// Email sends — solo lettura (scritto dal backend)
match /email_sends/{sendId} {
  allow read: if isSales();
  allow create, update: if false;  // Solo backend via Admin SDK
}

// Workflow
match /workflows/{wfId} {
  allow read: if isSales();
  allow create, update: if isSales();
  allow delete: if isAdmin();
}

// Segmenti
match /segments/{segId} {
  allow read: if isSales();
  allow create, update: if isSales();
  allow delete: if isAdmin();
}

// Conversazioni e messaggi
match /conversations/{convId} {
  allow read: if isSales();
  allow create, update: if isSales();
  allow delete: if isAdmin();

  match /messages/{msgId} {
    allow read: if isSales();
    allow create: if isSales();
    allow update, delete: if false;  // Append-only
  }
}

// Preventivi
match /proposals/{propId} {
  allow read: if isSales();
  allow create, update: if isSales();
  allow delete: if isAdmin();
}
```

---

## 19. CI/CD — aggiornamento

### Nuove immagini Docker da buildare e deployare

```bash
# Aggiungi al cloudbuild.yaml principale o crea file separati

# Worker images
gcloud builds submit ./backend/workers/workflow_worker \
  --tag=europe-west1-docker.pkg.dev/$PROJECT_ID/crm/workflow-worker:latest

gcloud builds submit ./backend/workers/sequence_worker \
  --tag=europe-west1-docker.pkg.dev/$PROJECT_ID/crm/sequence-worker:latest

gcloud builds submit ./backend/workers/scoring_worker \
  --tag=europe-west1-docker.pkg.dev/$PROJECT_ID/crm/scoring-worker:latest

gcloud builds submit ./backend/workers/inbox_worker \
  --tag=europe-west1-docker.pkg.dev/$PROJECT_ID/crm/inbox-worker:latest

gcloud builds submit ./backend/scheduler_handlers \
  --tag=europe-west1-docker.pkg.dev/$PROJECT_ID/crm/scheduler:latest

# Deploy nuovi Cloud Run services
for SERVICE in workflow-worker sequence-worker scoring-worker inbox-worker; do
  gcloud run deploy crm-$SERVICE \
    --image=europe-west1-docker.pkg.dev/$PROJECT_ID/crm/${SERVICE/:/-}:latest \
    --region=europe-west1 \
    --no-allow-unauthenticated \
    --service-account=crm-workers@$PROJECT_ID.iam.gserviceaccount.com \
    --memory=256Mi \
    --cpu=1 \
    --min-instances=0 \
    --max-instances=5 \
    --concurrency=10
done

gcloud run deploy crm-scheduler \
  --image=europe-west1-docker.pkg.dev/$PROJECT_ID/crm/scheduler:latest \
  --region=europe-west1 \
  --no-allow-unauthenticated \
  --service-account=crm-backend@$PROJECT_ID.iam.gserviceaccount.com \
  --memory=512Mi \
  --min-instances=0 \
  --max-instances=2
```

---

## 20. Costi stimati Fase 2

### Fase 2 aggiuntiva (sulla base di Fase 1)

```
Scenario: 500 lead, 200 email/mese, 50 WA/mese, 4 worker services

Pub/Sub:
  ~5K messaggi/mese                              → €0.00 (free tier: 10GB/mese)

Cloud Scheduler:
  5 job                                          → €0.00 (free tier: 3 job gratuiti)
  2 job a pagamento                              → €0.20

Cloud Run — 4 nuovi worker services:
  Scala a 0 quando non ci sono eventi
  ~20K invocazioni/mese totali, 256MB            → €3–8

Firestore — nuove collezioni Fase 2:
  ~30K write/mese aggiuntive                    → €0.05
  ~200K read/mese aggiuntive                    → €0.04

Resend EU — email sequenze:
  < 3K email/mese                               → €0.00 (free tier)

WhatsApp Business API (Meta):
  < 1K conversazioni/mese (business-initiated)  → ~€15–50
  (conversazioni user-initiated nelle 24h: gratis)

WeasyPrint PDF (in Cloud Run):
  CPU usage per PDF generation                  → incluso in Cloud Run

COSTO AGGIUNTIVO FASE 2 STIMATO: €20–60/mese
TOTALE FASE 1 + FASE 2: €25–90/mese
```

---

## 21. Checklist sviluppatore

### Setup Fase 2 (prerequisiti)

- [ ] Fase 1 completata e in produzione
- [ ] Meta Business Manager verificato + WABA approvato
- [ ] Template WhatsApp creati e approvati su Meta

### Sprint 1 — settimane 1–3

**Event bus & worker foundation**
- [ ] Cloud Pub/Sub: tutti i topic creati in europe-west1
- [ ] Service account `crm-workers` con permessi corretti
- [ ] `pubsub_service.py` — publish helper + emit_* functions
- [ ] `workflow_worker` — Docker image, Cloud Run deploy, subscription configurata
- [ ] `scoring_worker` — Docker image, Cloud Run deploy
- [ ] Test end-to-end: cambio stage → evento Pub/Sub → worker riceve

**Email sequences foundation**
- [ ] Nuove collezioni Firestore: sequences, steps, enrollments, email_sends
- [ ] `sequence_service.py` — enroll_lead, process_due_enrollments
- [ ] `template_service.py` — render_template con tutte le variabili
- [ ] `email_service.py` — send_tracked_email con pixel + link tracking
- [ ] `tracking.py` router — /track/open/:id e /track/click/:id
- [ ] Cloud Scheduler — crm-sequence-tick ogni ora (lun-ven 8-20)
- [ ] Test sequenza completa: enroll → wait → send email → track open → log activity

### Sprint 2 — settimane 4–6

**Workflow builder**
- [ ] Nuova collezione Firestore: workflows (con conditions)
- [ ] `workflow_service.py` — _evaluate_workflows, _execute_actions
- [ ] Router `/api/v1/workflows` — CRUD completo
- [ ] Tutti i tipi di azione implementati e testati
- [ ] Frontend: `WorkflowBuilder` pagina con lista workflow + form creazione
- [ ] Test workflow: lead creato con industry=legal → auto-enroll sequenza

**Lead scoring v2**
- [ ] `scoring_service.py` aggiornato con decay temporale
- [ ] `scoring_worker` Cloud Run riceve eventi score.events
- [ ] Cloud Scheduler — crm-score-decay ogni lunedì
- [ ] Test: lead inattivo da 30 giorni → score ridotto automaticamente

**Segmenti dinamici**
- [ ] Nuova collezione Firestore: segments, segment_memberships
- [ ] `segment_service.py` — evaluate_all_segments, _eval_condition
- [ ] Cloud Scheduler — crm-segment-refresh ogni notte alle 02:00
- [ ] Frontend: pagina Segmenti con regole builder
- [ ] Test: segmento "Studio Legale score > 70" → lista leads corretta

### Sprint 3 — settimane 7–9

**WhatsApp & Inbox**
- [ ] Meta Cloud API configurata + webhook verificato
- [ ] `whatsapp.py` router — receive + send template
- [ ] `whatsapp_service.py` — send_template, send_text
- [ ] Nuove collezioni Firestore: conversations, messages, whatsapp_templates
- [ ] `inbox_worker` Cloud Run per eventi inbox
- [ ] Firebase Realtime DB configurato per notifiche
- [ ] Frontend: `InboxPage` con lista conversazioni + thread messages
- [ ] Frontend: `useInboxNotifications` hook con real-time updates
- [ ] Test: messaggio WhatsApp in entrata → crea conversazione → notifica real-time nel CRM

**Preventivi PDF**
- [ ] WeasyPrint installato nell'immagine Docker backend
- [ ] `pdf_service.py` — generate_proposal_pdf
- [ ] Router `/api/v1/proposals` — CRUD + genera PDF + tracking token
- [ ] Frontend: `ProposalBuilder` con form items + preview totale
- [ ] Test: crea preventivo → genera PDF → carica su Storage → link funzionante

**Integrazione & QA**
- [ ] Template email Fase 2: welcome, case study, costo inazione, demo invite, last call
- [ ] Sequenza "Playbook Download" completa (5 step, 14 giorni) testata end-to-end
- [ ] Sequenza "Assessment Completed" (risposta in 5 min) testata
- [ ] Workflow "Auto-assign Legal" testato
- [ ] Report settimanale CEO/CMO: template email + Cloud Scheduler
- [ ] Firestore rules aggiornate e testate
- [ ] Security review: webhook WhatsApp verify token, OIDC worker auth
- [ ] Performance: query Firestore con EXPLAIN, indici compositi ottimizzati
- [ ] Deploy staging completo + smoke test tutte le feature
- [ ] Handoff QA + documentazione API aggiornata (OpenAPI)

---

> **Prossimo documento:** `CRM_ARCHITECTURE_PHASE3.md`
> Intelligence: Vertex AI lead scoring, ZenTratto sul CRM (ricerca semantica),
> blockchain audit trail consensi via SignSisure, BigQuery analytics,
> revenue forecasting ML, report CEO generati da LLM.

---

*AiChain Solutions — CTO Office · Fase 2 Automation · Maggio 2026*
*Stack: FastAPI · Firebase · Cloud Pub/Sub · Cloud Scheduler · Cloud Run Workers · GCP europe-west1*
