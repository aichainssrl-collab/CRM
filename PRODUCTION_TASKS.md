# AiChain CRM — Task per Produzione

> Aggiornato: 2025-01-XX | Stato: 109 test backend ✅ | Build frontend ✅ | TypeScript ✅

---

## Legenda
- 🔴 Critico — blocca il deploy
- 🟡 Importante — da fare prima del go-live
- 🟢 Miglioramento — post-launch o nice-to-have

---

## 1. COMMIT & VERSIONING

### 1.1 🔴 Commit intermedio di tutto il lavoro
- 84 file modificati + ~20 nuovi, tutto uncommitted
- Rischi: perdita lavoro, impossibilità di rollback
- **Azione**: `git add -A && git commit -m "feat: i18n, sidebar, enrichment, meta ads, refactoring massiccio"`

### 1.2 🟡 Branching strategy
- Attualmente tutto su `main` senza branch di sviluppo
- **Azione**: definire workflow (Git Flow o trunk-based) e documentarlo

---

## 2. SICUREZZA

### 2.1 🔴 DEBUG=false in produzione
- `config.py` ha `DEBUG: bool = True` come default
- `cloudbuild.yaml` già imposta `DEBUG=false` nel deploy, ma meglio verificare
- **Azione**: controllare che il Cloud Build deploy setti correttamente `DEBUG=false`

### 2.2 🔴 Exception handler espone dettagli interni
- `main.py` line ~62: `"detail": f"Errore interno: {type(exc).__name__}: {exc}"`
- In produzione espone nomi classi Python e stack info all'utente
- **Azione**: in produzione restituire solo `"Errore interno del server"`, loggare il traceback

### 2.3 🟡 CORS hardcoded
- `ALLOWED_ORIGINS` è una lista in config, il Cloud Build la aggiorna dinamicamente
- **Azione**: verificare che il deploy aggiorni sempre la lista con l'URL del frontend

### 2.4 🟡 Rate limiting
- `slowapi` è configurato ma solo su forms pubblici
- **Azione**: valutare rate limiting su tutti gli endpoint autenticati (non solo forms)

### 2.5 🟡 Input validation
- Tests `test_security.py` coprono email, consent, limit bounding
- **Azione**: audit completo degli schema Pydantic per tutti i router

### 2.6 🟢 Headers di sicurezza
- Nessun header HSTS, X-Frame-Options, CSP configurati
- **Azione**: aggiungere middleware per security headers o configurare su Cloud Run

---

## 3. DATABASE

### 3.1 🔴 Indici MongoDB
- `db_service.py` non crea indici esplicitamente
- **Azione**: creare script di migrazione indici per:
  - `leads`: email (unique), status, owner, createdAt
  - `deals`: stage, leadId, owner
  - `tasks`: status, dueDate, assignedTo
  - `users`: uid (unique), email
  - `form_submissions`: createdAt, formType
  - `gdpr_consents`: leadId, timestamp

### 3.2 🟡 Seed script
- `seed_local.py` è menzionato in CLAUDE.md ma non esiste
- **Azione**: creare script di seed per utenti e dati di esempio

### 3.3 🟡 Backup strategy
- Nessun backup MongoDB configurato
- **Azione**: se MongoDB Atlas → abilitare automatic backups; se self-hosted → script cron

### 3.4 🟢 Connection pooling tuning
- `motor` client usa default settings
- **Azione**: configurare maxPoolSize, minPoolSize, serverSelectionTimeoutMS

---

## 4. BACKEND

### 4.1 🟡 Pydantic v2 deprecation warning
- 1 warning durante i test: `Support for class-based config is deprecated`
- **Azione**: migrare da `class Config:` a `model_config = ConfigDict(...)`

### 4.2 🟡 Python version mismatch
- Dockerfile usa `python:3.12-slim`, venv locale usa Python 3.11
- **Azione**: allineare (preferibile 3.12 ovunque)

