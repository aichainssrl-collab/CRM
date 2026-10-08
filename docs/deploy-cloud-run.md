# Deploy su GCP Cloud Run — Procedura completa

> Guida passo-passo per il primo deploy e per i deploy successivi.
> **Progetto GCP:** `level-facility-479122-u4` — **Regione:** `europe-west1`

---

## Checklist rapida

| Step | Tipo | Fatto? |
|---|---|---|
| 1.1 `./scripts/setup-gcp.sh` | Automatico | ☐ |
| 1.2 Cluster MongoDB Atlas | **Manuale** | ☐ |
| 1.3 Popola secrets in Secret Manager | **Manuale** | ☐ |
| 1.4 Firebase Auth — Authorized Domains | **Manuale** | ☐ |
| 1.5 Meta Ads — token e account ID | **Manuale** | ☐ |
| 2.1 Docker configure Artifact Registry | Automatico | ☐ |
| 2.2 `./scripts/deploy.sh` | Automatico | ☐ |
| 2.3 Aggiungi URL frontend a Firebase Auth | **Manuale** | ☐ |
| 2.4 Seed utenti su Atlas | **Manuale** | ☐ |
| 3.1 Trigger Cloud Build in console GCP | **Manuale** | ☐ |

---

## Prerequisiti locali

```bash
# Verifica che gcloud sia installato
gcloud version

# Verifica che Docker sia installato e in esecuzione
docker info

# Login GCP
gcloud auth login
gcloud auth application-default login
gcloud config set project level-facility-479122-u4
```

---

## FASE 1 — Setup infrastruttura (una sola volta)

### 1.1 Esegui lo script di setup — AUTOMATICO ✅

```bash
chmod +x scripts/setup-gcp.sh
./scripts/setup-gcp.sh
```

Lo script crea automaticamente:
- ✅ API GCP abilitate (Cloud Run, Artifact Registry, Secret Manager, Cloud Tasks, ecc.)
- ✅ Artifact Registry `crm` in `europe-west1`
- ✅ Service Account `crm-backend` con ruoli IAM corretti
- ✅ Service Account `crm-frontend`
- ✅ Secrets placeholder in Secret Manager (7 secrets)
- ✅ Cloud Tasks queue `crm-tasks`
- ✅ Permessi Cloud Build per il deploy

---

### 1.2 MongoDB Atlas — Cluster di produzione ⚠️ MANUALE

Il backend in Cloud Run non può raggiungere `localhost:27017`. Serve MongoDB Atlas.

