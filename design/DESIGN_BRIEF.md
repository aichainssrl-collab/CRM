# AiChain CRM — Design Brief per Grafico

**Versione:** 1.0  
**Data:** 2026-05-09  
**Progetto:** AiChain CRM — Fase 1  
**Stack frontend:** Next.js 14 App Router · shadcn/ui · Tailwind CSS

---

## 1. Obiettivo e posizionamento

Creare un CRM B2B enterprise che superi HubSpot in:

- **Chiarezza visiva**: meno rumore, più segnale — ogni pixel deve servire all'utente
- **Velocità percepita**: transizioni fluide, skeleton loader, ottimistic UI
- **Densità informativa controllata**: tabelle dense ma leggibili, non cramped
- **Gerarchia tipografica rigorosa**: l'utente deve capire dove guardare senza pensarci

Il tono visivo è **professionale, sobrio, moderno** — non colorato e rumoroso come HubSpot.  
Riferimenti estetici: Linear, Vercel Dashboard, Notion, Raycast.

---

## 2. Sistema di colori

### Palette primaria

| Token | Hex | Uso |
|---|---|---|
| `--primary` | `#1A1A2E` | Background sidebar, testo heading principale |
| `--primary-foreground` | `#FFFFFF` | Testo su primary |
| `--accent` | `#3B5BDB` | CTA primari, link attivi, badge informativi |
| `--accent-hover` | `#2F4AC4` | Stato hover accent |
| `--accent-light` | `#EEF2FF` | Background chip/badge accent, hover righe |

### Palette semantica

| Token | Hex | Uso |
|---|---|---|
| `--success` | `#2F9E44` | Deal vinto, status positivo |
| `--success-light` | `#EBFBEE` | Background badge successo |
| `--warning` | `#E67700` | Task in scadenza, azioni richieste |
| `--warning-light` | `#FFF9DB` | Background badge warning |
| `--destructive` | `#C92A2A` | Eliminazione, errori critici |
| `--destructive-light` | `#FFF5F5` | Background badge errore |
| `--neutral` | `#868E96` | Testo secondario, placeholder, icone inattive |

### Palette sfondo (light mode — default)

| Token | Hex | Uso |
|---|---|---|
| `--background` | `#F8F9FA` | Sfondo pagina |
| `--surface` | `#FFFFFF` | Card, panel, dialog |
| `--surface-raised` | `#FFFFFF` | Dropdown, popover (con shadow) |
| `--border` | `#E9ECEF` | Bordi sottili, divisori |
| `--border-strong` | `#CED4DA` | Bordi input focus |

> **Dark mode**: da progettare in fase 2. Per ora solo light mode.

---

## 3. Tipografia

**Font principale:** `Inter` (Google Fonts) — già ottimizzato per dashboard UI.

| Ruolo | Size | Weight | Line-height | Uso |
|---|---|---|---|---|
| `display` | 28px | 700 | 1.2 | Titoli pagina principali |
| `heading-1` | 22px | 600 | 1.3 | Section header, dialog title |
| `heading-2` | 18px | 600 | 1.3 | Card title, widget header |
| `heading-3` | 15px | 600 | 1.4 | Table header, group label |
| `body` | 14px | 400 | 1.5 | Testo corrente |
| `body-medium` | 14px | 500 | 1.5 | Label, valore enfatizzato |
| `small` | 12px | 400 | 1.5 | Timestamp, metadata, caption |
| `small-medium` | 12px | 500 | 1.5 | Badge text, chip |
| `mono` | 13px | 400 | 1.5 | ID Firestore, codice, hash |

---

## 4. Spaziatura e griglia

Sistema basato su multipli di `4px`:

```
4px   — gap micro (icona-testo)
8px   — gap small (elementi inline)
12px  — gap medium (elementi lista)
16px  — padding card, gap standard
24px  — padding sezione, gap componenti
32px  — margin sezione grande
48px  — margin pagina top
```

**Griglia pagina:**
- Sidebar: larghezza fissa `240px` (collassabile a `56px` icon-only)
- Content area: `max-width: 1280px`, centrata con padding `24px`
- Header topbar: altezza fissa `56px`

---

## 5. Layout globale

