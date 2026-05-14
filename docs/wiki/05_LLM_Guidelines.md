# 05 LLM Guidelines

Queste linee guida sono destinate agli agenti AI (come Claude, GPT, o altri LLM) che lavorano su questo repository.

## 1. Mantieni Aggiornata la Wiki
Ogni volta che implementi un nuovo modulo significativo, modifichi l'architettura o prendi una decisione tecnica rilevante, **devi aggiornare questa Wiki**.
- Se è una decisione architetturale, crea un nuovo file in `04_ADRs/`.
- Se modifichi lo stack o aggiungi un componente chiave, aggiorna `03_Tech_Stack` o `02_Architecture`.

## 2. Leggi prima di Scrivere
Prima di iniziare a implementare logiche complesse, consulta la Wiki per capire il contesto, specialmente per logiche condivise (es. autenticazione Firebase, servizi MongoDB).

## 3. Best Practices del Progetto
- Usa sempre il tool `Read` o `SearchCodebase` per capire le convenzioni esistenti prima di creare nuovi file.
- Non duplicare le chiamate API, usa `apiClient` in `lib/api.ts` per il frontend.
- Non bypassare i middleware di sicurezza (es. `require_sales` in FastAPI).
- Evita di scrivere commenti ridondanti nel codice; usa la Wiki o gli ADR per spiegare il *perché* di decisioni complesse.