1. Vai su [https://cloud.mongodb.com](https://cloud.mongodb.com)
2. Crea un nuovo **cluster**:
   - **Tier:** M0 Free (sviluppo) oppure M10+ (produzione)
   - **Cloud provider:** GCP
   - **Regione:** `europe-west1` (latenza minima con Cloud Run)
   - **Nome cluster:** `crm-aichain`
3. Crea un **database user** (tab *Database Access*):
   - Username: `crm-backend`
   - Password: genera e salva in un posto sicuro
   - Role: `readWrite` sul database `crm-aichain-db`
4. Whitelist IP (tab *Network Access*):
   - Clicca **Add IP Address** → **Allow Access from Anywhere** (`0.0.0.0/0`)
   - Cloud Run usa IP dinamici, quindi non è possibile limitare a IP fissi senza VPC
5. Vai su **Connect** → **Drivers** → copia l'URI:
   ```
   mongodb+srv://crm-backend:<password>@crm-aichain.xxxxx.mongodb.net/crm-aichain-db?retryWrites=true&w=majority
   ```
   Salva questo URI — serve al passo 1.3.

---

### 1.3 Popola i Secret Manager ⚠️ MANUALE

Dopo aver eseguito `setup-gcp.sh`, i secrets esistono con valore `PLACEHOLDER`.
Devi aggiornare ciascuno con il valore reale.

#### firebase-credentials

Il JSON è già nel file `backend/.env` (campo `GOOGLE_APPLICATION_CREDENTIALS_JSON`). Copialo intero:

```bash
# Estrai il JSON dal .env e caricalo direttamente
python3 -c "
import os, re
env = open('backend/.env').read()
m = re.search(r'GOOGLE_APPLICATION_CREDENTIALS_JSON=(.*)', env)
print(m.group(1).strip()) if m else print('NOT FOUND')
" | gcloud secrets versions add firebase-credentials \
    --data-file=- \
    --project=level-facility-479122-u4
```

Oppure manualmente — copia il valore JSON dal `.env` e incollalo:

```bash
echo -n '{"type":"service_account","project_id":"level-facility-479122-u4",...}' | \
  gcloud secrets versions add firebase-credentials \
    --data-file=- \
    --project=level-facility-479122-u4
```

#### resend-api-key

```bash
echo -n 're_YOUR_RESEND_API_KEY' | \
  gcloud secrets versions add resend-api-key \
    --data-file=- \
    --project=level-facility-479122-u4
```

#### mongodb-uri

Usa l'URI ottenuto al passo 1.2:

```bash
echo -n 'mongodb+srv://crm-backend:<password>@crm-aichain.xxxxx.mongodb.net/crm-aichain-db?retryWrites=true&w=majority' | \
  gcloud secrets versions add mongodb-uri \
    --data-file=- \
    --project=level-facility-479122-u4
```

#### meta-access-token *(opzionale — solo se usi la sezione Marketing)*

Ottieni il token su [Meta Graph API Explorer](https://developers.facebook.com/tools/explorer/):
- Seleziona la tua app Meta
- Permessi da aggiungere: `ads_read`, `read_insights`
- Clicca **Generate Access Token**
- Per uso in produzione: converti in **Long-Lived Token** (durata 60 giorni) tramite:
  ```
  GET https://graph.facebook.com/v19.0/oauth/access_token
    ?grant_type=fb_exchange_token
    &client_id={app-id}
    &client_secret={app-secret}
    &fb_exchange_token={short-lived-token}
  ```

```bash
echo -n 'EAAxxxxx...' | \
  gcloud secrets versions add meta-access-token \
    --data-file=- \
    --project=level-facility-479122-u4
```

#### meta-ad-account-id *(opzionale — solo se usi la sezione Marketing)*

Trovalo su [Ads Manager](https://business.facebook.com/adsmanager) → in alto a sinistra accanto al nome account. Formato: `act_XXXXXXXXX`.

```bash
echo -n 'act_123456789' | \
  gcloud secrets versions add meta-ad-account-id \
    --data-file=- \
    --project=level-facility-479122-u4
```

#### Verifica tutti i secrets

```bash
for secret in firebase-credentials resend-api-key mongodb-uri meta-access-token meta-ad-account-id; do
  echo -n "$secret: "
  gcloud secrets versions access latest --secret=$secret \
    --project=level-facility-479122-u4 2>/dev/null | head -c 30
  echo "..."
done
```

---

### 1.4 Firebase Auth — Authorized Domains ⚠️ MANUALE

Il dominio `*.run.app` del frontend Cloud Run deve essere autorizzato, altrimenti il login fallisce con `auth/unauthorized-domain`.

> ⚠️ L'URL esatto del frontend lo conosci solo **dopo il primo deploy** (passo 2.2). Puoi tornare qui dopo.

1. Vai su [Firebase Console → Authentication → Settings](https://console.firebase.google.com/project/level-facility-479122-u4/authentication/settings)
2. Sezione **Authorized domains**
3. Clicca **Add domain**
4. Aggiungi l'URL del frontend Cloud Run (es. `crm-frontend-abc123-ew.a.run.app`)
5. Se hai un dominio custom: aggiungi anche `crm.aichainsolutions.net`

---

### 1.5 Meta Ads — Credenziali ⚠️ MANUALE (opzionale)

Necessario solo per attivare la sezione **Marketing → Meta Ads** nel CRM.

**Dove trovare le credenziali:**

| Credenziale | Dove | Formato |
|---|---|---|
| `META_ACCESS_TOKEN` | [developers.facebook.com/tools/explorer](https://developers.facebook.com/tools/explorer/) | `EAAxxxxx...` |
| `META_AD_ACCOUNT_ID` | [business.facebook.com/adsmanager](https://business.facebook.com/adsmanager) → in alto a sx | `act_XXXXXXXXX` |

**Permessi necessari per il token:** `ads_read`, `read_insights`

Dopo aver ottenuto le credenziali, caricale in Secret Manager (vedi passo 1.3) oppure, per test locali, aggiungile a `backend/.env`:

```env
META_ACCESS_TOKEN=EAAxxxxx...
META_AD_ACCOUNT_ID=act_123456789
```

> Il token Meta dura 60 giorni (long-lived). Imposta un promemoria per rinnovarlo.

---

## FASE 2 — Primo deploy

### 2.1 Configura Docker per Artifact Registry — AUTOMATICO ✅

```bash
gcloud auth configure-docker europe-west1-docker.pkg.dev
```

### 2.2 Deploy completo — AUTOMATICO ✅

```bash
# Dry-run — verifica i comandi senza eseguirli
./scripts/deploy.sh --dry-run

# Deploy reale
./scripts/deploy.sh
```

Lo script esegue in ordine:
1. Controllo prerequisiti (gcloud, Docker, autenticazione)
2. Test backend (`pytest tests/ -v`)
3. Build immagine Docker backend → push su Artifact Registry
4. Deploy backend su Cloud Run
5. Recupera URL backend → imposta `BACKEND_INTERNAL_URL` (per Cloud Tasks)
6. Build immagine Docker frontend (con variabili Firebase baked in)
7. Push frontend su Artifact Registry
8. Deploy frontend su Cloud Run (con `BACKEND_URL` runtime)
9. Aggiorna `ALLOWED_ORIGINS` nel backend con l'URL del frontend

Al termine vedrai:
```
  Backend:   https://crm-backend-<hash>-ew.a.run.app
  Frontend:  https://crm-frontend-<hash>-ew.a.run.app
```

---

### 2.3 Aggiungi URL frontend a Firebase Auth ⚠️ MANUALE

Ora che hai l'URL del frontend, torna al passo **1.4** e aggiungi l'URL esatto (`crm-frontend-<hash>-ew.a.run.app`) agli Authorized Domains Firebase.

---

### 2.4 Seed utenti su Atlas ⚠️ MANUALE

Il backend risponde **403** su tutti gli endpoint se la collection `users` in Atlas è vuota.

```bash
# Connettiti ad Atlas con l'URI
mongosh "mongodb+srv://crm-backend:<password>@crm-aichain.xxxxx.mongodb.net/crm-aichain-db"
```

In mongosh:

```js
db.users.insertMany([
  {
    uid: "eHFeSPGP8cWxWHFcM5In4KVYQQ42",
    email: "fred@it.it",
    role: "admin",
    isActive: true,
    createdAt: new Date()
  },
  {
    uid: "fFW6zJBJxCYQ77y0vXskwuFQEIH3",
    email: "admin@aichain.it",
    role: "admin",
    isActive: true,
    createdAt: new Date()
  },
  {
    uid: "JY9qlgBlfWMmtSLo4n2bjte6q8Z2",
    email: "marketing@aichainsolutions.net",
    role: "sales",
    isActive: true,
    createdAt: new Date()
  }
])

// Verifica
db.users.countDocuments()  // deve ritornare 3
```

---

## FASE 3 — Deploy successivi (CI/CD automatico)

### 3.1 Configura il trigger Cloud Build ⚠️ MANUALE (una volta sola)

1. Vai su [Cloud Build → Triggers](https://console.cloud.google.com/cloud-build/triggers?project=level-facility-479122-u4)
2. Clicca **Create trigger**
3. Configura:
   - **Name:** `deploy-crm-main`
   - **Event:** Push to a branch
   - **Branch:** `^main$`
   - **Config file:** `cloudbuild.yaml` (root del repo)
4. Sezione **Substitution variables** — aggiungi:

   | Variabile | Valore |
   |---|---|
   | `_NEXT_PUBLIC_FIREBASE_API_KEY` | `AIzaSy_YOUR_FIREBASE_API_KEY` |
   | `_NEXT_PUBLIC_FIREBASE_APP_ID` | `1:722754739274:web:8c52d53d85d38f6b342b33` |

5. Clicca **Save**

Da ora in poi: ogni `git push` su `main` triggera il deploy automatico.

### 3.2 Deploy manuale selettivo — AUTOMATICO ✅

```bash
./scripts/deploy.sh --backend-only   # solo backend (es. fix Python)
./scripts/deploy.sh --frontend-only  # solo frontend (es. fix UI)
./scripts/deploy.sh --skip-tests     # senza test (emergenza)
./scripts/deploy.sh --tag v1.0.0     # tag specifico
```

---

## Verifica post-deploy

```bash
# Health check backend
curl https://crm-backend-<hash>-ew.a.run.app/api/health
# Risposta attesa: {"status":"ok"}

# Stato sezione Marketing (Meta Ads)
curl -H "Authorization: Bearer <token>" \
  https://crm-backend-<hash>-ew.a.run.app/api/v1/meta/status
# {"configured": true/false, ...}

# Log in tempo reale
gcloud run services logs tail crm-backend --region=europe-west1 --project=level-facility-479122-u4
gcloud run services logs tail crm-frontend --region=europe-west1 --project=level-facility-479122-u4

# Stato servizi
gcloud run services list --region=europe-west1 --project=level-facility-479122-u4
```

---

## Dominio custom (opzionale) ⚠️ MANUALE

Per usare `crm.aichainsolutions.net` invece dell'URL `*.run.app`:

```bash
# Mappa il dominio al servizio frontend
gcloud run domain-mappings create \
  --service=crm-frontend \
  --domain=crm.aichainsolutions.net \
  --region=europe-west1 \
  --project=level-facility-479122-u4

# Recupera i record DNS da configurare
gcloud run domain-mappings describe \
  --domain=crm.aichainsolutions.net \
  --region=europe-west1 \
  --project=level-facility-479122-u4
```

Aggiungi il record CNAME/A al tuo provider DNS, poi:
1. Aggiungi `crm.aichainsolutions.net` agli **Authorized Domains** Firebase Auth (passo 1.4)
2. `ALLOWED_ORIGINS` nel backend include già `https://crm.aichainsolutions.net`

---

## Rinnovo token Meta Ads ⚠️ MANUALE (ogni 60 giorni)

I Long-Lived Token Meta scadono dopo 60 giorni. Per rinnovare:

1. Vai su [Graph API Explorer](https://developers.facebook.com/tools/explorer/) → genera nuovo token
2. Converti in long-lived token (vedi passo 1.5)
3. Aggiorna il secret in GCP:
   ```bash
   echo -n 'EAAxxxxx_nuovo_token...' | \
     gcloud secrets versions add meta-access-token \
       --data-file=- \
       --project=level-facility-479122-u4
   ```
4. Riavvia il backend per caricare la nuova versione del secret:
   ```bash
   gcloud run services update crm-backend \
     --region=europe-west1 \
     --project=level-facility-479122-u4 \
     --set-secrets=META_ACCESS_TOKEN=meta-access-token:latest
   ```

---

## Troubleshooting

### 403 su tutti gli endpoint in produzione
- MongoDB Atlas: verifica che il cluster sia attivo e che l'URI nel secret sia corretto
- Verifica che la collection `users` in Atlas non sia vuota → passo 2.4
- Log: `gcloud run services logs tail crm-backend --region=europe-west1`

### Login Firebase fallisce (`auth/unauthorized-domain`)
- Aggiungi l'URL del frontend agli Authorized Domains in Firebase Auth Console → passo 1.4 / 2.3

### CORS error in produzione
- Verifica che `ALLOWED_ORIGINS` includa l'URL del frontend:
  ```bash
  gcloud run services describe crm-backend \
    --region=europe-west1 \
    --format="value(spec.template.spec.containers[0].env)"
  ```

### Sezione Marketing non mostra dati
- Verifica stato Meta: `GET /api/v1/meta/status` (deve ritornare `configured: true`)
- Controlla che i secrets `meta-access-token` e `meta-ad-account-id` siano popolati e non scaduti
- Il token Meta dura 60 giorni → vedi sezione "Rinnovo token Meta Ads"

### Build Docker fallisce (Out of memory)
- Aumenta la macchina Cloud Build: modifica `machineType: E2_HIGHCPU_8` in `cloudbuild.yaml`

### Secret non trovato (`ERROR: secret not found`)
```bash
gcloud secrets versions access latest --secret=mongodb-uri --project=level-facility-479122-u4
```

### Cloud Tasks falliscono silenziosamente
```bash
# Verifica che la queue esista
gcloud tasks queues describe crm-tasks --location=europe-west1 --project=level-facility-479122-u4

# Verifica BACKEND_INTERNAL_URL (deve essere l'URL Cloud Run, non localhost)
gcloud run services describe crm-backend \
  --region=europe-west1 \
  --format="value(spec.template.spec.containers[0].env)"
```