```
┌────────────────────────────────────────────────────┐
│  TOPBAR  (56px) — logo · breadcrumb · notifiche · avatar  │
├──────────┬─────────────────────────────────────────┤
│          │  PAGE HEADER  (titolo + azioni primarie)  │
│ SIDEBAR  ├─────────────────────────────────────────┤
│  (240px) │                                          │
│          │          CONTENT AREA                    │
│  nav     │          (scrollabile)                   │
│  items   │                                          │
│          │                                          │
└──────────┴─────────────────────────────────────────┘
```

### Sidebar

- Background: `--primary` (`#1A1A2E`)
- Sezioni: **CRM** (Dashboard, Lead, Deal, Contatti), **Strumenti** (Form, Prenotazioni, Email), **Impostazioni**
- Item attivo: background `--accent` con pill laterale sinistra 3px
- Icone: Lucide Icons (già incluse in shadcn/ui)
- Logo AiChain: in alto, height 32px, testo bianco
- Avatar utente + nome in basso (fixed bottom)
- Collassabile: mantieni tooltip su hover in icon-only mode

### Topbar

- Background: `--surface` bianco con border-bottom `--border`
- Sinistra: breadcrumb navigazione (es. `Lead / Mario Rossi`)
- Destra: icona notifiche · avatar + dropdown

---

## 6. Schermate principali da progettare

### 6.1 Dashboard (`/crm/dashboard`)

Layout a griglia fluida:

```
┌──────────┬──────────┬──────────┬──────────┐
│ KPI card │ KPI card │ KPI card │ KPI card │  (4 colonne)
├──────────┴──────────┼──────────┴──────────┤
│                     │                     │
│  Grafico pipeline   │  Lead recenti        │
│  (area chart)       │  (lista compatta)    │
│                     │                     │
├─────────────────────┴─────────────────────┤
│         Attività recenti (timeline)        │
└────────────────────────────────────────────┘
```

**KPI Card:**
- Numero grande (28px bold), label (12px neutral), delta rispetto al mese (freccia + %)
- Icona colorata 36x36 in alto destra
- Nessun bordo colorato — solo sfondo bianco e shadow sottile

### 6.2 Lead Table (`/crm/leads`)

Questa è la schermata più usata — deve essere eccellente.

**Header:**
- Titolo `Lead` + contatore `(847)`
- Barra azioni: `[+ Nuovo Lead]` (primary) · `[Importa CSV]` · `[Filtri]` · `[Colonne]` · `[Esporta]`
- Barra di ricerca full-width sotto (con icona search + placeholder `Cerca per nome, email, azienda...`)

**Tabella:**
- Righe: altezza `48px`, hover background `--accent-light`
- Colonne suggerite: `☐` · Avatar+Nome · Azienda · Email · Telefono · Status · Score · Assegnato · Ultima att. · `⋯`
- Status badge: pill colorata (colori semantici), testo `small-medium`
- Score: barra lineare mini (0-100, colore gradient verde) + numero
- Ordinamento: freccia inline nella colonna header, visibile solo su hover
- Paginazione: cursor-based — `← Precedente` / `Successivo →` con count `1–50 di 847`
- Selezione multipla: quando selezionate N righe, appare action bar sticky in fondo (`Assegna · Tag · Elimina · X`)
- Colonna azioni `⋯`: dropdown `Apri · Modifica · Assegna · Aggiungi attività · Elimina`

**Filtri panel** (drawer laterale destra, 320px):
- Filtri: Stato, Fonte, Data creazione, Assegnato a, Score range, Tags
- Ogni filtro è un accordion collassabile
- Footer: `[Pulisci filtri]` + `[Applica (12)]`

### 6.3 Lead Detail (`/crm/leads/[id]`)

Layout 2 colonne:

```
┌────────────────────────────┬──────────────┐
│  HEADER lead               │              │
│  Nome · Azienda · Actions  │  INFO CARD   │
├────────────────────────────┤  (dati core) │
│                            │              │
│  TABS:                     ├──────────────┤
│  Attività | Tasks | Deal   │  DEAL CARD   │
│  GDPR | Note               │  (pipeline)  │
│                            ├──────────────┤
│  CONTENT TAB ATTIVO        │  ASSEGNAZIONE│
│  (timeline o lista)        │              │
└────────────────────────────┴──────────────┘
```

