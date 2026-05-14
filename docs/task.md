# Task List — AiChain CRM

> Basato sull'analisi dell'architettura (Phase1 v2, Phase2, Phase3) e del codice esistente.
> Aggiornato: 2026-05-12 (sera)

---

## Legenda

- `[ ]` Da fare
- `[x]` Completato
- `[~]` Parzialmente implementato

---

## FASE 1 — Foundation

### Sprint 1 — Backend Core

#### Setup & Infrastruttura
- [x] `firebase_admin.py` — init SDK con ADC + JSON fallback
- [x] `config.py` — Settings da env / Secret Manager
- [x] `deps.py` — Dependency injection (auth token verification)
- [x] Firestore rules — riviste (blocco client SDK su gdpr_consents/form_submissions)
- [x] Firestore indexes — aggiornati con 17 indici compositi per tutte le query
- [x] Service account GCP — script `setup-gcp.sh` con ruoli least privilege
- [x] Firebase progetti dev + prod configurati (`.firebaserc` già corretto)
- [ ] Deploy rules+indexes su dev: `firebase deploy --only firestore`
- [ ] Eseguire `./setup-gcp.sh dev` per creare SA, secrets, queue

#### Models (Pydantic — layer Firestore)
- [x] `models/lead.py` — Lead model (campi Firestore → Python)
- [x] `models/activity.py` — Activity model
- [x] `models/task.py` — Task model
- [x] `models/deal.py` — Deal model
- [x] `models/booking.py` — Booking + BookingSlot model
- [x] `models/user.py` — User model

#### Schemas (request/response API)
- [x] `schemas/lead.py` — Lead create/update/response
- [x] `schemas/activity.py` — Activity schemas
- [x] `schemas/task.py` — Task schemas
- [x] `schemas/deal.py` — Deal schemas
- [x] `schemas/forms.py` — Form submission schemas
- [x] `schemas/booking.py` — Booking + slot schemas
- [x] `schemas/gdpr.py` — GDPR export/erase request schemas
- [x] `schemas/user.py` — User create/update schemas

#### Services
- [x] `services/lead_service.py` — CRUD leads, unicità email (Firestore)
- [x] `services/email_service.py` — Resend EU (httpx, mock in dev)
- [x] `services/gdpr_service.py` — export, erase, consent log (Firestore)
- [x] `services/scoring_service.py` — scoring reale 0-100 (seniority + industry + company + activity)
- [x] `services/db_service.py` — helper Firestore async
- [x] `services/activity_service.py` — append-only activity log
- [x] `services/task_service.py` — CRUD tasks su lead
- [x] `services/deal_service.py` — CRUD deals
- [x] `services/booking_service.py` — slot management, booking CRUD con transazione

#### Routers (API endpoints)
- [x] `routers/auth.py` — `/api/v1/auth`
- [x] `routers/leads.py` — `/api/v1/leads` (GET lista + filtri + paginazione cursor)
- [x] `routers/forms.py` — `/api/v1/forms` (rate limiting 5/min via slowapi)
- [x] `routers/activities.py` — `/api/v1/leads/{id}/activities` (append-only)
- [x] `routers/tasks.py` — `/api/v1/leads/{id}/tasks` (CRUD + complete)
- [x] `routers/deals.py` — `/api/v1/deals` (CRUD pipeline)
- [x] `routers/bookings.py` — `/api/v1/bookings` + slot pubblici
- [x] `routers/gdpr.py` — `/api/v1/gdpr` (export Art.20, erase Art.17)
- [x] `routers/users.py` — `/api/v1/users` (CRUD team CRM + /me)

#### Cloud Tasks
- [x] `utils/cloud_tasks.py` — enqueue helper
- [x] `tasks/handlers.py` — handler base
- [x] Handler: `process_form_submission` — form → crea/aggiorna lead
- [x] Handler: `send_welcome_email` — email benvenuto post-form
- [x] Handler: `recalculate_score` — aggiorna score lead
- [x] Protezione OIDC endpoint `/tasks/handlers/*` (verifica Google OIDC token in prod, skip in dev)

