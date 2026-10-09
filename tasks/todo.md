# Marketing Agent — Task List

## Fase 1: Fondazione + Agente Core

- [ ] **T1.1** Installazione Skills Marketing — Clonare skill da marketingskills in `.agents/skills/`, creare `product-marketing.md` per AiChain
- [ ] **T1.2** Backend — Marketing Agent Router + Service — Router FastAPI `/api/v1/marketing-agent/` con POST /chat, /generate, /analyze, GET /suggestions, /templates + service orchestratore LLM
- [ ] **T1.3** Backend — CRM Context Provider — Service che aggrega dati CRM (lead, deals, attività) come contesto per l'agente
- [ ] **T1.4** Backend — Content Generator Service — Generazione email sequences, copy, social posts, ad copy usando SKILL.md come guida
- [ ] **T1.5** Frontend — Marketing Agent Layout (Tab Structure) — Ridisegnare `/crm/marketing` con 4 tab: Agent, Content, Ads, Insights

### Checkpoint Fase 1
- [ ] Skills installate
- [ ] POST /chat funzionante
- [ ] Struttura tab operativa
- [ ] Dashboard Meta Ads nella tab Ads
- [ ] Build passa

## Fase 2: Agent Chat + Content Generation

- [ ] **T2.1** Frontend — Agent Chat — Chat completa con streaming, suggerimenti rapidi, storico conversazione
- [ ] **T2.2** Frontend — Content Generator Panel — Form per tipo contenuto + output anteprima + copia/salva
- [ ] **T2.3** Backend — Streaming Responses (SSE) — Server-Sent Events per risposte progressive
- [ ] **T2.4** Frontend — Insights Panel — Analisi CRO/SEO da URL

### Checkpoint Fase 2
- [ ] Chat con streaming funzionante
- [ ] Generazione contenuti operativa
- [ ] Insights CRO/SEO funzionante
- [ ] Conversazioni salvate in MongoDB
- [ ] UX fluida desktop/mobile

## Fase 3: Integrazione Avanzata

- [ ] **T3.1** Backend — Email Sequence Builder con Resend — Genera + invia email sequences via Resend EU
- [ ] **T3.2** Frontend — Email Sequence Builder UI — Drag & drop step, editor, preview, attivazione
- [ ] **T3.3** Backend — Suggerimenti Intelligenti — Analisi automatica CRM → suggerimenti actionable
- [ ] **T3.4** Frontend — Ads Intelligence — Analisi AI delle campagne Meta Ads

### Checkpoint Fase 3
- [ ] Email sequences con invio Resend
- [ ] Suggerimenti automatici dal CRM
- [ ] Meta Ads con AI insights
- [ ] Tutte le tab funzionanti

## Fase 4: Polish (opzionale)

- [ ] **T4.1** Content Library — Repository contenuti generati
- [ ] **T4.2** Marketing Templates — Template predefiniti per casi d'uso AiChain
- [ ] **T4.3** Competitor Intelligence — Analisi automatica competitor
- [ ] **T4.4** Marketing Calendar — Calendario editoriale