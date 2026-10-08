"""
EnrichmentService — Arricchimento automatico dei lead via web scraping (Scrapling).

Flusso:
  1. Estrae il dominio dall'email del lead
  2. Scraping del sito aziendale (httpx, veloce, no JS)
  3. Scraping profilo LinkedIn personale (StealthyFetcher, anti-detection)
  4. Scraping pagina LinkedIn aziendale (se trovata al passo 2)
  5. Merge dei dati in MongoDB senza sovrascrivere campi già compilati manualmente

Non sovrascrive mai campi già presenti nel documento originale del lead.
"""

import asyncio
import logging
import re
import time
import urllib.robotparser
from urllib.parse import urlparse

from app.services.db_service import db, utcnow

logger = logging.getLogger(__name__)

# ── Costanti ──────────────────────────────────────────────────────────────────

PUBLIC_EMAIL_DOMAINS = {
    "gmail.com", "yahoo.com", "yahoo.it", "hotmail.com", "hotmail.it",
    "outlook.com", "outlook.it", "libero.it", "virgilio.it", "alice.it",
    "tiscali.it", "icloud.com", "me.com", "live.com", "live.it",
    "protonmail.com", "proton.me", "fastmail.com", "tutanota.com",
    "aol.com", "msn.com", "tin.it", "email.it",
}

# Fingerprint per rilevamento tech stack
TECH_SIGNATURES: dict[str, list[str]] = {
    "WordPress":       ["wp-content/", "wp-includes/", "wp-json"],
    "Shopify":         ["cdn.shopify.com", "Shopify.theme", "myshopify.com"],
    "HubSpot":         ["hs-scripts.com", "hubspot.com", "hbspt"],
    "Salesforce":      ["salesforce.com", "pardot.com", "force.com"],
    "Webflow":         ["webflow.com", "wf-form"],
    "Next.js":         ["_next/static", "__NEXT_DATA__"],
    "Nuxt.js":         ["__nuxt", "_nuxt/"],
    "React":           ["react.development.js", "react.production.min.js"],
    "Vue.js":          ["vue.runtime", "vue.min.js"],
    "Angular":         ["ng-version", "angular.min.js"],
    "Google Analytics":["gtag(", "google-analytics.com", "GA_TRACKING"],
    "Google Tag Manager":["googletagmanager.com/gtm.js"],
    "Intercom":        ["intercom.io", "Intercom("],
    "Drift":           ["drift.com", "driftt.com"],
    "Crisp":           ["crisp.chat", "CRISP_WEBSITE_ID"],
    "Zendesk":         ["zendesk.com", "zopim"],
    "Stripe":          ["js.stripe.com"],
    "Typeform":        ["typeform.com"],
    "Calendly":        ["calendly.com"],
    "ActiveCampaign":  ["activehosted.com"],
    "Mailchimp":       ["list-manage.com", "mailchimp.com"],
    "Pipedrive":       ["pipedriveassets.com"],
}

# Pattern per estrarre numero dipendenti da testo libero
SIZE_PATTERNS = [
    (r"(\d{1,5})\s*[-–]\s*(\d{1,5})\s*(dipendenti|employees|persone|people|collaboratori)", "range"),
    (r"(oltre|more than|oltre i|più di)\s*(\d{1,5})\s*(dipendenti|employees|persone)", "gt"),
    (r"(\d{1,5})\+\s*(dipendenti|employees|persone)", "gt_simple"),
    (r"(\d{1,5})\s*(dipendenti|employees|persone|people)", "exact"),
    (r"\b(startup|early.?stage|early stage)\b", "1-10"),
    (r"\b(pmi|sme|piccola impresa|small business)\b", "11-50"),
    (r"\b(media impresa|mid.?market|midmarket)\b", "51-200"),
]

# Delay minimo tra richieste allo stesso dominio (secondi)
DOMAIN_MIN_DELAY = 3.0
_domain_last_hit: dict[str, float] = {}


# ── Helpers ────────────────────────────────────────────────────────────────────

def _extract_domain(email: str) -> str | None:
    try:
        domain = email.split("@")[1].lower().strip()
        return None if domain in PUBLIC_EMAIL_DOMAINS else domain
    except (IndexError, AttributeError):
        return None


