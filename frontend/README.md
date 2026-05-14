# AiChain CRM - Frontend

Frontend applicativo per il CRM AiChain, sviluppato in React e Next.js.

## Prerequisiti
- Node.js >= 18
- npm o pnpm

## Configurazione Iniziale (MOLTO IMPORTANTE)

Per evitare l'errore `FirebaseError: Firebase: Error (auth/invalid-api-key)` o problemi di connessione API, **devi configurare correttamente le variabili d'ambiente**.

1. Crea un file `.env.local` nella root del frontend:
   ```bash
   cp .env.local.example .env.local
   ```

2. Assicurati che le variabili siano valorizzate con i dati corretti del progetto Firebase:

   ```env
   # API Backend
   NEXT_PUBLIC_API_URL=http://localhost:8000
   
   # Firebase Config (Richiesto per il Login!)
   NEXT_PUBLIC_FIREBASE_PROJECT_ID=level-facility-479122-u4
   NEXT_PUBLIC_FIREBASE_API_KEY=AIzaSY_SET_NEXT_PUBLIC_FIREBASE_API_KEY_ENV
   NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=level-facility-479122-u4.firebaseapp.com
   NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=level-facility-479122-u4.appspot.com
   NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=722754739274
   NEXT_PUBLIC_FIREBASE_APP_ID=1:722754739274:web:8c52d53d85d38f6b342b33
   ```

> ⚠️ **Attenzione:** Se non configuri correttamente `NEXT_PUBLIC_FIREBASE_API_KEY`, il login fallirà istantaneamente lato client ancor prima di contattare il backend.

## Avvio rapido

1. Installa le dipendenze:
   ```bash
   npm install
   ```

2. Avvia il server di sviluppo:
   ```bash
   npm run dev
   ```

3. Apri [http://localhost:3000](http://localhost:3000) nel browser.

## Troubleshooting

### `auth/invalid-api-key`
- **Causa**: La variabile `NEXT_PUBLIC_FIREBASE_API_KEY` è mancante o vuota.
- **Soluzione**: Controlla che il file `.env.local` sia presente e che contenga la chiave corretta. Se hai appena modificato il file `.env.local`, devi **riavviare il server Next.js** (ferma con CTRL+C e fai ripartire `npm run dev`).

### `net::ERR_CONNECTION_REFUSED` su porta `8002` o `8000`
- **Causa**: Il frontend sta cercando di contattare il backend, ma il backend non è in esecuzione, oppure l'URL configurato nel frontend è sbagliato.
- **Soluzione**: 
  1. Assicurati che il backend sia avviato (vedi `backend/README.md`).
  2. Verifica in `.env.local` che `NEXT_PUBLIC_API_URL` punti alla porta giusta (di default `http://localhost:8000`).

## Comandi disponibili

| Comando | Descrizione |
|---------|-------------|
| `npm run dev` | Avvia il server di sviluppo |
| `npm run build` | Compila per la produzione |
| `npm start` | Avvia il server di produzione |
| `npm run lint` | Esegue il linter per trovare errori di codice |
| `npm test` | Esegue la test suite |
