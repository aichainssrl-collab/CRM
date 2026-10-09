# Piano di Implementazione: Marketing Agent per AiChain CRM

## Overview

Trasformare la sezione marketing del CRM (attualmente un semplice dashboard Meta Ads) in un **AI Marketing Agent** completo, ispirato al progetto open-source [marketingskills](https://github.com/coreyhaines31/marketingskills) (53.7k stelle). L'agente integrerà 50+ capacità marketing organizzate per categorie (CRO, SEO, Email, Cold Outreach, Social, Ads, Copywriting, Analytics) e le collegherà ai dati CRM esistenti (lead, deals, attività) per fornire raccomandazioni e generazione di contenuti contestualizzati.

### Cosa cambia nella UX

**Prima (oggi):** Pagina "Marketing" = tabella campagne Meta Ads + KPI spend/CTR/CPC.

**Dopo:** Sezione "Marketing Agent" con:
1. **Chat AI** — interfaccia conversazionale per richiedere analisi, copy, strategie
2. **Capabilities** — schede per ogni dominio marketing (Email, SEO, CRO, Ads, Social, Cold Outreach)
3. **Dashboard** — il vecchio Meta Ads dashboard integrato come tab "Ads Intelligence"
4. **Templates** — generatore di contenuti marketing (email sequences, ad copy, landing page copy, social posts)

---

## Architettura

```
┌─────────────────────────────────────────────────────────────────┐
│                    FRONTEND (Next.js App Router)                 │
│                                                                 │
│  /crm/marketing  (pagina ridisegnata)                          │
│  ├── Tab "Agent"     → Chat con AI Marketing Agent             │
│  ├── Tab "Content"   → Generatore contenuti (email/copy/social)│
│  ├── Tab "Ads"       → Dashboard Meta Ads (esistente)          │
│  └── Tab "Insights"  → Analisi CRO/SEO/recommendations         │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                   BACKEND (FastAPI)                              │
│                                                                 │
│  /api/v1/marketing-agent/                                      │
│  ├── POST /chat          → Chat con l'agente                   │
│  ├── POST /generate       → Genera contenuti (email/copy/...)  │
│  ├── POST /analyze        → Analizza URL per CRO/SEO           │
│  ├── GET  /suggestions    → Suggerimenti basati su dati CRM    │
│  └── GET  /templates      → Template disponibili               │
│                                                                 │
│  /api/v1/meta/ (esistente, mantenuto)                          │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                   SERVIZI                                        │
│                                                                 │
│  marketing_agent_service.py  → Orchestrazione agente            │
│  content_generator.py        → Generazione contenuti            │
│  cro_analyzer.py             → Analisi CRO pagine               │
│  email_sequence_builder.py   → Costruzione sequenze email       │
│  crm_context_provider.py     → Contesto da lead/deals/activities│
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                   DATI                                           │
│                                                                 │
│  MongoDB: marketing_conversations, marketing_templates,         │
│           marketing_campaigns, content_library                  │
│                                                                 │
│  .agents/skills/  → SKILL.md (conoscenza marketing)            │
└─────────────────────────────────────────────────────────────────┘
```

---

## Decisioni Architetturali

1. **LLM Backend**: Usare il servizio OpenAI (già configurato nel progetto) per alimentare l'agente. Il system prompt carica le SKILL.md rilevanti come contesto.

2. **Knowledge come Skills**: Le SKILL.md del repo marketingskills diventano la "base di conoscenza" dell'agente. Non installiamo il repo come submodule — estraiamo le skill più rilevanti e le adattiamo al contesto AiChain.

3. **Integrazione CRM**: L'agente accede ai dati CRM (lead, deals, attività, form submissions) per generare raccomandazioni personalizzate. Esempio: "Analizza i lead degli ultimi 30 giorni e suggerisci una email sequence di nurturing."

4. **Persistenza conversazioni**: Le conversazioni con l'agente vengono salvate in MongoDB per continuità.

5. **Generazione contenuti**: Output in formato markdown, copiabile e salvabile nella content library.

6. **Meta Ads**: Il router esistente resta invariato. L'agente può accedere ai dati Meta Ads per analisi avanzate.

---

## Skills da integrare (priorità)

### Fase 1 — Core (più usate)
| Skill | Cosa fa | Rilevanza per AiChain |
|-------|---------|----------------------|
| `product-marketing` | Contesto prodotto/ICP/positioning | Fondazione per tutte le altre |
| `copywriting` | Copy per landing page, homepage, feature page | Richiesta frequente |
| `emails` | Sequenze email (welcome, nurture, re-engagement) | Integrazione Resend già esistente |
| `cro` | Analisi conversioni su pagine web | Ottimizzazione form pubblici |
| `cold-email` | Email B2B outbound | Per il team sales |

### Fase 2 — Growth
| Skill | Cosa fa | Rilevanza |
|-------|---------|-----------|
| `seo-audit` | Audit SEO tecnico e on-page | Per sito AiChain |
| `social` | Contenuti social media | LinkedIn/Twitter per brand |
| `analytics` | Setup tracking eventi | GA4 integration |
| `ads` | Campagne Google/Meta/LinkedIn | Espansione Meta Ads esistente |
| `marketing-plan` | Piano marketing completo AARRR | Strategia |

### Fase 3 — Avanzate
| Skill | Cosa fa |
|-------|---------|
| `launch` | Piani di lancio prodotto |
| `pricing` | Strategia pricing/packaging |
| `ab-testing` | Design esperimenti A/B |
| `referrals` | Programmi referral |
| `competitors` | Analisi competitor |

---

## Task List

### Fase 1: Fondazione + Agente Core (Sprint 1)

#### Task 1.1: Installazione Skills Marketing
**Description:** Clonare le skill rilevanti dal repo marketingskills e posizionarle in `.agents/skills/` del progetto CRM. Creare un `product-marketing.md` per AiChain Solutions.

**Acceptance criteria:**
- [ ] Skill files `.agents/skills/product-marketing/SKILL.md` presente
- [ ] Skill files `.agents/skills/copywriting/SKILL.md` presente
- [ ] Skill files `.agents/skills/emails/SKILL.md` presente
- [ ] Skill files `.agents/skills/cro/SKILL.md` presente
- [ ] Skill files `.agents/skills/cold-email/SKILL.md` presente
- [ ] `.agents/product-marketing.md` compilato con contesto AiChain Solutions

**Files likely touched:**
- `.agents/skills/` (nuovo)
- `.agents/product-marketing.md` (nuovo)

**Estimated scope:** Small

---

#### Task 1.2: Backend — Marketing Agent Router + Service
**Description:** Creare il router FastAPI `/api/v1/marketing-agent/` con endpoint per chat, generazione contenuti, analisi. Implementare il service layer che orchestra le chiamate LLM con il contesto delle skills.

**Acceptance criteria:**
- [ ] Router `backend/app/routers/marketing_agent.py` con endpoint POST `/chat`, `/generate`, `/analyze`, GET `/suggestions`, `/templates`
- [ ] Service `backend/app/services/marketing_agent_service.py` che:
  - Carica le SKILL.md come system context
  - Accede ai dati CRM per contesto (lead, deals, attività)
  - Gestisce la conversazione (multi-turn)
  - Salva conversazioni in MongoDB
- [ ] Schema Pydantic per request/response in `backend/app/schemas/marketing_agent.py`
- [ ] Registrazione router in `backend/app/main.py`
- [ ] Test: endpoint /chat risponde con contesto marketing

**Files likely touched:**
- `backend/app/routers/marketing_agent.py` (nuovo)
- `backend/app/services/marketing_agent_service.py` (nuovo)
- `backend/app/schemas/marketing_agent.py` (nuovo)
- `backend/app/main.py` (modifica)

**Dependencies:** Task 1.1 (skills installate)
**Estimated scope:** Large

---

#### Task 1.3: Backend — CRM Context Provider
**Description:** Creare un service che aggrega dati CRM (lead, deals, attività, form submissions) come contesto per l'agente marketing. Esempio: "Ultimi 30 lead → industrie, fonti, score, stato pipeline."

**Acceptance criteria:**
- [ ] Service `backend/app/services/crm_context_provider.py`
- [ ] Funzione `get_marketing_context()` che restituisce:
  - Statistiche lead (per periodo, fonte, industria, score)
  - Statistiche deals (pipeline, conversion rate, deal medio)
  - Attività recenti (tipo, outcome)
  - Form submissions (tipo, completamento)
- [ ] Funzione `get_lead_insights()` per analisi specifiche
- [ ] Integrazione nel marketing_agent_service

**Files likely touched:**
- `backend/app/services/crm_context_provider.py` (nuovo)
- `backend/app/services/marketing_agent_service.py` (modifica)

**Dependencies:** None (usa dati CRM esistenti)
**Estimated scope:** Medium

---

#### Task 1.4: Backend — Content Generator Service
**Description:** Service per generazione contenuti marketing: email sequences, copy (headline, CTA, body), social posts, ad copy. Usa il framework delle SKILL.md come guida.

**Acceptance criteria:**
- [ ] Service `backend/app/services/content_generator.py`
- [ ] Funzioni:
  - `generate_email_sequence(type, audience, goal)` → sequenza email completa
  - `generate_copy(type, product, audience)` → copy per pagina/annuncio
  - `generate_social_post(platform, topic, tone)` → post social
  - `generate_ad_copy(platform, product, audience)` → copy per ads
- [ ] Ogni funzione usa la SKILL.md corrispondente come system prompt
- [ ] Output formattato (markdown strutturato, campi separati)

**Files likely touched:**
- `backend/app/services/content_generator.py` (nuovo)
- `backend/app/schemas/marketing_agent.py` (modifica)

**Dependencies:** Task 1.2
**Estimated scope:** Medium

---

#### Task 1.5: Frontend — Marketing Agent Layout (Tab Structure)
**Description:** Ridisegnare la pagina `/crm/marketing` con struttura a tab: Agent (chat), Content (generatore), Ads (dashboard esistente), Insights (analisi).

**Acceptance criteria:**
- [ ] Layout con 4 tab (Agent, Content, Ads, Insights)
- [ ] Tab "Ads" mostra il contenuto esattamente uguale alla pagina attuale
- [ ] Tab "Agent" ha placeholder per chat
- [ ] Tab "Content" ha placeholder per generatore
- [ ] Tab "Insights" ha placeholder per analisi
- [ ] Navigazione tab fluida, responsive mobile
- [ ] Usare componenti shadcn/ui (Tabs, Card, etc.)

**Files likely touched:**
- `frontend/app/[locale]/crm/marketing/page.tsx` (modifica completa)
- `frontend/components/crm/marketing/AgentChat.tsx` (nuovo)
- `frontend/components/crm/marketing/ContentGenerator.tsx` (nuovo)
- `frontend/components/crm/marketing/AdsDashboard.tsx` (nuovo — estratto da page.tsx)
- `frontend/components/crm/marketing/InsightsPanel.tsx` (nuovo)

**Dependencies:** None (può essere fatto in parallelo con backend)
**Estimated scope:** Large

---

### Checkpoint: Fase 1 Completata
- [ ] Skills marketing installate
- [ ] Backend marketing agent risponde a POST /chat
- [ ] Frontend mostra la nuova struttura a tab
- [ ] Dashboard Meta Ads funzionante nella tab "Ads"
- [ ] Build frontend passa senza errori

---

### Fase 2: Agent Chat + Content Generation (Sprint 2)

#### Task 2.1: Frontend — Componente Agent Chat
**Description:** Implementare la chat conversazionale completa: messaggi utente, risposte agente (streaming), suggerimenti rapidi, storia conversazione.

**Acceptance criteria:**
- [ ] Componente `AgentChat.tsx` con:
  - Input testuale + invio
  - Bubble messaggi utente/agente
  - Streaming risposte (SSE o polling)
  - Suggerimenti rapidi ("Analizza i miei lead", "Scrivi una email sequence", "CRO check")
  - Storico conversazione (carica da MongoDB)
  - Loading state con skeleton
- [ ] Hook `useMarketingAgent.ts` per API calls
- [ ] Supporto markdown nelle risposte dell'agente

**Files likely touched:**
- `frontend/components/crm/marketing/AgentChat.tsx` (completamento)
- `frontend/hooks/useMarketingAgent.ts` (nuovo)
- `frontend/app/[locale]/crm/marketing/page.tsx` (integrazione)

**Dependencies:** Task 1.2, Task 1.5
**Estimated scope:** Large

---

#### Task 2.2: Frontend — Content Generator Panel
**Description:** Interfaccia per generare contenuti marketing: form per specificare tipo, audience, obiettivo; output con anteprima + copia + salva.

**Acceptance criteria:**
- [ ] Componente `ContentGenerator.tsx` con:
  - Select tipo contenuto (Email Sequence, Landing Page Copy, Social Post, Ad Copy)
  - Campi dinamici per tipo (audience, product, tone, platform)
  - Pulsante "Genera"
  - Output formattato con anteprima
  - Pulsante "Copia" e "Salva in Content Library"
- [ ] Hook `useContentGenerator.ts`
- [ ] Integrazione con backend `/api/v1/marketing-agent/generate`

**Files likely touched:**
- `frontend/components/crm/marketing/ContentGenerator.tsx` (completamento)
- `frontend/hooks/useContentGenerator.ts` (nuovo)

**Dependencies:** Task 1.4, Task 1.5
**Estimated scope:** Medium

---

#### Task 2.3: Backend — Streaming Responses (SSE)
**Description:** Implementare Server-Sent Events per le risposte dell'agente in streaming, così l'utente vede la risposta apparire progressivamente.

**Acceptance criteria:**
- [ ] Endpoint POST `/api/v1/marketing-agent/chat` supporta streaming SSE
- [ ] Token inviati progressivamente al frontend
- [ ] Fallback a response completa se SSE non supportato
- [ ] Frontend gestisce SSE con EventSource o fetch + ReadableStream

**Files likely touched:**
- `backend/app/routers/marketing_agent.py` (modifica)
- `frontend/hooks/useMarketingAgent.ts` (modifica)

**Dependencies:** Task 1.2, Task 2.1
**Estimated scope:** Medium

---

#### Task 2.4: Frontend — Insights Panel (CRO/SEO)
**Description:** Pannello "Insights" che permette di inserire un URL e ricevere un'analisi CRO/SEO dell'agente.

**Acceptance criteria:**
- [ ] Componente `InsightsPanel.tsx` con:
  - Input URL
  - Select tipo analisi (CRO, SEO, Competitor)
  - Risultato strutturato (score, raccomandazioni prioritarie, quick wins)
  - Grafici semplici per metriche (opzionale)
- [ ] Integrazione con backend `/api/v1/marketing-agent/analyze`

**Files likely touched:**
- `frontend/components/crm/marketing/InsightsPanel.tsx` (completamento)

**Dependencies:** Task 1.5
**Estimated scope:** Medium

---

### Checkpoint: Fase 2 Completata
- [ ] Chat agente funzionante con streaming
- [ ] Generazione contenuti (email, copy, social) funzionante
- [ ] Insights CRO/SEO da URL funzionante
- [ ] Conversazioni salvate e ripristinabili
- [ ] UX fluida su desktop e mobile

---

### Fase 3: Integrazione Avanzata + Features (Sprint 3)

#### Task 3.1: Backend — Email Sequence Builder con Resend
**Description:** Integrare la generazione di email sequences con l'invio effettivo via Resend (già configurato). L'agente genera la sequence, l'utente può attivarla.

**Acceptance criteria:**
- [ ] Service `backend/app/services/email_sequence_builder.py`
- [ ] Genera email sequence → salva in MongoDB
- [ ] Endpoint per attivare/disattivare una sequence
- [ ] Integrazione Resend per invio (EU server)
- [ ] Tracking aperture/click di base

**Files likely touched:**
- `backend/app/services/email_sequence_builder.py` (nuovo)
- `backend/app/routers/marketing_agent.py` (modifica)

**Dependencies:** Task 1.4, esistenza Resend config
**Estimated scope:** Large

---

#### Task 3.2: Frontend — Email Sequence Builder UI
**Description:** Interfaccia dedicata per creare e gestire email sequences: drag & drop step, editor email, preview, attivazione.

**Acceptance criteria:**
- [ ] Componente `EmailSequenceBuilder.tsx`
- [ ] Lista step con drag & drop riordinamento
- [ ] Editor per ogni email (subject, body, delay)
- [ ] Preview email (render HTML)
- [ ] Toggle attivazione sequence
- [ ] Statistiche (inviate, aperture, click)

**Files likely touched:**
- `frontend/components/crm/marketing/EmailSequenceBuilder.tsx` (nuovo)

**Dependencies:** Task 3.1
**Estimated scope:** Large

---

#### Task 3.3: Backend — Suggerimenti Intelligenti da CRM
**Description:** Endpoint che analizza i dati CRM e genera suggerimenti automatici: "Hai 15 lead freddi da 30+ giorni → invia re-engagement", "Tasso conversione form booking sceso 20% → CRO check consigliato."

**Acceptance criteria:**
- [ ] GET `/api/v1/marketing-agent/suggestions` ritorna lista suggerimenti
- [ ] Ogni suggerimento ha: tipo, priorità, titolo, descrizione, azione consigliata
- [ ] Logica:
  - Lead stagnanti → suggerisci email re-engagement
  - Form con basso tasso → suggerisci CRO check
  - Deal persi → suggerisci analisi competitor
  - Campagne Meta con CTR basso → suggerisci nuovo ad copy
  - Nuovi lead senza follow-up → suggerisci cold email sequence
- [ ] Frontend mostra suggerimenti come card actionable nella tab Agent

**Files likely touched:**
- `backend/app/services/crm_context_provider.py` (modifica)
- `backend/app/routers/marketing_agent.py` (modifica)
- `frontend/components/crm/marketing/AgentChat.tsx` (modifica — suggerimenti)

**Dependencies:** Task 1.3
**Estimated scope:** Medium

---

#### Task 3.4: Frontend — Ads Intelligence (Meta Ads potenziati)
**Description:** Potenziare il dashboard Meta Ads esistente con analisi AI: l'agente analizza le campagne e suggerisce ottimizzazioni.

**Acceptance criteria:**
- [ ] Sezione "AI Insights" sotto il grafico trend
- [ ] L'agente analizza dati Meta e produce:
  - Campagne sotto/sopra performanti
  - Suggerimenti budget reallocation
  - Suggerimenti nuove audience
  - Copy alternativo per ads
- [ ] Pulsante "Analizza con AI" accanto al pulsante "Aggiorna"

**Files likely touched:**
- `frontend/components/crm/marketing/AdsDashboard.tsx` (modifica)
- `frontend/hooks/useMarketingAgent.ts` (modifica)

**Dependencies:** Task 1.5, Task 2.1
**Estimated scope:** Medium

---

### Checkpoint: Fase 3 Completata
- [ ] Email sequence builder con Resend funzionante
- [ ] Suggerimenti intelligenti dal CRM operativi
- [ ] Meta Ads con analisi AI integrata
- [ ] Tutte le tab del marketing agent funzionanti

---

### Fase 4: Polish + Features Avanzate (Sprint 4, opzionale)

#### Task 4.1: Content Library
**Description:** Repository di tutti i contenuti generati dall'agente, ricercabili e riutilizzabili.

#### Task 4.2: Marketing Templates
**Description:** Template predefiniti per i casi d'uso più comuni di AiChain (demo follow-up, event follow-up, cold outreach legal/FinTech).

#### Task 4.3: Competitor Intelligence
**Description:** Analisi automatica competitor tramite web scraping + LLM analysis.

#### Task 4.4: Marketing Calendar
**Description:** Calendario editoriale con piani contenuti, deadline, reminder.

---

## Rischi e Mitigazioni

| Rischio | Impatto | Mitigazione |
|---------|---------|-------------|
| Costi LLM elevati per chat continua | Medio | Cache risposte, limita contesto, usa modelli più economici per task semplici |
| Skills troppo generiche per settore AiChain | Medio | Adattare le SKILL.md al contesto legal/FinTech/PA nelle prime fasi |
| Complessità SSE streaming | Basso | Fallback a response completa; polling come alternativa |
| Performance con molte skill caricate | Basso | Caricare solo skill rilevanti per la richiesta, non tutte |
| Dati CRM insufficienti per suggerimenti | Medio | Suggerimenti "cold start" con best practices generiche |

---

## Stack Tecnico Confermato

| Layer | Tecnologia | Note |
|-------|-----------|------|
| Frontend chat | React + shadcn/ui | Tabs, Card, ScrollArea, Button |
| Frontend streaming | EventSource / fetch ReadableStream | SSE per risposte progressive |
| Backend router | FastAPI | Async, Pydantic v2 |
| LLM | OpenAI API (configurata) | System prompt = SKILL.md context |
| Storage conversazioni | MongoDB | Collection `marketing_conversations` |
| Content library | MongoDB | Collection `content_library` |
| Email sending | Resend API (EU) | Già integrato nel progetto |
| Skills knowledge | .agents/skills/*.md | Da repo marketingskills |
| Meta Ads | Graph API (esistente) | Router meta_ads.py invariato |

---

## Metriche di Successo

1. **Adozione**: L'utente interagisce con l'agente almeno 3x/settimana
2. **Contenuti generati**: 10+ email/copy generati nelle prime 2 settimane
3. **Tempo risparmiato**: Riduzione tempo creazione email sequence da 2h a 10min
4. **Conversioni**: Miglioramento CTR form pubblici dopo suggerimenti CRO
5. **Pipeline**: 5+ lead nurtured con email sequence generate dall'agente

---

## Open Questions

1. **LLM model**: Quale modello usare per l'agente? (GPT-4o per qualità, GPT-4o-mini per costi)
2. **Rate limiting**: Quante richieste/giorno per utente?
3. **Multi-lingua**: Le risposte dell'agente devono essere solo in italiano o anche inglese?
4. **Permessi**: Solo admin possono usare l'agente o anche sales?
5. **Web scraping per CRO**: L'agente deve poter fetchare URL esterni per analisi?