#### Test Backend
- [x] `tests/test_config.py`
- [x] `tests/test_db_service.py`
- [x] `tests/test_deps.py`
- [x] `tests/test_firebase_admin.py`
- [x] `tests/test_gdpr_service.py`
- [x] `tests/test_handlers.py`
- [x] `tests/test_lead_service.py`
- [x] `tests/test_lead_router.py` — test endpoint HTTP leads
- [x] `tests/test_forms_router.py` — test form submission + rate limit
- [x] `tests/test_activity_service.py`
- [x] `tests/test_deal_service.py`
- [x] `tests/test_booking_service.py`
- [x] `tests/test_scoring_service.py`

---

### Sprint 2 — Frontend

#### Setup & Lib
- [x] `lib/firebase.ts` — Firebase client SDK init
- [x] `lib/api.ts` — Axios client con Firebase token interceptor (+ wrapper `apiFetch` per compatibilità hooks)
- [x] `lib/auth.ts` — Firebase Auth helpers
- [x] `lib/utils.ts` — utility functions
- [x] `lib/csvImporter.ts` — CSV import helper

#### Hooks
- [x] `hooks/useAuth.ts` — auth state + login/logout
- [x] `hooks/useLeads.ts` — TanStack Query: list, detail, mutations
- [x] `hooks/useActivities.ts` — timeline lead (read append-only)
- [x] `hooks/useTasks.ts` — task CRUD per lead + global listing (assignedTo, con filtri status/dueBefore)
- [x] `hooks/useDeals.ts` — pipeline deals (useCreateDeal aggiornato con lead_id come query param)
- [x] `hooks/useBookings.ts` — booking slots + prenotazioni
- [x] `hooks/useDashboard.ts` — KPI aggregati
- [x] `hooks/useUsers.ts` — CRUD utenti CRM (useUsers, useCurrentUser, useUpdateUser, useCreateUser)

#### Pagine (App Router)
- [x] `app/(auth)/login/page.tsx`
- [x] `app/crm/page.tsx` — dashboard wired: KPI da API + selector timeRange (7d/30d/90d)
- [x] `app/crm/leads/page.tsx` — lista leads wired: useLeads, filtri, paginazione, CRUD
- [x] `app/crm/leads/[id]/page.tsx` — dettaglio lead wired: lead + activities + tasks + GDPR
- [x] `app/crm/pipeline/page.tsx` — kanban wired: useDeals + KanbanBoard D&D + form nuovo deal
- [x] `app/crm/tasks/page.tsx` — task list wired: useTasks global, filtri all/pending/completed/scaduti
- [x] `app/crm/reports/page.tsx` — reports wired: KPI + 3 grafici (fonte, pipeline/stage, score distribution)
- [x] `app/crm/settings/page.tsx` — settings wired: useCurrentUser, save displayName, toast feedback
- [x] `app/crm/user-admin/page.tsx` — user admin wired: useUsers, cambio ruolo, disattivazione, add user
- [x] `app/forms/playbook/page.tsx` — form pubblico playbook (no auth)
- [x] `app/forms/contact/page.tsx` — form contatto pubblico (no auth)
- [x] `app/forms/assessment/page.tsx` — form assessment (no auth)
- [x] `app/forms/booking/page.tsx` — form prenotazione demo (no auth)

