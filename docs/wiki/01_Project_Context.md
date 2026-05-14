# 01 Project Context

## Cos'è AiChain CRM
AiChain CRM è un sistema di Customer Relationship Management progettato per l'azienda AiChain. Il sistema ha l'obiettivo di gestire l'intero ciclo di vita del cliente, dall'acquisizione dei lead (anche tramite form o CSV) fino alla gestione di deal, task, e meeting.

## Moduli Principali (Fase 1)
- **Lead Management**: Creazione, importazione (CSV), e tracciamento delle attività sui lead.
- **Form & GDPR**: Gestione dei form di contatto pubblici, raccolta dei consensi (GDPR) e tracciamento.
- **Booking**: Prenotazione di slot per appuntamenti integrata nel sistema.
- **Task & Activity**: Gestione dei task assegnati agli utenti (sales) e tracciamento delle attività fatte sui lead.

## Utenti e Ruoli
- **Admin**: Accesso completo al sistema, inclusa l'eliminazione dei lead e la gestione degli utenti.
- **Sales**: Gestione quotidiana di lead, task e meeting.

## Sicurezza e Autenticazione
Il sistema utilizza Firebase Authentication per gestire l'identità degli utenti, validando i token JWT lato backend tramite middleware di FastAPI.
