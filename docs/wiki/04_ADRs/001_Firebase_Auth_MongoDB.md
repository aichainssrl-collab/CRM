# ADR-001: Architettura Ibrida Firebase Auth + MongoDB

## Status
Accepted

## Date
2026-05-14

## Context
Per il CRM AiChain avevamo bisogno di un sistema robusto per gestire l'identità degli utenti (password, reset, 2FA futuri, etc) e contemporaneamente di un database flessibile per la complessa struttura dei Lead, Deal e Attività.
Mentre l'idea iniziale era di usare l'intero ecosistema Firebase (Auth + Firestore), ci siamo scontrati con le limitazioni di Firestore riguardanti aggregazioni complesse e query articolate, necessarie per il motore del CRM.

## Decision
Abbiamo adottato un modello ibrido:
- **Identità (Login/Token)**: Affidata interamente a **Firebase Authentication**.
- **Dati e Profili (Storage)**: Affidati interamente a **MongoDB**.

**Come funziona nel codice:**
1. Il client (Next.js) si autentica con Firebase e ottiene un JWT.
2. Il client invia il JWT come Bearer Token a FastAPI.
3. Il backend usa l'Admin SDK di Firebase **solo** per decodificare il token e ottenere l'`UID`.
4. Il backend usa quell'`UID` per interrogare la collezione `users` su **MongoDB** e ottenere permessi, ruoli e dati dell'utente.

*In nessuna parte del sistema Firestore o Firebase Realtime DB devono essere utilizzati.*

## Alternatives Considered
- **Tutto su Firebase (Auth + Firestore)**
  - *Pro*: Stack omogeneo, integrazione client-side diretta.
  - *Contro*: Firestore scala male per query relazionali o aggregazioni complesse (es. filtri avanzati sui lead).
  - *Scartata*: Per i limiti del database.
- **Tutto Custom (JWT custom + MongoDB)**
  - *Pro*: Nessuna dipendenza da Google.
  - *Contro*: Dover implementare a mano reset password, validazione email, sicurezza delle password.
  - *Scartata*: Reinventare la ruota per la gestione dell'identità avrebbe rallentato la Fase 1.

## Consequences
- **Pro**: Otteniamo il meglio dei due mondi: gestione sicura dell'identità senza sforzo (Firebase) e query illimitate e veloci (MongoDB).
- **Contro**: Potenziale confusione per i nuovi sviluppatori o per gli agenti AI, che potrebbero presumere erroneamente che essendo in uso Firebase, anche i dati vadano scritti in Firestore (motivo per cui è nato questo ADR a seguito di un errore di runtime).
- **Azione richiesta**: Ogni nuova dipendenza legata agli utenti deve sempre sincronizzare i dati su MongoDB usando l'UID di Firebase come chiave primaria.