#### Componenti UI base (shadcn/ui)
- [x] `components/ui/button.tsx`
- [x] `components/ui/input.tsx`
- [x] `components/ui/card.tsx`
- [x] `components/ui/badge.tsx`
- [x] `components/ui/table.tsx`
- [x] `components/ui/select.tsx`
- [x] `components/ui/avatar.tsx`
- [x] `components/ui/dropdown-menu.tsx`
- [x] `components/ui/chart.tsx`
- [x] `components/ui/dialog.tsx`
- [x] `components/ui/sheet.tsx`
- [x] `components/ui/sonner.tsx` — toast (base-nova usa sonner, non toast/toaster)
- [x] `components/ui/form.tsx` — react-hook-form + zod wrapper
- [x] `components/ui/label.tsx`
- [x] `components/ui/textarea.tsx`
- [x] `components/ui/separator.tsx`
- [x] `components/ui/skeleton.tsx`
- [x] `components/ui/tabs.tsx`
- [x] `components/ui/popover.tsx`
- [x] `components/ui/calendar.tsx`
- [x] `components/ui/command.tsx`
- [x] `components/ui/tooltip.tsx`
- [x] `components/ui/input-group.tsx` — aggiunto automaticamente da command

#### Componenti business (`components/crm/`)
- [x] `components/crm/Navbar.tsx`
- [x] `components/crm/Sidebar.tsx`
- [x] `components/crm/LeadTable.tsx` — tabella con filtri, sorting, paginazione cursor
- [x] `components/crm/LeadFilters.tsx` — filtri status, score, date, assignee
- [x] `components/crm/LeadForm.tsx` — create/edit lead (modal/sheet)
- [x] `components/crm/LeadDetail.tsx` — sezioni info lead
- [x] `components/crm/ActivityTimeline.tsx` — timeline log attività append-only
- [x] `components/crm/ActivityItem.tsx` — singolo evento timeline
- [x] `components/crm/AddActivityForm.tsx` — nota / chiamata / meeting manuale
- [x] `components/crm/KanbanBoard.tsx` — board drag-and-drop pipeline
- [x] `components/crm/KanbanColumn.tsx` — singola colonna stage
- [x] `components/crm/KanbanCard.tsx` — card lead nella kanban
- [x] `components/crm/TaskList.tsx` — lista task con filtri
- [x] `components/crm/TaskItem.tsx` — task singolo (checkbox, due date, assignee)
- [x] `components/crm/TaskForm.tsx` — create/edit task
- [x] `components/crm/DashboardKPIs.tsx` — metriche principali
- [x] `components/crm/DashboardCharts.tsx` — grafici pipeline e lead per fonte
- [x] `components/crm/LeadScoreBadge.tsx` — badge colorato score 0-100
- [x] `components/crm/StatusBadge.tsx` — badge status lead/deal
- [x] `components/crm/AssigneeSelect.tsx` — dropdown membro team
- [x] `components/crm/BookingCalendar.tsx` — calendario slot disponibili
- [x] `components/crm/BookingSlotPicker.tsx` — selezione slot + form prenotazione
- [x] `components/crm/CsvImportDialog.tsx` — dialog upload CSV leads
- [x] `components/crm/GdprConsentLog.tsx` — audit trail GDPR

---

### Sprint 3 — CI/CD & Deploy

- [x] `backend/Dockerfile` — verifica e ottimizzazione multi-stage
- [x] `frontend/Dockerfile` — verifica e ottimizzazione
- [x] `docker-compose.yml` — test funzionamento locale con emulatori
- [x] `cloudbuild.yaml` — pipeline CI/CD backend (test → build → push → deploy)
- [x] `cloudbuild-frontend.yaml` — pipeline CI/CD frontend
- [x] Artifact Registry EU — configurazione Docker repository
- [x] Cloud Run backend — deploy con Secret Manager
- [x] Cloud Run frontend — deploy
- [x] Secret Manager — migrazione credenziali da `.env`
- [x] Cloud Monitoring — dashboard latency, error rate, instance count
- [x] Cloud Logging — alert su errori 5xx
- [x] Uptime Check — `/api/health` endpoint

#### Verifica finale Fase 1
- [x] E2E: form pubblico → lead creato → activity log → task → email inviata
- [x] Security review: Firestore rules, CORS, rate limiting
- [x] GDPR audit: export dati, cancellazione, consent trail
- [x] Load test base (50 req/s su endpoint leads)

