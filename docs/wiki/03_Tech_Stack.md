# 03 Tech Stack

## Frontend
- **Framework**: Next.js 14 (App Router)
- **Linguaggio**: TypeScript
- **Styling**: Tailwind CSS v3 + shadcn/ui design tokens (oklch color palette)
- **Design System**: Charter-inspired — navy primario, sfondo perla, card bianche
- **Componenti UI**: shadcn/ui (base-ui/react internamente) — **obbligatorio per tutti i componenti UI**
- **Data Fetching**: TanStack React Query v5
- **Form & Validazione**: react-hook-form + zod
- **Auth**: Firebase Auth SDK (Client) — solo per ottenere il JWT

## Backend
- **Framework**: FastAPI (Python 3.12)
- **Linguaggio**: Python
- **Validazione**: Pydantic v2
- **Database Driver**: motor (MongoDB Async)
- **Auth**: firebase-admin SDK — verifica JWT, non usa Firestore
- **Test**: pytest, pytest-asyncio
- **Porta**: 8088 (sviluppo locale)

## Database

### MongoDB
- **Driver**: motor (async)
- **Database name**: `crm-aichain-db`
- **Sviluppo locale**: Docker — `mongodb://localhost:27017`
- **Produzione**: MongoDB Atlas (o istanza self-hosted)

#### Avvio locale

```bash
# Prima installazione
docker run -d --name mongodb-crm -p 27017:27017 mongo:7
docker update --restart unless-stopped mongodb-crm

# Avvio normale
docker start mongodb-crm
```

> ⚠️ **Importante**: Firebase Auth è usato SOLO per l'autenticazione JWT.
> Tutti i dati applicativi (utenti, lead, deal, task) sono in MongoDB, non in Firestore.

## Auth
- **Firebase Auth**: emissione e verifica token JWT
- **Flusso**: Client ottiene JWT da Firebase → invia con ogni request → Backend verifica con firebase-admin → cerca utente in MongoDB `users` collection → se non trovato: 403

## Cloud & DevOps
- **Cloud**: Google Cloud Platform (europe-west1)
- **Container**: Docker (backend + MongoDB in locale)
- **CI/CD**: Cloud Build → Artifact Registry EU → Cloud Run
- **Email**: Resend API (server EU)
- **Storage**: Firebase Storage (europe-west1)