### 4.3 🟡 Health check endpoint
- `/api/health` esiste e funziona ✅
- **Azione**: aggiungere check MongoDB connectivity nel health (non solo `{"status": "ok"}`)

### 4.4 🟡 Logging strutturato
- Attualmente `logging.basicConfig(level=logging.INFO)`
- **Azione**: configurare JSON logging per Cloud Run (google-cloud-logging)

### 4.5 🟢 API versioning
- Tutte le API sotto `/api/v1/` ✅
- **Azione**: documentare policy di versioning per breaking changes

### 4.6 🟢 OpenAPI schema
- Swagger UI disponibile su `/docs` ✅
- **Azione**: verificare che tutti i router abbiano response models e description

---

## 5. FRONTEND

### 5.1 ✅ Build completata con successo
- TypeScript: 0 errori
- Next.js build: success, standalone output
- I18n: it/en funzionanti

### 5.2 🟡 NEXT_PUBLIC_API_URL obsoleto
- `.env.local.example` ha `NEXT_PUBLIC_API_URL` ma il frontend usa rewrites in `next.config.mjs`
- **Azione**: rimuovere `NEXT_PUBLIC_API_URL` dall'env example, documentare che il proxy è gestito da Next.js

### 5.3 🟡 Firebase SDK nel frontend
- `firebase.ts` importa anche `getFirestore` e `getStorage` ma il CLAUDE.md dice che Firebase è solo per Auth
- **Azione**: rimuovere import inutilizzati di Firestore e Storage dal client se non usati

### 5.4 🟡 Test frontend
- `vitest` è configurato ma non ci sono test nel frontend
- **Azione**: aggiungere test critici (auth flow, lead CRUD, form submission)

### 5.5 🟡 Error boundaries
- Nessun error boundary React configurato
- **Azione**: aggiungere `error.tsx` e `not-found.tsx` nelle route principali

### 5.6 🟢 Performance
- Bundle size sembra ragionevole (First Load JS ~87.5 kB)
- **Azione**: verificare Lighthouse score, lazy loading per pagine pesanti

### 5.7 🟢 Accessibilità
- shadcn/ui ha buone basi a11y
- **Azione**: audit ARIA labels, keyboard navigation, contrast ratio

---

## 6. CI/CD & DEPLOY

### 6.1 ✅ Cloud Build pipeline configurata
- `cloudbuild.yaml` completo: test → build → push → deploy backend → frontend → CORS
- Secrets da Secret Manager ✅

### 6.2 🟡 Frontend build secrets
- `_NEXT_PUBLIC_FIREBASE_API_KEY` e `_NEXT_PUBLIC_FIREBASE_APP_ID` sono stringa vuota nel substitutions
- **Azione**: compilare i valori reali nel trigger Cloud Build

### 6.3 🟡 Cloudbuild frontend separato
- `cloudbuild-frontend.yaml` esiste ma non è chiaro se è usato
- **Azione**: verificare se serve un trigger separato o se il main basta

### 6.4 🟡 Docker image scanning
- Nessuno step di security scanning delle immagini Docker
- **Azione**: aggiungere Trivy o Container Analysis nello step di build

### 6.5 🟡 Rollback strategy
- Nessuna strategia di rollback documentata
- **Azione**: documentare `gcloud run services update-traffic` per rollback

### 6.6 🟢 Preview environments
- Nessun ambiente di preview/staging
- **Azione**: valutare Cloud Run revisions con traffico split

---

## 7. MONITORING & LOGGING

### 7.1 🟡 Uptime monitoring
- Health check endpoint esiste ma nessun alert configurato
- **Azione**: configurare Cloud Monitoring uptime checks + alerting

### 7.2 🟡 Error tracking
- Solo logging Python base, nessun Sentry/error tracker
- **Azione**: integrare Sentry o Google Cloud Error Reporting

### 7.3 🟡 Structured logging backend
- Logging non strutturato (plain text)
- **Azione**: passare a JSON logging per Cloud Run