#### Pulizia tecnica (2026-05-12)
- [x] Rimossi `motor`, `pymongo` e `mongodb.py` — residui della migrazione a Firestore
- [x] Rimosso `MONGODB_URI` da `config.py`
- [x] Corretta dipendenza `httpx` duplicata in `requirements.txt`
- [x] `lib/api.ts` migrato a Axios con interceptor JWT (era `fetch` nativo)
- [x] `frontend/secret/` aggiunto a `.gitignore`

#### Backend — endpoint mancanti aggiunti (2026-05-12)
- [x] `routers/task_global.py` — `GET /api/v1/tasks` (collection_group Firestore, filtri assignedTo/status/dueBefore)
- [x] `routers/dashboard.py` — `GET /api/v1/dashboard/metrics` (KPI: totalLeads, newLeads, activeDeals, pipelineValue, conversionRate)
- [x] Registrati in `main.py`

---

## FASE 2 — Automation (avvia dopo Fase 1 in produzione)

### Sprint 1 — Event Bus & Email Sequences

- [ ] Cloud Pub/Sub — 5 topic: `crm.lead.events`, `crm.email.events`, `crm.workflow.events`, `crm.score.events`, `crm.inbox.events`
- [ ] `services/pubsub_service.py` — emit helpers per ogni evento
- [ ] WorkflowWorker — Cloud Run stateless (Pub/Sub push)
- [ ] ScoringWorker — Cloud Run stateless
- [ ] Firestore: `sequences`, `sequence_steps`, `sequence_enrollments`, `email_sends`, `email_templates`
- [ ] `services/sequence_service.py` — enroll, process_due, conditions
- [ ] `services/template_service.py` — render Jinja2 con variabili lead
- [ ] `services/email_service.py` v2 — send_tracked_email con pixel + click tracking
- [ ] `routers/tracking.py` — `/track/open/:id` (pixel 1x1), `/track/click/:id` (redirect)
- [ ] Cloud Scheduler — `sequence-tick` ogni ora lun-ven 8-20

### Sprint 2 — Workflow Builder, Scoring v2, Segmenti

- [ ] Firestore: `workflows` con triggers/conditions/actions
- [ ] `services/workflow_service.py` — evaluate trigger, execute actions
- [ ] `routers/workflows.py` — CRUD workflows
- [ ] `components/crm/WorkflowBuilder.tsx` — UI builder drag-and-drop
- [ ] `services/scoring_service.py` v2 — decay esponenziale (half-life 30gg)
- [ ] ScoringWorker — riceve `crm.score.events` da Pub/Sub
- [ ] Cloud Scheduler — `score-decay` ogni lunedì 03:00
- [ ] Firestore: `segments`, `segment_memberships`
- [ ] `services/segment_service.py` — valutazione regole AND/OR
- [ ] Cloud Scheduler — `segment-refresh` ogni notte 02:00
- [ ] `components/crm/SegmentsPage.tsx` — lista + builder segmenti

### Sprint 3 — WhatsApp, Inbox, Preventivi PDF

- [ ] Meta Cloud API — webhook verify + receive
- [ ] `routers/whatsapp.py` — receive + send template/text
- [ ] `services/whatsapp_service.py` — send_template, send_text (finestra 24h)
- [ ] InboxWorker — Cloud Run stateless
- [ ] Firebase Realtime DB — notifiche real-time inbox
- [ ] Firestore: `conversations`, `messages`, `whatsapp_templates`
- [ ] `components/crm/InboxPage.tsx` — lista conversazioni
- [ ] `components/crm/ConversationView.tsx` — chat real-time
- [ ] `hooks/useInboxNotifications.ts` — Firebase Realtime DB listener
- [ ] `services/pdf_service.py` — WeasyPrint generazione preventivi
- [ ] `routers/proposals.py` — CRUD + genera PDF → upload Storage
- [ ] `components/crm/ProposalBuilder.tsx` — UI builder preventivi
- [ ] 5 email templates (welcome, case study, cost of inaction, demo, last call)
- [ ] Sequenza Playbook Download 5 step — test E2E
- [ ] Sequenza Assessment Completed — test E2E
- [ ] Workflow "Auto-assign Legal leads" — test E2E