def _is_robots_allowed(url: str, user_agent: str = "CRMBot/1.0") -> bool:
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    rp = urllib.robotparser.RobotFileParser()
    rp.set_url(robots_url)
    try:
        rp.read()
        return rp.can_fetch(user_agent, url)
    except Exception:
        return True


async def _rate_limit(domain: str) -> None:
    last = _domain_last_hit.get(domain, 0.0)
    wait = DOMAIN_MIN_DELAY - (time.monotonic() - last)
    if wait > 0:
        await asyncio.sleep(wait)
    _domain_last_hit[domain] = time.monotonic()


def _detect_tech_stack(html: str) -> list[str]:
    found = []
    for tech, sigs in TECH_SIGNATURES.items():
        if any(sig in html for sig in sigs):
            found.append(tech)
    return found


def _parse_employee_count(text: str) -> str | None:
    t = text.lower()
    for pattern, fmt in SIZE_PATTERNS:
        m = re.search(pattern, t)
        if m:
            if fmt == "range":
                lo, hi = int(m.group(1)), int(m.group(2))
                if hi <= 10:    return "1-10"
                if hi <= 50:    return "11-50"
                if hi <= 200:   return "51-200"
                if hi <= 1000:  return "201-1000"
                return "1000+"
            elif fmt in ("gt", "gt_simple"):
                n = int(m.group(2) if fmt == "gt" else m.group(1))
                if n >= 1000: return "1000+"
                if n >= 200:  return "201-1000"
                if n >= 50:   return "51-200"
                if n >= 10:   return "11-50"
                return "1-10"
            elif fmt == "exact":
                n = int(m.group(1))
                if n <= 10:   return "1-10"
                if n <= 50:   return "11-50"
                if n <= 200:  return "51-200"
                if n <= 1000: return "201-1000"
                return "1000+"
            else:
                return fmt  # stringa diretta (es. "1-10" per startup)
    return None


def _infer_seniority(title: str) -> str:
    t = title.lower()
    if any(w in t for w in ["ceo", "cto", "coo", "cfo", "cmo", "ciso",
                              "founder", "co-founder", "cofunder", "owner",
                              "president", "managing director", "amministratore"]):
        return "c-level"
    if any(w in t for w in ["vp ", "vice president", "vice presidente",
                              "svp", "evp", "director", "direttore"]):
        return "vp"
    if any(w in t for w in ["head of", "head,", "manager", "responsabile",
                              "lead ", "principal", "team lead"]):
        return "manager"
    if any(w in t for w in ["senior", "sr.", "sr "]):
        return "senior"
    if any(w in t for w in ["junior", "jr.", "jr ", "intern", "stage",
                              "trainee", "associate"]):
        return "junior"
    return "mid"


def _extract_linkedin_company_url(page_html: str) -> str | None:
    """Cerca link linkedin.com/company/ nel HTML della pagina."""
    m = re.search(r'https?://(?:www\.)?linkedin\.com/company/([a-zA-Z0-9\-_]+)/?', page_html)
    return m.group(0).rstrip("/") if m else None


# ── Scrapling import con fallback graceful ────────────────────────────────────

def _get_fetchers():
    """
    Importa Scrapling. Se non installato, ritorna None e logga warning.
    Questo evita crash del backend se scrapling non è ancora in requirements.
    """
    try:
        from scrapling import Fetcher, StealthyFetcher
        return Fetcher, StealthyFetcher
    except ImportError:
        logger.warning(
            "scrapling non installato — enrichment disabilitato. "
            "Aggiungi 'scrapling' a requirements.txt e riavvia."
        )
        return None, None


# ── EnrichmentService ─────────────────────────────────────────────────────────