### 7.4 🟢 Dashboard metriche
- Nessuna dashboard GCP configurata
- **Azione**: creare dashboard Cloud Run con latenza, errori, istanze

---

## 8. DOCUMENTAZIONE

### 8.1 🟡 README.md mancante
- Nessun README nella root del progetto
- **Azione**: creare README con: stack, setup locale, deploy, env vars, struttura

### 8.2 🟡 API documentation
- Swagger UI disponibile ma potrebbe essere incompleto
- **Azione**: aggiungere description e response model a ogni endpoint

### 8.3 🟡 Runbook deploy
- `docs/deploy-cloud-run.md` esiste
- **Azione**: verificare che sia aggiornato con la configurazione attuale

### 8.4 🟢 CHANGELOG
- Nessun changelog
- **Azione**: iniziare a mantenere CHANGELOG.md o usare conventional commits

---

## 9. I18N & LOCALIZZAZIONE

### 9.1 ✅ Struttura i18n configurata
- `next-intl` con routing it/en
- `messages/it.json` e `messages/en.json` presenti
- Middleware per routing locale ✅

### 9.2 🟡 Completezza traduzioni
- **Azione**: verificare che tutti i testi nelle pagine CRM usino `useTranslations()` e non hardcoded strings

### 9.3 🟢 Aggiungere lingue
- Attualmente solo it/en
- **Azione**: valutare de/fr per mercato EU se necessario

---

## 10. GDPR & COMPLIANCE

### 10.1 ✅ GDPR endpoints implementati
- Export dati, cancellazione, audit trail
- `gdpr_consents` append-only ✅

### 10.2 🟡 Cookie consent
- Nessun banner cookie configurato
- **Azione**: aggiungere cookie consent per analytics/tracking se usati

### 10.3 🟡 Privacy policy / Terms
- Nessuna pagina privacy policy nel frontend
- **Azione**: creare pagine /privacy e /terms

### 10.4 🟢 Data retention policy
- Nessuna policy automatica di retention
- **Azione**: definire e implementare TTL per dati vecchi

---

## 11. PERFORMANCE & SCALING

### 11.1 🟡 Cloud Run cold starts
- `min-instances=0` → cold start possibile
- **Azione**: valutare `min-instances=1` per eliminare cold start

### 11.2 🟡 MongoDB Atlas vs self-hosted
- `.env.example` mostra sia locale che Firestore (via MongoDB wire protocol)
- **Azione**: chiarire se produzione usa Atlas o Firestore direct

### 11.3 🟢 CDN per assets statici
- Nessun CDN configurato per frontend
- **Azione**: valutare Cloud CDN o Cloudflare

---

## 12. TESTING

### 12.1 ✅ Backend: 109 test passanti
- Copertura: security, CORS, input validation, rate limiting, data isolation
- Services testati: lead, deal, booking, gdpr, scoring, activity, db

### 12.2 🟡 Test E2E
- `test_e2e_flow.py` esiste ma non è chiaro se è completo
- **Azione**: verificare copertura E2E

### 12.3 🟡 Test frontend mancanti
- vitest configurato ma 0 test
- **Azione**: aggiungere test per componenti critici

### 12.4 🟢 Load testing
- `load_test.py` esiste
- **Azione**: eseguire load test contro staging prima del go-live

---

## PRIORITÀ RACCOMANDATA

### Sprint 1 — Prima del deploy (🔴 critico)
1. Commit di tutto il lavoro in corso
2. Fix exception handler (non esporre dettagli interni)
3. Compilare secrets nel Cloud Build trigger
4. Creare indici MongoDB
5. Verificare DEBUG=false nel deploy

### Sprint 2 — Prima del go-live (🟡 importante)
6. Creare README.md
7. Health check con MongoDB connectivity
8. Error boundaries frontend
9. Test frontend base
10. Monitoring + alerting Cloud Run

### Sprint 3 — Post-launch (🟢 miglioramenti)
11. Security headers
12. Load testing
13. Cookie consent + privacy policy
14. Dashboard metriche
15. Preview environments