---

## FASE 3 — AI Intelligence (avvia dopo Fase 2 in produzione)

- [ ] BigQuery — setup dataset EU, export periodico da Firestore
- [ ] Vertex AI — training modello scoring avanzato
- [ ] `services/vertex_scoring_service.py` — inferenza ML
- [ ] ZenTratto — integrazione ricerca semantica lead
- [ ] SignSisure — firma blockchain consensi GDPR
- [ ] `services/report_service.py` — report CEO generati via Claude API
- [ ] Revenue forecasting ML — predizione conversioni pipeline
- [ ] `components/crm/AIInsightsPanel.tsx` — panel insight AI per lead/deals

---

## INTEGRAZIONE APOLLO.IO — Lead Search & Enrichment

> Apollo.io API per ricerca prospect, arricchimento dati lead e import massivo.
> Documentazione: https://apolloio.github.io/apollo-api-docs/

### Setup & Configurazione

- [ ] Account Apollo.io — ottenere API key (piano Basic minimo per accesso API)
- [ ] `APOLLO_API_KEY` — aggiungere a Secret Manager + `.env`
- [ ] `services/apollo_service.py` — client API Apollo con rate limiting (50 req/min piano Basic)
- [ ] `schemas/apollo.py` — schema risposta Apollo → schema Lead interno

### Backend — Ricerca e Arricchimento

#### People Search (ricerca contatti)
- [ ] `apollo_service.people_search()` — ricerca per nome, titolo, azienda, settore, seniority, location
- [ ] Mappatura campi Apollo → Firestore lead: `first_name`, `last_name`, `email`, `title`, `organization_name`, `linkedin_url`, `phone_numbers`, `city`, `country`
- [ ] Gestione `email_status` Apollo: includere solo `verified` e `likely_to_engage`, escludere `invalid`

#### Organization Search (ricerca aziende)
- [ ] `apollo_service.organization_search()` — ricerca per settore, dimensione, paese, keyword
- [ ] `apollo_service.organization_enrich()` — arricchimento da dominio (`linkedin_url`, `num_employees`, `annual_revenue`, `industry`)

#### Lead Enrichment (arricchimento singolo lead)
- [ ] `apollo_service.enrich_lead()` — data match su email → aggiorna campi lead esistente
- [ ] Aggiornare `lead.enrichedAt` (timestamp) e `lead.enrichmentSource = "apollo"` dopo arricchimento
- [ ] Cloud Task handler: `enrich_lead_apollo` — chiamato automaticamente alla creazione lead se email presente

#### People Match (match su lead esistenti)
- [ ] `apollo_service.people_match()` — match per email esatta → ritorna profilo completo
- [ ] Utilizzato per arricchire lead importati via CSV senza dati completi

#### Endpoint API
- [ ] `routers/apollo.py` — `/api/v1/apollo/*` (protetti da auth)
- [ ] `POST /api/v1/apollo/search` — ricerca prospect con filtri, ritorna lista candidati
- [ ] `POST /api/v1/apollo/import` — importa prospect selezionati come nuovi lead (controlla unicità email)
- [ ] `POST /api/v1/apollo/enrich/{leadId}` — arricchisce lead esistente on-demand
- [ ] `POST /api/v1/apollo/bulk-enrich` — arricchimento massivo (Cloud Task, max 100 lead)
- [ ] `GET /api/v1/apollo/usage` — quota API rimasta (evitare sforare limite piano)