class EnrichmentService:

    async def enrich(self, lead_id: str) -> dict:
        """
        Arricchisce un lead con dati estratti dal web.
        Salva i risultati in MongoDB e ritorna il dizionario dei campi aggiornati.
        Non sovrascrive campi già compilati nel documento originale.
        """
        Fetcher, StealthyFetcher = _get_fetchers()
        if not Fetcher:
            return {}

        lead = await db["leads"].find_one({"_id": lead_id})
        if not lead:
            logger.warning("enrich: lead %s non trovato", lead_id)
            return {}

        accumulated: dict = {}

        # ── Passo 1: sito aziendale ───────────────────────────────────────────
        domain = _extract_domain(lead.get("email", ""))
        if domain:
            try:
                site_data = await self._scrape_website(domain, Fetcher)
                accumulated.update(site_data)
                logger.info("enrich[%s]: sito %s → %d campi", lead_id, domain, len(site_data))
            except Exception as e:
                logger.warning("enrich[%s]: _scrape_website(%s) fallito: %s", lead_id, domain, e)

        # ── Passo 2: profilo LinkedIn personale ───────────────────────────────
        linkedin_url = lead.get("linkedinUrl") or accumulated.get("linkedinUrl")
        if linkedin_url and "linkedin.com/in/" in str(linkedin_url):
            try:
                li_profile = await self._scrape_linkedin_profile(linkedin_url, StealthyFetcher)
                # Non sovrascrivere campi già nel lead originale
                for k, v in li_profile.items():
                    if not lead.get(k) and k not in accumulated:
                        accumulated[k] = v
                logger.info("enrich[%s]: LinkedIn profile → %d campi", lead_id, len(li_profile))
            except Exception as e:
                logger.warning("enrich[%s]: _scrape_linkedin_profile fallito: %s", lead_id, e)

        # ── Passo 3: pagina LinkedIn aziendale ───────────────────────────────
        company_li = (
            accumulated.get("customFields.companyLinkedinUrl")
            or (lead.get("customFields") or {}).get("companyLinkedinUrl")
        )
        if company_li and "linkedin.com/company/" in str(company_li):
            try:
                li_company = await self._scrape_linkedin_company(company_li, StealthyFetcher)
                for k, v in li_company.items():
                    if not lead.get(k) and k not in accumulated:
                        accumulated[k] = v
                logger.info("enrich[%s]: LinkedIn company → %d campi", lead_id, len(li_company))
            except Exception as e:
                logger.warning("enrich[%s]: _scrape_linkedin_company fallito: %s", lead_id, e)

        if not accumulated:
            logger.info("enrich[%s]: nessun dato estratto", lead_id)
            return {}

        # ── Salva in MongoDB ──────────────────────────────────────────────────
        # Separa campi normali da customFields annidati
        top_level = {}
        custom_fields_delta = {}
        for k, v in accumulated.items():
            if k.startswith("customFields."):
                custom_fields_delta[k.split(".", 1)[1]] = v
            else:
                top_level[k] = v

        set_payload: dict = {**top_level}
        for cf_key, cf_val in custom_fields_delta.items():
            set_payload[f"customFields.{cf_key}"] = cf_val

        set_payload["enrichedAt"] = utcnow()
        set_payload["enrichmentSource"] = "scrapling"
        set_payload["updatedAt"] = utcnow()

        await db["leads"].update_one(
            {"_id": lead_id},
            {"$set": set_payload}
        )

        result_keys = [k for k in accumulated if k not in ("updatedAt", "enrichedAt")]
        logger.info(
            "enrich[%s]: completato — %d campi aggiornati: %s",
            lead_id, len(result_keys), result_keys
        )
        return set_payload

    # ── Sito aziendale ────────────────────────────────────────────────────────

    async def _scrape_website(self, domain: str, Fetcher) -> dict:
        await _rate_limit(domain)

        url_https = f"https://{domain}"
        if not _is_robots_allowed(url_https):
            logger.info("_scrape_website: robots.txt disallow per %s", domain)
            return {}

        page = None
        for url in [url_https, f"http://{domain}"]:
            try:
                page = Fetcher(auto_match=True).get(
                    url,
                    timeout=15,
                    stealthy_headers=True,
                    follow_redirects=True,
                )
                break
            except Exception:
                continue

        if page is None:
            return {}

        data: dict = {"website": url_https}
        html_str = page.content if hasattr(page, "content") else str(page)

        # LinkedIn company link nel footer/header
        li_url = _extract_linkedin_company_url(html_str)
        if li_url:
            data["customFields.companyLinkedinUrl"] = li_url

        # Numero dipendenti dal testo della pagina
        body_el = page.find("body")
        body_text = body_el.text if body_el else ""
        size = _parse_employee_count(body_text)
        if size:
            data["companySize"] = size

        # Tech stack
        tech = _detect_tech_stack(html_str)
        if tech:
            data["customFields.techStack"] = tech

        # Privacy policy → segnale GDPR
        privacy_links = page.find_all("a") or []
        has_privacy = any(
            "privacy" in (a.attrib.get("href", "") + a.text).lower()
            for a in privacy_links
        )
        data["customFields.hasPrivacyPolicy"] = has_privacy

        # Lingua del sito
        html_el = page.find("html")
        if html_el:
            lang = html_el.attrib.get("lang", "")
            if lang:
                data["customFields.siteLanguage"] = lang[:2].lower()

        # og:description come note aggiuntiva (solo se notes non c'è già)
        og = page.find('meta[property="og:description"]') or page.find('meta[name="description"]')
        if og:
            desc = og.attrib.get("content", "").strip()
            if desc and len(desc) > 10:
                data["customFields.companyDescription"] = desc[:400]

        return {k: v for k, v in data.items() if v is not None and v != "" and v != []}

    # ── LinkedIn profilo personale ─────────────────────────────────────────────

    async def _scrape_linkedin_profile(self, url: str, StealthyFetcher) -> dict:
        await _rate_limit("linkedin.com")

        try:
            page = StealthyFetcher(auto_match=True).get(
                url,
                timeout=20,
                block_resources=True,  # blocca immagini/font per velocità
            )
        except Exception as e:
            logger.warning("linkedin profile fetch error: %s", e)
            return {}

        data: dict = {}

        # Nome — h1 principale
        h1 = page.find("h1")
        if h1:
            parts = h1.text.strip().split(" ", 1)
            if parts[0]:
                data["firstName"] = parts[0].strip()
            if len(parts) > 1 and parts[1]:
                data["lastName"] = parts[1].strip()

        # Headline / titolo
        for selector in [".text-body-medium", "h2", '[class*="headline"]']:
            el = page.find(selector)
            if el and el.text.strip():
                data["roleTitle"] = el.text.strip()
                break

        # Location
        for selector in [".text-body-small.inline", '[class*="location"]']:
            el = page.find(selector)
            if el and el.text.strip():
                data["customFields.location"] = el.text.strip()
                break

        # Seniority inferita
        if data.get("roleTitle"):
            data["roleSeniority"] = _infer_seniority(data["roleTitle"])

        return {k: v for k, v in data.items() if v}

    # ── LinkedIn pagina aziendale ──────────────────────────────────────────────

    async def _scrape_linkedin_company(self, url: str, StealthyFetcher) -> dict:
        await _rate_limit("linkedin.com")

        try:
            page = StealthyFetcher(auto_match=True).get(
                url,
                timeout=20,
                block_resources=True,
            )
        except Exception as e:
            logger.warning("linkedin company fetch error: %s", e)
            return {}

        data: dict = {}
        html_str = page.content if hasattr(page, "content") else str(page)

        # Numero dipendenti
        for el in (page.find_all("dd") or []):
            size = _parse_employee_count(el.text)
            if size:
                data["numEmployeesRange"] = size
                break

        # Industry
        for selector in ['[data-test-id="about-us__industry"]', '.industry', '[class*="industry"]']:
            el = page.find(selector)
            if el and el.text.strip():
                data["industry"] = el.text.strip()
                break

        # Followers
        for el in (page.find_all("span") or []):
            if "follower" in el.text.lower() and any(c.isdigit() for c in el.text):
                data["customFields.linkedinFollowers"] = el.text.strip()
                break

        # Specialties → tags CRM
        for selector in ['[data-test-id="about-us__specialties"]', '[class*="specialties"]']:
            el = page.find(selector)
            if el and el.text.strip():
                specs = [s.strip() for s in el.text.split(",") if s.strip()][:8]
                if specs:
                    data["tags"] = specs
                break

        # Descrizione aziendale
        for selector in ['[data-test-id="about-us__description"]', '[class*="about-us"]']:
            el = page.find(selector)
            if el and el.text.strip():
                data["customFields.companyDescription"] = el.text.strip()[:400]
                break

        # Founded year
        m = re.search(r'\b(19|20)\d{2}\b', html_str)
        if m:
            year = int(m.group(0))
            if 1900 < year <= 2024:
                data["customFields.foundedYear"] = year

        return {k: v for k, v in data.items() if v}