- Colonna sinistra: `flex-1` (scrollabile)
- Colonna destra: `320px` fissa
- Timeline attività: icona tipo · timestamp · autore · descrizione — append-only visivo (nessun pulsante edit/delete)

### 6.4 Kanban Deal (`/crm/deals`)

Kanban orizzontale a colonne scorrevoli:

**Colonne pipeline (stages):**
`Nuovo → Qualificato → Proposta → Negoziazione → Chiuso Vinto → Chiuso Perso`

- Header colonna: nome stage + count + valore totale (es. `Proposta · 4 · €42.000`)
- Card deal: Nome deal · Azienda · Valore · Avatar assegnato · Data chiusura prevista
- Drag & drop tra colonne (cursore grab)
- Colonna `Chiuso Vinto`: header verde `--success-light`
- Colonna `Chiuso Perso`: header grigio, opacità ridotta sulle card
- Bottone `+ Nuovo deal` sotto ogni colonna

### 6.5 Form pubblico (`/f/[slug]`) — landing pubblica

- Layout centrato, max-width `560px`, sfondo `#F8F9FA`
- Logo AiChain in alto centrato
- Card bianca con padding `40px`
- Titolo form, descrizione opzionale
- Campi: label sopra, input shadcn/ui standard
- GDPR checkbox obbligatorio in fondo (testo legal, small)
- CTA: `[Invia richiesta]` — full width, primary
- Stato successo: icona check verde, messaggio ringraziamento (no redirect)

### 6.6 Prenotazioni (`/crm/bookings`)

- Vista calendario mensile (left) + lista prenotazioni (right)
- Slot disponibili evidenziati in verde pallido
- Slot prenotati: avatar prenotante + orario
- Dettaglio prenotazione: drawer destra con tutti i dati

---

## 7. Componenti UI ricorrenti

### Badge / Status pill

| Status | Background | Testo |
|---|---|---|
| Nuovo | `#EEF2FF` | `#3B5BDB` |
| Contattato | `#E3FAFC` | `#0C8599` |
| Qualificato | `#FFF9DB` | `#E67700` |
| Proposta inviata | `#F3F0FF` | `#7048E8` |
| Chiuso vinto | `#EBFBEE` | `#2F9E44` |
| Chiuso perso | `#F1F3F5` | `#868E96` |

Shape: `border-radius: 100px`, padding `2px 10px`, font `small-medium`.

### Input

- Height: `36px` (default), `32px` (compact)
- Border: `1px solid --border`
- Focus: `border-color: --accent`, `box-shadow: 0 0 0 3px rgba(59,91,219,0.12)`
- Error: `border-color: --destructive`
- Prefix icon: `16px`, colore `--neutral`

### Button

| Variant | Background | Testo | Uso |
|---|---|---|---|
| primary | `--accent` | bianco | CTA principale |
| secondary | `--surface` | `--primary` | border 1px | Azioni secondarie |
| ghost | trasparente | `--primary` | Azioni terziarie |
| destructive | `--destructive` | bianco | Eliminazione |

Height: `36px`, padding `8px 16px`, border-radius `8px`, font `body-medium`.  
Loading state: spinner inline a sinistra, testo invariato, disabled.

### Card

- Background: `--surface`
- Border: `1px solid --border`
- Border-radius: `12px`
- Shadow: `0 1px 3px rgba(0,0,0,0.08)`
- Padding: `20px`

### Dialog / Modal

- Overlay: `rgba(0,0,0,0.4)` backdrop
- Border-radius: `16px`
- Max-width: `480px` (small), `640px` (medium), `800px` (large)
- Header: titolo `heading-1` + X close button
- Footer: right-aligned `[Annulla] [Conferma]`
- Animazione: scale-in da `0.95` a `1.0` + fade-in (100ms)

### Empty state

- Illustrazione SVG minimal (lineare, monocromatica `--accent-light`)
- Titolo `heading-2`, descrizione `body neutral`
- CTA primary opzionale
- Centrato verticalmente nel contenitore
- Dimensioni illustrazione: `160px × 120px`

### Skeleton loader

- Usa `animate-pulse` (Tailwind) — background `#F1F3F5`
- Rispetta la forma del layout finale (non barre generiche)

---

## 8. Iconografia