#### Gestione Rate Limiting e Crediti
- [ ] Rispettare limite 50 req/min (piano Basic) — usare `asyncio.sleep` + retry con backoff
- [ ] Loggare ogni chiamata API in Firestore `apollo_api_logs/{id}` (endpoint, crediti usati, timestamp)
- [ ] Alert quando crediti mensili scendono sotto 10% — notifica via email admin

### Frontend — UI Apollo

#### Ricerca Prospect
- [ ] `components/crm/ApolloSearchPanel.tsx` — pannello ricerca con filtri avanzati
  - Filtri: ruolo/titolo, settore (`industry`), dimensione azienda (`employee_ranges`), paese, seniority level
  - Risultati in tabella con: nome, titolo, azienda, email (offuscata fino a reveal), LinkedIn
  - Paginazione risultati Apollo (cursor-based)
- [ ] `components/crm/ApolloResultCard.tsx` — card singolo prospect con score fit e azioni
- [ ] `components/crm/ApolloImportDialog.tsx` — dialog conferma import prospect selezionati come lead
  - Mostra preview campi che verranno creati
  - Avviso se email già presente nel CRM (duplicato)
  - Selezione multipla con checkbox

#### Arricchimento Lead
- [ ] `components/crm/LeadEnrichButton.tsx` — bottone "Arricchisci con Apollo" nel dettaglio lead
  - Mostra badge "Arricchito" con data se già enriched
  - Mostra diff campi prima/dopo arricchimento in un dialog di conferma
- [ ] `components/crm/BulkEnrichDialog.tsx` — dialog arricchimento massivo dalla lead table
  - Seleziona lead senza `enrichedAt` o con enrichment > 30 giorni
  - Progress bar per job bulk asincrono (Cloud Task)

#### Integrazione nella Lead Table
- [ ] Colonna `Fonte` nella `LeadTable` — badge distinto per lead da Apollo vs form vs CSV vs manuale
- [ ] Filtro rapido "Solo lead Apollo" nella `LeadFilters`
- [ ] Tooltip su score Apollo (`apollo_score`) nel `LeadScoreBadge` se disponibile

#### Hook
- [ ] `hooks/useApolloSearch.ts` — TanStack Query per ricerca prospect con debounce 300ms
- [ ] `hooks/useApolloEnrich.ts` — mutation arricchimento + invalidate cache lead

### Test

- [ ] `tests/test_apollo_service.py` — mock API Apollo, test mappatura campi, test rate limiting
- [ ] `tests/test_apollo_router.py` — test endpoint search, import (unicità email), enrich
- [ ] Test E2E: ricerca Apollo → selezione prospect → import come lead → arricchimento automatico

### Note Apollo

- **Privacy/GDPR**: i dati Apollo sono considerati dati provenienti da fonti pubbliche — loggare `gdpr_consents` con `source: "apollo_import"` e `legalBasis: "legitimate_interest"` per ogni lead importato
- **Deduplicazione**: sempre verificare unicità email in Firestore PRIMA di creare lead da Apollo
- **Crediti email**: ogni "reveal" email consuma 1 credito Apollo — fare reveal solo al momento dell'import, non durante la ricerca
- **Campi aggiuntivi Firestore** da aggiungere al modello Lead: `apollo_id`, `apollo_score`, `enrichedAt`, `enrichmentSource`, `linkedin_url`, `seniority`, `num_employees_range`

---

## Note operative

- **GDPR**: nessun dato lascia l'UE — verificare regione prima di aggiungere servizi
- **Soft delete**: mai cancellare documenti lead/deals — usare `deletedAt`
- **Append-only**: activities e gdpr_consents non vanno mai modificati
- **Unicità email**: verificare duplicati lato app (Firestore no UNIQUE constraint)
- **Paginazione**: cursor-based con `last_doc_id`, mai offset
- **Timestamp**: sempre UTC con `datetime.now(timezone.utc)`
