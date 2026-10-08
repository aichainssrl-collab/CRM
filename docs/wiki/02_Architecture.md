# 02 Architecture

Il sistema segue un'architettura **Client-Server** con un frontend Single Page Application (SSR/SSG via Next.js) e un backend API RESTful.

## Frontend (Next.js)
- Applicazione React basata su Next.js (App Router).
- Gestione dello stato e fetching dei dati con **React Query** (TanStack Query).
- Componenti UI basati su **shadcn/ui** e Tailwind CSS.
- Chiamate API autenticate usando `axios` e token JWT di Firebase passati come Bearer token.

## Backend (FastAPI)
- API REST scritta in Python con **FastAPI**.
- Architettura divisa in layer:
  - `routers/`: Controller che definiscono gli endpoint API.
  - `services/`: Business logic e interazione con il database.
  - `schemas/`: Modelli Pydantic per validazione di input e output.
  - `models/`: Modelli dati (quando applicabile).
- **Rate Limiting** configurato tramite `slowapi`.
- **Autenticazione**: Middleware che verifica i token Firebase e popola `UserRecord`.

## Sicurezza e Autenticazione (⚠️ Firebase vs MongoDB)
**ATTENZIONE:** Il sistema adotta un modello ibrido molto specifico che separa l'identità dai dati.
1. **Firebase Authentication**: È usato *esclusivamente* per la generazione dei token JWT e la verifica dell'identità.
2. **MongoDB**: Contiene i profili utente reali, i ruoli e **tutti** i dati dell'applicazione.

Il middleware di FastAPI (`app/deps.py`) prende il token da Firebase, ne verifica la firma (per capire l'UID) ma poi interroga **sempre e solo MongoDB** per ottenere le autorizzazioni, i ruoli e lo stato dell'utente. 
*Non tentare mai di usare Firestore o il DB di Firebase per memorizzare dati.*

## Database (MongoDB)
- Database NoSQL per la flessibilità dei dati (Lead, Form, GDPR log, Activities).
- La comunicazione avviene tramite `motor` (driver asincrono MongoDB) wrappato in `app/services/db_service.py` (o `app/mongodb.py` a seconda del refactoring).

## Infrastruttura Cloud (GCP/Firebase)
- **Firebase Auth**: Gestione identità utenti.
- **GCP Cloud Tasks**: (In configurazione) per la gestione di code asincrone, invio email, ricalcolo scoring, ecc.