**Libreria:** Lucide Icons (già integrata in shadcn/ui).

Dimensioni standard:
- `16px` — inline nel testo, badge
- `18px` — azioni tabella, dropdown
- `20px` — navigation sidebar
- `24px` — KPI card, header sezione

**Non** usare emoji o icon font alternativi.  
Stroke width: `1.5px` (default Lucide).

---

## 9. Microinterazioni

- **Row hover tabella**: background fade `0ms → 150ms ease`
- **Button click**: scale `1 → 0.97 → 1` (`80ms`)
- **Dialog open**: scale + fade `100ms ease-out`
- **Sidebar collapse**: slide + fade `200ms ease-in-out`
- **Toast notification**: slide-in da bottom-right `250ms`, auto-dismiss `4s`
- **Drag kanban card**: `box-shadow` elevato + rotazione `2deg`, placeholder grigio nella slot originale
- **Badge status change**: background e testo cross-fade `150ms`

---

## 10. Toast / Notifiche

Posizione: **bottom-right**, stack verticale (max 3 visibili).

| Tipo | Icona | Border-left |
|---|---|---|
| Success | `CheckCircle` verde | `--success` |
| Error | `XCircle` rosso | `--destructive` |
| Warning | `AlertTriangle` arancione | `--warning` |
| Info | `Info` blu | `--accent` |

---

## 11. Responsive

Il CRM è **desktop-first** (utenza B2B con PC/laptop).

| Breakpoint | Layout |
|---|---|
| `≥ 1280px` | Full layout, sidebar espansa |
| `1024–1280px` | Sidebar collassata icon-only |
| `768–1024px` | Sidebar come overlay drawer |
| `< 768px` | **Non supportato** in fase 1 — mostrare messaggio "Usa un desktop" |

---

## 12. Accessibilità (WCAG 2.1 AA)

- Contrasto testo/sfondo minimo **4.5:1** (verificare con Figma plugin Contrast)
- Focus ring visibile su tutti i componenti interattivi (non rimuovere mai `outline`)
- Tutte le icone standalone hanno `aria-label`
- Tabelle hanno `<caption>` e `scope` corretto
- Form fields hanno label associata (mai solo placeholder)

---

## 13. Deliverable richiesti al designer

### Figma

1. **Design system page**: colori, tipografia, spaziatura, griglia, icone
2. **Component library page**: tutti i componenti in §7 in tutti gli stati (default, hover, focus, disabled, error, loading)
3. **Schermate desktop (1440px canvas)**:
   - Dashboard
   - Lead Table (con filtri panel aperto)
   - Lead Detail
   - Kanban Deal
   - Form pubblico
   - Pagina prenotazioni
4. **Prototype** con navigazione base tra schermate
5. **Handoff**: annotazioni spacing + token CSS per sviluppatore

### Export

- Icone custom (se presenti): SVG ottimizzato
- Illustrazioni empty state: SVG, export anche come PNG @2x
- Naming layers: BEM-style (`lead-table__row--selected`)

---

## 14. Vincoli tecnici per il designer

- **NON** progettare componenti che non esistono in shadcn/ui — customizzare invece quelli esistenti
- **NON** usare font custom diversi da Inter — Google Fonts, già in bundle
- **NON** usare immagini raster per UI chrome
- **NON** aggiungere animazioni che richiedono librerie JS aggiuntive (solo CSS/Tailwind)
- I **colori devono usare i CSS token** di Tailwind/shadcn — non hardcodare hex nel codice
- Border-radius globale: `--radius: 8px` (shadcn default) — usarlo ovunque tranne pill (`100px`)

---

## 15. Riferimenti visivi

| Prodotto | Elemento da ispirarsi |
|---|---|
| **Linear** | Sidebar minimalista, tipografia, velocità percepita |
| **Vercel Dashboard** | KPI card, table layout, color palette neutra |
| **Notion** | Gerarchia contenuti, empty states, icone |
| **Raycast** | Microinterazioni, search experience |
| **Retool** | Densità informativa tabelle senza essere caotico |

**Non** ispirarsi a: HubSpot (troppo colorato), Salesforce (troppo pesante), Pipedrive (font troppo piccolo).

---

*Documento generato internamente — da condividere con il designer esterno come PDF/MD*
