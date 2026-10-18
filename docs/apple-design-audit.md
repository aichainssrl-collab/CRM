# Audit design front-end CRM — ispirazione Apple Store (buy-home)

**Riferimento:** https://www.apple.com/it/shop/buy-home  
**Principi:** *Designing Fluid Interfaces* + Apple 8 principles (skill `apple-design`)  
**Data:** 2026-10-18 · Stack: Next.js 14 · shadcn/ui · Tailwind · palette «Charter»

---

## Cosa fa bene Apple (buy-home)

| Aspetto | Apple Shop Home |
|---|---|
| Gerarchia | Titoli display grandi («Acquista Apple Home»), sottotitoli corti |
| Card prodotto | Superfici morbide, molto spazio, foto grande, CTA chiara |
| Ritmo | Sezioni ampie, footer denso solo in fondo |
| Navigazione | Chrome leggero, icone silenziose, focus sul contenuto |
| CTA | Pattern ripetuto: etichetta + «Acquista / Preordina / Scopri» |
| Tag | «NOVITÀ» piccoli, non urlati |
| Materiali | Bianco/grigio caldo, ombre morbide, poco bordo duro |
| Tipografia | Tracking ottico (titoli stretti, body leggibile) |

Il CRM è uno **strumento operativo**, non un catalogo: non va *copiato* 1:1, ma si prende **spazio, morbidezza, gerarchia e feedback**.

---

## Problemi trovati (per gravità)

### P1 — Motion «da computer», non fluida
| Problema | Dove | Principio Apple |
|---|---|---|
| Solo `transition-all duration-150 ease-out` | `button.tsx`, card | Springs + velocity (§4–5) |
| Nessun `prefers-reduced-motion` | intero frontend | §14 |
| Sheet/dialog non interruptible a gesture | `sheet.tsx`, picker | §3 Interruptibility |
| Nessun rubber-band / momentum | kanban, liste orizzontali | §6, §9 |
| Feedback su `click`, non su `:active` parziale | bottoni custom, righe tabella | §1 Response |

**Da tenere:** `active:scale-[0.97]` sui bottoni è già in direzione giusta.

### P2 — Superfici troppo «piatte / bordate»
| Problema | Apple | CRM oggi |
|---|---|---|
| `--radius: 0.5rem` | card ~18–22px+ | angoli piccoli |
| `border` 1px grigio ovunque | quasi solo ombra soft | `border` su ogni card |
| Poco `backdrop-filter` | navbar/toolbar translucent | solo sheet overlay |
| Stack ombre incoerente | pesi diversi per livello | `shadow-sm/xs` quasi uniformi |

### P3 — Tipografia e spazio
| Problema | Nota |
|---|---|
| `tracking-tight` su **ogni** `h1` | ok sui display, sbagliato su testo piccolo |
| `font-bold` vs `font-semibold` mescolati a caso | es. dashboard `bold`, agent `semibold` |
| Titoli solo `text-2xl` | Apple scala di più i titoli di sezione |
| Densità KPI/table alta | poco «respiro» nelle card metriche |
| Empty state deboli | Apple usa copy + spazio + un’azione chiara |

### P4 — Consistenza e wayfinding
| Problema | Nota |
|---|---|
| Pattern CTA diversi | «Salva», «Crea», icona + testo, solo icona |
| Sidebar pesante + navbar + palette cmd-k | 3 livelli di chrome (Apple: 1–2) |
| Badge/stato non allineati | pipeline vs leads vs task |
| Tab settings lunghi | Profile / Agente / Skill / Goal / Notifiche… |

### P5 — Accessibilità
| Manca | Impatto |
|---|---|
| `prefers-reduced-transparency` | blur non riducibile |
| `prefers-contrast: more` | bordi/token insufficienti |
| Focus ring su tutte le surface | alcuni `outline-none` senza alternativa |
| Hit target < 44px su alcuni icon-button | mobile |

---

## Piano di restyle «Apple Home» (applicato al CRM)

### 1. Token (globals.css)
```css
--radius: 1rem;          /* card più morbide */
--radius-lg: 1.25rem;
--shadow-card: 0 1px 2px rgb(12 20 69 / 0.04), 0 8px 24px rgb(12 20 69 / 0.06);
--font-display: clamp(1.75rem, 2.5vw + 1rem, 2.5rem);
```
- Bordi: quasi solo su input/liste; le card vivono di **ombra + fill**.
- Navbar/sidebar: `backdrop-filter: blur(16px) saturate(180%)` + fill 70%.

### 2. Tipografia
```css
.display { font-size: var(--font-display); line-height: 1.1; letter-spacing: -0.025em; }
.section-title { font-size: 1.35rem; letter-spacing: -0.015em; }
.body { line-height: 1.55; letter-spacing: 0; }
```
- Un solo stack weight per ruolo: display `600`, body `400`, label `500`.
- Spacing in `rem` per Dynamic Type.

### 3. Card & KPI (stile «product tile»)
- Padding più generoso (`p-5` / `p-6`), **meno righe per card**.
- KPI: numero grande + label corta + micro-trend (come «NOVITÀ»).
- Hover: legger lift (`translateY(-1px)` + ombra), non solo colore.
- Raggio maggiore su card «hero» (dashboard top), minore su tabelle dense.

### 4. Motion
| Uso | Valore |
|---|---|
| Press | `scale(0.98)` su `:active`, 100ms |
| Card hover | spring critico (`bounce: 0`, 0.3–0.4s) |
| Sheet/drawer | `damping 0.8`, `response 0.3` + velocity release |
| Enter list | fade + 4–8px rise, stagger ≤ 30ms |
| Reduced motion | solo opacity 200ms |

### 5. Navigazione
- Un solo chrome primario (sidebar **o** top bar, non entrambi densi).
- Sezioni dashboard come «shop sections»: titolo + sottotitolo + griglia.
- CTA primaria sempre stessa forma/posizione (destra alto o in card).

### 6. Materiali
- Sheet/dialog: scrim + blur, enter blur+scale insieme.
- Table: niente doppio bordo card+riga.
- Scroll edge: fade blur su header sticky, non `border-b` duro.

---

## Quick-win (1–2 gg)

1. `--radius` → `0.875rem` / card `1rem` + `shadow-card`
2. `prefers-reduced-motion` globale in `globals.css`
3. Titoli pagina → `text-[1.75rem] leading-[1.1] tracking-[-0.025em]`
4. KpiCard: più spazio, numero `text-3xl`, label uppercase 11px (come LeadDetail)
5. Navbar: blur + `bg-background/70`
6. Uniformare `font-semibold` sui titoli pagina

## Media (2–4 gg)
- Restyle empty state (icona grande, copy, CTA)
- Sheet con drag-to-dismiss + velocity (Motion)
- Badge di stato tokenizzati
- Focus-visible ovunque + hit target 44px

## Out of scope
- Copiare layout shop Apple (foto prodotto, griglia merchandising)
- Animazioni decorative non legate al gesto

---

## Esito

| Aspetto | Voto /10 | Note |
|---|---|---|
| Gerarchia | 7 | titoli ok, manca scala display |
| Spazio / respiro | 5 | denso come dashboard, poco «shop» |
| Superfici / materiali | 5 | bordi duri, poco blur |
| Motion / feedback | 4 | CSS only, no spring/velocity |
| Consistenza | 6 | shadcn salva, custom UI disallineate |
| A11y / reduced motion | 3 | quasi assente |

**Priorità:** materiali + tipografia + reduced-motion (quick-win), poi gesture/sheet.

*Documento operativo di design — usare come backlog UI.*
