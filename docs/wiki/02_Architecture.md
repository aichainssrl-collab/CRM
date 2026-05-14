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

## Database (MongoDB)
- Database NoSQL per la flessibilità dei dati (Lead, Form, GDPR log, Activities).
- La comunicazione avviene tramite `motor` (driver asincrono MongoDB) wrappato in `app/services/db_service.py` (o `app/mongodb.py` a seconda del refactoring).

## Infrastruttura Cloud (GCP/Firebase)
- **Firebase Auth**: Gestione identità utenti.
- **GCP Cloud Tasks**: (In configurazione) per la gestione di code asincrone, invio email, ricalcolo scoring, ecc.
