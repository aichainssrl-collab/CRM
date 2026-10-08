# Setup locale — AiChain CRM

## Prerequisiti

- Docker (per MongoDB)
- Python 3.12+
- Node.js 18+
- Firebase CLI (`npm install -g firebase-tools`)

---

## 1. MongoDB (Docker)

Il database locale gira tramite Docker. **Docker deve essere avviato prima del backend.**
mongodb://02b5902a-e160-49f2-837f-cf3aa0855a75.europe-west1.firestore.goog:443/crm-aichain-db?loadBalanced=true&tls=true&retryWrites=false&authMechanism=MONGODB-OIDC&authMechanismProperties=ENVIRONMENT:gcp,TOKEN_RESOURCE:FIRESTORE


### Prima installazione

```bash
docker run -d \
  --name mongodb-crm \
  -p 27017:27017 \
  -e MONGO_INITDB_DATABASE=crm-aichain-db \
  mongo:7

# Auto-restart al riavvio del sistema
docker update --restart unless-stopped mongodb-crm
```

### Avvio normale (container già esistente)

```bash
docker start mongodb-crm

# Verifica
docker ps | grep mongodb-crm
```

### Connessione

```
URI:      mongodb://localhost:27017
Database: crm-aichain-db
```

### Seed dati iniziali

Dopo aver creato il container (o dopo `docker rm` + ricreazione), il DB è vuoto.
Inserire almeno gli utenti nella collection `users`:

```bash
# Accesso diretto a mongosh per inserimento manuale
docker exec -it mongodb-crm mongosh crm-aichain-db

# In mongosh:
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
```

> **⚠️ Senza utenti nel DB, il backend restituisce 403 su tutti gli endpoint autenticati.**

---

## 2. Backend (FastAPI)

```bash
cd backend
python -m venv venv
source venv/bin/activate         # macOS/Linux
# oppure: venv\Scripts\activate  # Windows

pip install -r requirements.txt
cp .env.example .env             # compilare con i valori dev

uvicorn app.main:app --host 0.0.0.0 --port 8088 --reload
# Docs: http://localhost:8088/api/docs
```

### Variabili d'ambiente backend (`.env`)

```env
FIREBASE_PROJECT_ID=aichain-crm-dev
GOOGLE_APPLICATION_CREDENTIALS_JSON=<json service account>
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB=crm-aichain-db
GCP_LOCATION=europe-west1
RESEND_API_KEY=re_...
ALLOWED_ORIGINS=["http://localhost:3000"]
```

---

## 3. Frontend (Next.js)

```bash
cd frontend
npm install
cp .env.example .env.local   # compilare con valori dev

npm run dev
# CRM: http://localhost:3000
```

### Variabili d'ambiente frontend (`.env.local`)

```env
NEXT_PUBLIC_FIREBASE_API_KEY=...
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=aichain-crm-dev.firebaseapp.com
NEXT_PUBLIC_FIREBASE_PROJECT_ID=aichain-crm-dev
NEXT_PUBLIC_API_BASE_URL=http://localhost:8088
```

---

## Ordine di avvio

```
1. docker start mongodb-crm
2. uvicorn app.main:app ... (backend)
3. npm run dev (frontend)
```

---

## Troubleshooting

### 403 su tutti gli endpoint

MongoDB non è avviato o la collection `users` è vuota.

```bash
docker ps | grep mongodb-crm           # verificare che sia running
docker start mongodb-crm               # avviarlo se fermo
docker exec -it mongodb-crm mongosh crm-aichain-db --eval "db.users.countDocuments()"
# Se 0 → eseguire seed utenti (vedi sopra)
```

### Porta 8088 già in uso

```bash
lsof -ti:8088 | xargs kill -9
```

### Container MongoDB rimosso accidentalmente

Ricreare con il comando `docker run` della sezione "Prima installazione", poi eseguire il seed.

---

## 4. Migrazione a Firestore Cloud

Per il deploy su Cloud Run, i dati vengono migrati da MongoDB locale a **Firestore Cloud**.

### Database Firestore

- **Project**: `level-facility-479122-u4`
- **Database**: `(default)`
- **URL**: https://console.firebase.google.com/project/level-facility-479122-u4/firestore

### Script di migrazione

```bash
cd backend
source venv/bin/activate

# Dry-run (verifica senza scrivere)
python migrate_to_firestore.py --dry-run

# Migrazione completa
python migrate_to_firestore.py --verify
```

### Opzioni

```bash
--dry-run            # Simula senza scrivere
--collection=leads   # Solo una collection specifica
--verify             # Verifica dopo migrazione
```

### Prerequisiti

```bash
# Autenticazione GCP
gcloud auth application-default login

# Abilitare API Firestore
gcloud services enable firestore.googleapis.com --project=level-facility-479122-u4
```

### Collections da migrare

| Collection | Documenti (stimati) |
|------------|---------------------|
| users | ~3 |
| leads | ~31 |
| deals | ~4 |
| activities | ~25 |
| tasks | ~4 |

---

## 5. Deploy su Cloud Run

### Prerequisiti

```bash
# Setup infrastruttura (una tantum)
./gcp/setup_infra.sh

# Autenticazione
gcloud auth login
gcloud auth configure-docker europe-west1-docker.pkg.dev
```

### Deploy

```bash
# Deploy completo
./scripts/deploy.sh

# Solo backend o frontend
./scripts/deploy.sh --backend-only
./scripts/deploy.sh --frontend-only

# Skip test
./scripts/deploy.sh --skip-tests
```

### Secret Manager

I seguenti secrets devono essere popolati in GCP Secret Manager:

- `firebase-credentials` - Service account Firebase
- `resend-api-key` - Chiave API Resend
- `mongodb-uri` - URI MongoDB OIDC (per Cloud Run)
- `apollo-api-key` - Chiave API Apollo (opzionale)
