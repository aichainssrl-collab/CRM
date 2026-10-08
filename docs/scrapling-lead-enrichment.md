# Scrapling — Analisi e Piano di Implementazione per AiChain CRM

> **Obiettivo:** arricchire automaticamente i lead con dati aziendali e profilo
> estratti dal web, riducendo il lavoro manuale del team sales e aumentando
> la qualità dei dati nel CRM.

---

## Cos'è Scrapling

[Scrapling](https://github.com/D4Vinci/Scrapling) è una libreria Python (2024)
per web scraping adattivo. A differenza di BeautifulSoup o Scrapy:

| Caratteristica | BeautifulSoup | Scrapy | **Scrapling** |
|---|---|---|---|
| Velocità parsing | Lenta | Media | **Molto veloce** (selectolax) |
| Adattamento a cambi layout | ❌ | ❌ | ✅ Auto-match |
| Anti-detection built-in | ❌ | ❌ | ✅ |
| JS rendering | ❌ | Plugin | ✅ Playwright integrato |
| Selettori CSS/XPath | ✅ | ✅ | ✅ + smart selectors |
| Async nativo | ❌ | ✅ | ✅ |

### Feature chiave: Auto-Match

Il selettore "smart" memorizza l'elemento trovato e lo rileva automaticamente
anche se il sito cambia HTML. Utile per siti che aggiornano frequentemente
la struttura (LinkedIn, pagine aziendali).

```python
# Scrapling impara dove si trova l'elemento e si adatta ai cambi di layout
page = Fetcher().get("https://example.com")
employees = page.find("span.employee-count", auto_match=True)
```

---

## Caso d'uso nel CRM AiChain

### Il problema attuale

Quando arriva un nuovo lead (da form, import CSV, inserimento manuale), i campi
aziendali sono spesso vuoti o incompleti:

```
email:       mario.rossi@acmecorp.it   ✅
companyName: Acme Corp                  ✅
industry:    —                          ❌
companySize: —                          ❌
roleTitle:   —                          ❌
linkedinUrl: —                          ❌
website:     —                          ❌
technology:  —                          ❌
```

Il team sales perde tempo a ricercare manualmente queste info prima di ogni call.

### La soluzione: enrichment pipeline asincrona

```
Lead creato/aggiornato
        │
        ▼
Cloud Task: enrich-lead
        │
        ├─► Scrapling → Sito aziendale (dominio dall'email)
        │       └─► company description, size, industry, location, social links
        │
        ├─► Scrapling → LinkedIn Company Page (se trovata)
        │       └─► followers, specialties, founded year, HQ
        │
        └─► Scrapling → LinkedIn Profile (se linkedinUrl presente)
                └─► job title, seniority, connections, skills
                        │
                        ▼
                Aggiorna lead in MongoDB
                enrichedAt, enrichmentSource, campi arricchiti
```

---

## Dati che possiamo estrarre

### Da sito aziendale (`domain` estratto dall'email)

| Campo CRM | Fonte | Esempio |
|---|---|---|
| `companyName` | `<title>`, og:site_name | "Acme Corp Srl" |
| `industry` | Sezione About / meta description | "SaaS B2B" |
| `companySize` | Pagina About, footer | "50-100 dipendenti" |
| `website` | URL scrapped | "https://acmecorp.it" |
| `location` | Footer, contatti | "Milano, IT" |
| `linkedinUrl` | Social links nel footer | linkedin.com/company/acme |
| `twitterUrl` | Social links | — |
| `techStack` (customField) | Tag script, meta generator | WordPress, Shopify, HubSpot |
| `hasPrivacyPolicy` (customField) | Link footer | true/false (GDPR signal) |

### Da LinkedIn Company Page

| Campo CRM | Esempio |
|---|---|
| `numEmployeesRange` | "51-200" |
| `industry` | "Information Technology" |
| `companyDescription` (customField) | testo breve |
| `foundedYear` (customField) | 2018 |
| `linkedinFollowers` (customField) | 1.240 |
| `headquarters` (customField) | "Catania, Sicilia" |
| `specialties` (tags) | ["AI", "SaaS", "Legal Tech"] |

### Da LinkedIn Profile (se linkedinUrl fornito)

| Campo CRM | Esempio |
|---|---|
| `roleTitle` | "Head of Legal Operations" |
| `roleSeniority` | "senior" |
| `firstName` / `lastName` | da nome profilo |
| `connections` (customField) | "500+" |
| `skills` (tags) | ["Contract Management", "eIDAS"] |

---

## Architettura di integrazione

### Flusso async con Cloud Tasks (già in uso nel CRM)

```
POST /api/v1/leads          PATCH /api/v1/leads/{id}
         │                            │
         └──── enqueue_task("enrich-lead", {"lead_id": ...})
                                 │
                    Cloud Tasks (ritardo 10s, max 3 tentativi)
                                 │
                    POST /tasks/handlers/enrich-lead
                                 │
                    EnrichmentService.enrich(lead_id)
                                 │
                ┌────────────────┼────────────────┐
                │                │                │
         scrape_website    scrape_linkedin    (futuro: Apollo API)
                │                │
                └────────────────┘
                         │
                 merge_enrichment_data()
                         │
                 db["leads"].update_one(...)
                         │
                 enrichedAt, enrichmentSource = "scrapling"
```

### Modalità di fetch

Scrapling offre tre modalità. Scegliamo in base al target:

| Target | Modalità | Motivo |
|---|---|---|
| Sito aziendale statico | `Fetcher` (httpx) | Veloce, no JS necessario |
| Sito aziendale con JS | `PlaywrightFetcher` | Render completo |
| LinkedIn | `StealthyFetcher` | Anti-detection, headers realistici |

---

## Implementazione

### 1. Dipendenze da aggiungere

```bash
# backend/requirements.txt — aggiungere:
scrapling>=0.2.9
playwright>=1.44.0
```

```bash
# Post-install per Playwright (nel Dockerfile)
playwright install chromium --with-deps
```

### 2. EnrichmentService

```python
# backend/app/services/enrichment_service.py

import logging
import re
from urllib.parse import urlparse
from scrapling import Fetcher, StealthyFetcher, PlaywrightFetcher
from app.services.db_service import db, utcnow

logger = logging.getLogger(__name__)

# Tech stack fingerprinting — tag/script da cercare nel HTML
TECH_SIGNATURES = {
    "WordPress": ["wp-content", "wp-includes"],
    "Shopify": ["cdn.shopify.com", "Shopify.theme"],
    "HubSpot": ["hs-scripts.com", "hubspot"],
    "Salesforce": ["salesforce.com", "pardot"],
    "Webflow": ["webflow.com"],
    "Next.js": ["_next/static"],
    "React": ["react.development.js", "__react"],
    "Google Analytics": ["gtag", "google-analytics.com"],
    "Intercom": ["intercom.io"],
    "Typeform": ["typeform.com"],
}

SIZE_PATTERNS = [
    (r"(\d+)\s*[-–]\s*(\d+)\s*(dipendenti|employees|persone|people)", "range"),
    (r"(oltre|more than|oltre)\s*(\d+)\s*(dipendenti|employees)", "gt"),
    (r"(\d+)\s*(dipendenti|employees|persone|people)", "exact"),
    (r"(startup|early.stage)", "1-10"),
    (r"(pmi|pme|small business|piccola impresa)", "11-50"),
    (r"(media impresa|mid.market)", "51-200"),
]


def _extract_domain(email: str) -> str | None:
    """Estrae il dominio dall'email, esclude provider pubblici."""
    PUBLIC_DOMAINS = {
        "gmail.com", "yahoo.com", "hotmail.com", "outlook.com",
        "libero.it", "virgilio.it", "alice.it", "icloud.com",
        "protonmail.com", "tiscali.it", "live.com"
    }
    try:
        domain = email.split("@")[1].lower().strip()
        return None if domain in PUBLIC_DOMAINS else domain
    except IndexError:
        return None


def _detect_tech_stack(html: str) -> list[str]:
    found = []
    html_lower = html.lower()
    for tech, signatures in TECH_SIGNATURES.items():
        if any(sig.lower() in html_lower for sig in signatures):
            found.append(tech)
    return found


def _parse_employee_count(text: str) -> str | None:
    text_lower = text.lower()
    for pattern, fmt in SIZE_PATTERNS:
        m = re.search(pattern, text_lower)
        if m:
            if fmt == "range":
                return f"{m.group(1)}-{m.group(2)}"
            elif fmt == "gt":
                n = int(m.group(2))
                if n >= 1000: return "1000+"
                if n >= 200: return "201-1000"
                if n >= 50: return "51-200"
                return f"{n}+"
            elif fmt == "exact":
                n = int(m.group(1))
                if n <= 10: return "1-10"
                if n <= 50: return "11-50"
                if n <= 200: return "51-200"
                if n <= 1000: return "201-1000"
                return "1000+"
            else:
                return fmt
    return None


class EnrichmentService:

    async def enrich(self, lead_id: str) -> dict:
        """Entry point principale — arricchisce un lead e salva in MongoDB."""
        lead = await db["leads"].find_one({"_id": lead_id})
        if not lead:
            logger.warning("enrich: lead %s non trovato", lead_id)
            return {}

        updates: dict = {}

        # ── 1. Scraping sito aziendale ────────────────────────────────────────
        domain = _extract_domain(lead.get("email", ""))
        if domain:
            try:
                site_data = await self._scrape_website(domain)
                updates.update(site_data)
            except Exception as e:
                logger.warning("scrape_website %s failed: %s", domain, e)

        # ── 2. Scraping LinkedIn Profile ──────────────────────────────────────
        linkedin_url = lead.get("linkedinUrl") or updates.get("linkedinUrl")
        if linkedin_url and "linkedin.com/in/" in linkedin_url:
            try:
                li_data = await self._scrape_linkedin_profile(linkedin_url)
                # Non sovrascrivere campi già presenti nel lead originale
                for k, v in li_data.items():
                    if not lead.get(k) and v:
                        updates[k] = v
            except Exception as e:
                logger.warning("scrape_linkedin_profile %s failed: %s", linkedin_url, e)

        # ── 3. Scraping LinkedIn Company ──────────────────────────────────────
        company_li_url = updates.get("companyLinkedinUrl") or lead.get("customFields", {}).get("companyLinkedinUrl")
        if company_li_url:
            try:
                co_data = await self._scrape_linkedin_company(company_li_url)
                for k, v in co_data.items():
                    if not lead.get(k) and v:
                        updates[k] = v
            except Exception as e:
                logger.warning("scrape_linkedin_company %s failed: %s", company_li_url, e)

        if not updates:
            logger.info("enrich: nessun dato estratto per lead %s", lead_id)
            return {}

        # ── Salva in MongoDB ──────────────────────────────────────────────────
        updates["enrichedAt"] = utcnow()
        updates["enrichmentSource"] = "scrapling"
        updates["updatedAt"] = utcnow()

        await db["leads"].update_one(
            {"_id": lead_id},
            {"$set": updates}
        )
        logger.info("enrich: lead %s arricchito con %d campi", lead_id, len(updates))
        return updates

    async def _scrape_website(self, domain: str) -> dict:
        """Scraping del sito aziendale. Estrae info chiave senza JS."""
        url = f"https://{domain}"
        fetcher = Fetcher(auto_match=True)

        try:
            page = fetcher.get(url, timeout=15, stealthy_headers=True)
        except Exception:
            # Fallback a HTTP
            page = fetcher.get(f"http://{domain}", timeout=15, stealthy_headers=True)

        data: dict = {"website": url}

        # Titolo e descrizione
        title = page.find("title")
        og_desc = page.find('meta[property="og:description"]')
        meta_desc = page.find('meta[name="description"]')

        description = (
            og_desc.attrib.get("content") if og_desc else
            meta_desc.attrib.get("content") if meta_desc else None
        )

        # Cerca link LinkedIn aziendale nel footer/header
        for a in page.find_all("a[href*='linkedin.com/company']"):
            href = a.attrib.get("href", "")
            if "linkedin.com/company/" in href:
                data["customFields.companyLinkedinUrl"] = href
                break

        # Cerca numero dipendenti nel testo della pagina
        full_text = page.find("body").text if page.find("body") else ""
        size = _parse_employee_count(full_text)
        if size:
            data["companySize"] = size

        # Tech stack
        html_raw = str(page.html) if hasattr(page, "html") else ""
        tech = _detect_tech_stack(html_raw)
        if tech:
            data["customFields.techStack"] = tech

        # Privacy policy (GDPR signal)
        has_privacy = bool(page.find_all("a[href*='privacy']"))
        data["customFields.hasPrivacyPolicy"] = has_privacy

        # Lingua del sito (approssimazione)
        html_el = page.find("html")
        if html_el:
            lang = html_el.attrib.get("lang", "")
            if lang:
                data["customFields.siteLanguage"] = lang[:2].lower()

        return {k: v for k, v in data.items() if v is not None}

    async def _scrape_linkedin_profile(self, url: str) -> dict:
        """
        Scraping profilo LinkedIn personale.
        Usa StealthyFetcher per evitare il blocco.
        ⚠️  LinkedIn richiede login per i dati completi.
              Questa implementazione funziona con la vista pubblica.
        """
        fetcher = StealthyFetcher(auto_match=True)
        page = fetcher.get(url, timeout=20)

        data: dict = {}

        # Nome
        name_el = page.find("h1")
        if name_el:
            parts = name_el.text.strip().split(" ", 1)
            if len(parts) >= 1 and not data.get("firstName"):
                data["firstName"] = parts[0]
            if len(parts) >= 2 and not data.get("lastName"):
                data["lastName"] = parts[1]

        # Titolo job
        headline = page.find(".text-body-medium")
        if headline:
            data["roleTitle"] = headline.text.strip()

        # Location
        location = page.find(".text-body-small.inline")
        if location:
            data["customFields.location"] = location.text.strip()

        # Seniority — inferita dal titolo
        if data.get("roleTitle"):
            title_lower = data["roleTitle"].lower()
            if any(w in title_lower for w in ["ceo", "cto", "coo", "founder", "co-founder", "president"]):
                data["roleSeniority"] = "c-level"
            elif any(w in title_lower for w in ["vp", "vice president", "director", "direttore"]):
                data["roleSeniority"] = "vp"
            elif any(w in title_lower for w in ["head", "manager", "responsabile", "lead"]):
                data["roleSeniority"] = "manager"
            elif any(w in title_lower for w in ["senior", "sr."]):
                data["roleSeniority"] = "senior"
            elif any(w in title_lower for w in ["junior", "jr.", "intern", "stage"]):
                data["roleSeniority"] = "junior"
            else:
                data["roleSeniority"] = "mid"

        return {k: v for k, v in data.items() if v}

    async def _scrape_linkedin_company(self, url: str) -> dict:
        """Scraping pagina aziendale LinkedIn (vista pubblica)."""
        fetcher = StealthyFetcher(auto_match=True)
        page = fetcher.get(url, timeout=20)

        data: dict = {}

        # Numero dipendenti
        for el in page.find_all("dd"):
            text = el.text.strip()
            size = _parse_employee_count(text)
            if size:
                data["numEmployeesRange"] = size
                break

        # Industry
        industry_el = page.find('[data-test-id="about-us__industry"]')
        if industry_el:
            data["industry"] = industry_el.text.strip()

        # Followers
        follower_el = page.find("span.org-top-card-summary-info-list__info-item")
        if follower_el and "follower" in follower_el.text.lower():
            data["customFields.linkedinFollowers"] = follower_el.text.strip()

        # Specialties → tags
        spec_el = page.find('[data-test-id="about-us__specialties"]')
        if spec_el:
            specialties = [s.strip() for s in spec_el.text.split(",") if s.strip()]
            if specialties:
                data["tags"] = specialties[:5]  # max 5 tag

        return {k: v for k, v in data.items() if v}
```

### 3. Task handler

```python
# backend/app/tasks/handlers.py — aggiungere:

from app.services.enrichment_service import EnrichmentService

@router.post("/enrich-lead")
async def handle_enrich_lead(request: Request):
    await verify_cloud_tasks_request(request)
    payload = await request.json()
    lead_id = payload.get("lead_id")
    if not lead_id:
        return {"success": False, "reason": "missing lead_id"}

    service = EnrichmentService()
    updates = await service.enrich(lead_id)
    return {"success": True, "fields_updated": list(updates.keys())}
```

### 4. Trigger automatico alla creazione del lead

```python
# backend/app/routers/leads.py — modifica create_lead:

@router.post("", status_code=201)
async def create_lead(data: LeadCreate, user: UserRecord = Depends(require_sales)):
    service = LeadService()
    existing = await service.find_by_email(data.email)
    if existing:
        raise HTTPException(409, f"Lead con email {data.email} già presente")

    lead = await service.create_lead(data, created_by=user.uid)
    # Score
    await enqueue_task("recalculate-score", {"lead_id": lead["id"]})
    # Enrichment automatico (ritardo 5s per non appesantire la risposta)
    await enqueue_task("enrich-lead", {"lead_id": lead["id"]}, delay_seconds=5)
    return lead
```

### 5. Endpoint manuale per ri-enrichare un lead

```python
# backend/app/routers/leads.py — aggiungere:

@router.post("/{lead_id}/enrich")
async def enrich_lead_now(
    lead_id: str,
    user: UserRecord = Depends(require_sales),
):
    """Forza re-enrichment di un lead specifico (utile dalla UI)."""
    await enqueue_task("enrich-lead", {"lead_id": lead_id})
    return {"message": "Enrichment avviato, i dati saranno disponibili tra pochi secondi"}
```

### 6. Dockerfile — aggiungi Playwright

```dockerfile
# backend/Dockerfile — aggiungere dopo pip install:
RUN playwright install chromium --with-deps
```

---

## Gestione rate limiting e rispetto robots.txt

```python
# backend/app/services/enrichment_service.py — aggiungere:

import asyncio
import urllib.robotparser

_domain_delays: dict[str, float] = {}  # ultimo scraping per dominio

async def _respect_rate_limit(domain: str, min_delay: float = 3.0):
    """Attende almeno min_delay secondi tra due scraping sullo stesso dominio."""
    last = _domain_delays.get(domain, 0)
    elapsed = asyncio.get_event_loop().time() - last
    if elapsed < min_delay:
        await asyncio.sleep(min_delay - elapsed)
    _domain_delays[domain] = asyncio.get_event_loop().time()

def _is_allowed_by_robots(url: str) -> bool:
    """Verifica robots.txt prima di fare scraping."""
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    rp = urllib.robotparser.RobotFileParser()
    rp.set_url(robots_url)
    try:
        rp.read()
        return rp.can_fetch("*", url)
    except Exception:
        return True  # se non leggibile, procedi
```

---

## Confronto con Apollo.io (già nel CRM)

Il modello `LeadModel` ha già campi Apollo (`apolloId`, `apolloScore`).
Scrapling e Apollo si **complementano**, non si escludono:

| Capacità | Apollo API | Scrapling |
|---|---|---|
| Costo | ~$0.05/lead | Gratuito (solo infra) |
| Dati email verificate | ✅ | ❌ |
| Dati aziendali strutturati | ✅ | Parziale |
| Tech stack del sito | ❌ | ✅ |
| Privacy policy / GDPR signal | ❌ | ✅ |
| Dati real-time (sito aggiornato) | ❌ | ✅ |
| LinkedIn profile data | Parziale | ✅ (vista pubblica) |
| Rate limit | 10.000/mese (piano base) | Dipende dal target |
| Dati personalizzati per il settore | ❌ | ✅ (customizzabile) |

**Strategia consigliata:**
1. **Scrapling** → enrichment gratuito immediato (sito, tech stack, LinkedIn pubblico)
2. **Apollo** → enrichment a pagamento per lead qualificati (email verificata, telefono)

---

## Dati sensibili e GDPR

- Scrapiamo **solo dati pubblicamente accessibili** (pagine pubbliche, profili LinkedIn pubblici)
- Non memorizziamo HTML grezzo — solo i campi estratti
- Tutti i dati sono collegati al consenso GDPR del lead (già gestito dalla collection `gdpr_consents`)
- `enrichmentSource: "scrapling"` traccia l'origine del dato per audit
- Il campo `enrichedAt` permette di sapere quando i dati sono stati raccolti

---

## Piano di implementazione

### Sprint A — Sito aziendale (1-2 giorni)

- [ ] Aggiungere `scrapling` a `requirements.txt`
- [ ] Creare `backend/app/services/enrichment_service.py` con `_scrape_website()`
- [ ] Aggiungere handler Cloud Task `enrich-lead` in `handlers.py`
- [ ] Aggiungere trigger in `create_lead` (delay 5s)
- [ ] Aggiungere endpoint `POST /leads/{id}/enrich`
- [ ] Test con 5 lead reali

### Sprint B — LinkedIn pubblico (2-3 giorni)

- [ ] Aggiungere `playwright install chromium` al Dockerfile
- [ ] Implementare `_scrape_linkedin_profile()` con `StealthyFetcher`
- [ ] Implementare `_scrape_linkedin_company()`
- [ ] Test anti-detection (User-Agent rotation, delays)
- [ ] Gestione errori 429 (rate limit LinkedIn)

### Sprint C — UI nel CRM (1 giorno)

- [ ] Badge "Arricchito" nella scheda lead (con data `enrichedAt`)
- [ ] Pulsante "Arricchisci" nella scheda lead → chiama `POST /leads/{id}/enrich`
- [ ] Mostrare tech stack e specialties come tag nella scheda
- [ ] Filtro leads: "Non arricchiti" per identificare i lead da processare

### Sprint D — Monitoring (0.5 giorni)

- [ ] Log strutturati: `fields_updated`, `enrichment_source`, `duration_ms`
- [ ] Alert se tasso di fallimento enrichment > 30%
- [ ] Dashboard Cloud Tasks per monitorare la queue

---

## Struttura file finale

```
backend/
└── app/
    ├── services/
    │   └── enrichment_service.py   ← nuovo
    ├── routers/
    │   └── leads.py                ← aggiungere trigger + endpoint /enrich
    └── tasks/
        └── handlers.py             ← aggiungere handler enrich-lead
```

---

## Rischi e mitigazioni

| Rischio | Probabilità | Impatto | Mitigazione |
|---|---|---|---|
| LinkedIn blocca lo scraping | Alta | Medio | StealthyFetcher + delays + fallback graceful |
| Sito aziendale con JS pesante | Media | Basso | PlaywrightFetcher come fallback |
| Dati estratti errati (false match) | Media | Basso | Enrich solo se confidence > soglia; non sovrascrivere dati esistenti |
| Playwright aumenta dimensioni Docker | Certezza | Basso | `--only-shell` in prod, Chromium headless minimal |
| Throttling Cloud Tasks | Bassa | Basso | min-backoff già configurato a 10s |
| robots.txt disallow | Media | Nessuno | Controllo robots.txt preventivo |
