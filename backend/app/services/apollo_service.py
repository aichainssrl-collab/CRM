"""
Apollo.io prospect search & enrichment.

Mock mode when `APOLLO_API_KEY` is empty: returns deterministic demo prospects
so UI/tests work offline. Live mode calls Apollo mixed_people/search + people/match.
"""
from __future__ import annotations

import logging
from typing import Any, Optional

import httpx

from app.config import settings
from app.services.db_service import db, new_id, utcnow, _to_dict

logger = logging.getLogger(__name__)

# Map Apollo email_status → include only safe ones
_OK_EMAIL_STATUS = {"verified", "likely_to_engage"}


def is_mock() -> bool:
    return not settings.APOLLO_API_KEY


# ── Mapping ──────────────────────────────────────────────────────────────────

def map_person(raw: dict) -> dict:
    """Apollo person → internal prospect shape."""
    org = raw.get("organization") or {}
    emails = raw.get("emails") or []
    email_status = raw.get("email_status") or (emails[0].get("status") if emails else None)
    email = raw.get("email") or (emails[0].get("email") if emails else None)
    phones = raw.get("phone_numbers") or []
    phone = phones[0].get("sanitized_number") if phones else raw.get("phone")
    return {
        "apolloId": raw.get("id") or raw.get("apollo_id") or "",
        "firstName": raw.get("first_name") or raw.get("firstName") or "",
        "lastName": raw.get("last_name") or raw.get("lastName") or "",
        "email": email or "",
        "emailStatus": email_status,
        "title": raw.get("title") or "",
        "linkedinUrl": raw.get("linkedin_url") or "",
        "phone": phone or "",
        "city": raw.get("city") or "",
        "country": raw.get("country") or "",
        "companyName": org.get("name") or raw.get("companyName") or "",
        "companyDomain": (org.get("primary_domain") or raw.get("companyDomain") or ""),
        "industry": org.get("industry") or raw.get("industry") or "",
        "numEmployeesRange": str(org.get("estimated_num_employees") or raw.get("numEmployeesRange") or ""),
        "seniority": raw.get("seniority") or "",
        "apolloScore": raw.get("score") or raw.get("apolloScore"),
    }


# ── Mock data ────────────────────────────────────────────────────────────────

_MOCK_PEOPLE = [
    {
        "id": "apollo-mock-1",
        "first_name": "Marco",
        "last_name": "Bianchi",
        "email": "marco.bianchi@lexfirm.it",
        "email_status": "verified",
        "title": "Managing Partner",
        "linkedin_url": "https://linkedin.com/in/marcobianchi",
        "phone_numbers": [{"sanitized_number": "+390212345678"}],
        "city": "Milano",
        "country": "Italy",
        "seniority": "c_suite",
        "score": 92,
        "organization": {
            "name": "LexFirm Studio Legale",
            "primary_domain": "lexfirm.it",
            "industry": "Legal Services",
            "estimated_num_employees": 45,
        },
    },
    {
        "id": "apollo-mock-2",
        "first_name": "Giulia",
        "last_name": "Rossi",
        "email": "giulia.rossi@finnovaspa.it",
        "email_status": "likely_to_engage",
        "title": "Head of Digital Transformation",
        "linkedin_url": "https://linkedin.com/in/giuliarossi",
        "phone_numbers": [{"sanitized_number": "+390698765432"}],
        "city": "Roma",
        "country": "Italy",
        "seniority": "vp",
        "score": 81,
        "organization": {
            "name": "Finnova SpA",
            "primary_domain": "finnovaspa.it",
            "industry": "Financial Services",
            "estimated_num_employees": 220,
        },
    },
    {
        "id": "apollo-mock-3",
        "first_name": "Luca",
        "last_name": "Ferrari",
        "email": "l.ferrari@pa-digitale.gov.it",
        "email_status": "verified",
        "title": "Direttore Sistemi Informativi",
        "linkedin_url": "https://linkedin.com/in/lcaferrari",
        "phone_numbers": [],
        "city": "Bologna",
        "country": "Italy",
        "seniority": "director",
        "score": 74,
        "organization": {
            "name": "PA Digitale",
            "primary_domain": "pa-digitale.gov.it",
            "industry": "Government",
            "estimated_num_employees": 1200,
        },
    },
    {
        "id": "apollo-mock-4",
        "first_name": "Anna",
        "last_name": "Conti",
        "email": "anna.conti@manutech.eu",
        "email_status": "invalid",
        "title": "Operations Manager",
        "linkedin_url": "",
        "phone_numbers": [{"sanitized_number": "+390111222333"}],
        "city": "Torino",
        "country": "Italy",
        "seniority": "manager",
        "score": 40,
        "organization": {
            "name": "ManuTech",
            "primary_domain": "manutech.eu",
            "industry": "Manufacturing",
            "estimated_num_employees": 80,
        },
    },
]


def _filter_mock(filters: dict) -> list[dict]:
    q = (filters.get("q") or filters.get("title") or "").lower()
    industry = (filters.get("industry") or "").lower()
    location = (filters.get("location") or "").lower()
    out = []
    for p in _MOCK_PEOPLE:
        blob = " ".join(
            [
                p.get("title", ""),
                p.get("first_name", ""),
                p.get("last_name", ""),
                p.get("organization", {}).get("name", ""),
            ]
        ).lower()
        if q and q not in blob:
            continue
        if industry and industry not in (p.get("organization", {}).get("industry") or "").lower():
            continue
        if location and location not in (p.get("city", "") + " " + p.get("country", "")).lower():
            continue
        out.append(p)
    return out


# ── Public API ───────────────────────────────────────────────────────────────

async def people_search(
    filters: Optional[dict] = None,
    page: int = 1,
    per_page: int = 25,
) -> dict:
    """Search prospects. Returns {people, total, page, perPage, mode}."""
    filters = filters or {}
    page = max(1, page)
    per_page = max(1, min(per_page, 100))

    if is_mock():
        matched = _filter_mock(filters)
        start = (page - 1) * per_page
        page_items = matched[start : start + per_page]
        return {
            "people": [map_person(p) for p in page_items],
            "total": len(matched),
            "page": page,
            "perPage": per_page,
            "mode": "mock",
        }

    payload = {
        "person_titles": [filters["title"]] if filters.get("title") else [],
        "person_locations": [filters["location"]] if filters.get("location") else [],
        "organization_industry_tag_ids": [],
        "q_keywords": filters.get("q") or "",
        "page": page,
        "per_page": per_page,
    }
    if filters.get("industry"):
        payload["organization_industry_tag_ids"] = [filters["industry"]]
    if filters.get("seniority"):
        payload["person_seniorities"] = [filters["seniority"]]

    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.post(
            f"{settings.APOLLO_API_BASE}/mixed_people/search",
            headers={"X-Api-Key": settings.APOLLO_API_KEY},
            json=payload,
        )
        resp.raise_for_status()
        data = resp.json()

    people = [map_person(p) for p in data.get("people", [])]
    # Drop invalid emails (do not spend reveal credits)
    people = [p for p in people if p.get("emailStatus") in _OK_EMAIL_STATUS or not p.get("emailStatus")]
    return {
        "people": people,
        "total": data.get("pagination", {}).get("total_entries", len(people)),
        "page": page,
        "perPage": per_page,
        "mode": "live",
    }


async def people_match(email: str) -> Optional[dict]:
    if not email:
        return None
    if is_mock():
        for p in _MOCK_PEOPLE:
            if p.get("email", "").lower() == email.lower():
                return map_person(p)
        return None

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            f"{settings.APOLLO_API_BASE}/people/match",
            headers={"X-Api-Key": settings.APOLLO_API_KEY},
            json={"email": email, "reveal_personal_emails": False},
        )
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        person = resp.json().get("person")
        return map_person(person) if person else None


async def enrich_lead(lead_id: str) -> Optional[dict]:
    """
    Enrich an existing lead via Apollo people/match on its email.
    Merges fields without overwriting non-empty manual values.
    """
    lead = await db["leads"].find_one({"_id": lead_id, "deletedAt": None})
    if not lead:
        return None

    email = lead.get("email") or ""
    person = await people_match(email)

    if person:
        now = utcnow()
        updates: dict[str, Any] = {
            "enrichedAt": now,
            "enrichmentSource": "apollo",
            "updatedAt": now,
        }
        field_map = {
            "apolloId": "apolloId",
            "apolloScore": "apolloScore",
            "linkedinUrl": "linkedinUrl",
            "roleTitle": "title",
            "roleSeniority": "seniority",
            "industry": "industry",
            "numEmployeesRange": "numEmployeesRange",
            "companyName": "companyName",
            "phone": "phone",
        }
        for target, source in field_map.items():
            val = person.get(source)
            if val in (None, "", 0):
                continue
            if lead.get(target) in (None, "", 0):
                updates[target] = val
        await db["leads"].update_one({"_id": lead_id}, {"$set": updates})
        updated = await db["leads"].find_one({"_id": lead_id})
        return _to_dict(updated)

    # No match: still stamp enrichment attempt
    now = utcnow()
    await db["leads"].update_one(
        {"_id": lead_id},
        {"$set": {"enrichedAt": now, "enrichmentSource": "apollo_miss", "updatedAt": now}},
    )
    updated = await db["leads"].find_one({"_id": lead_id})
    return _to_dict(updated)


async def import_prospects(prospects: list[dict], created_by: str) -> dict:
    """
    Import selected prospects as leads.
    Deduplicates by email (app-level unique check). Logs GDPR legitimate_interest.
    """
    from app.services.activity_service import append_activity

    imported: list[dict] = []
    skipped: list[dict] = []
    errors: list[str] = []

    for p in prospects:
        email = (p.get("email") or "").strip().lower()
        if not email:
            errors.append(f"{p.get('firstName', '')} {p.get('lastName', '')}: email mancante")
            continue
        if p.get("emailStatus") == "invalid":
            errors.append(f"{email}: email non valida (Apollo invalid)")
            continue

        existing = await db["leads"].find_one({"email": email, "deletedAt": None})
        if existing:
            skipped.append({"email": email, "reason": "duplicate", "leadId": existing["_id"]})
            continue

        now = utcnow()
        doc = {
            "_id": new_id(),
            "firstName": p.get("firstName") or "",
            "lastName": p.get("lastName") or "",
            "email": email,
            "phone": p.get("phone") or None,
            "linkedinUrl": p.get("linkedinUrl") or None,
            "companyName": p.get("companyName") or None,
            "companySize": p.get("numEmployeesRange") or None,
            "industry": p.get("industry") or None,
            "roleTitle": p.get("title") or None,
            "roleSeniority": p.get("seniority") or None,
            "numEmployeesRange": p.get("numEmployeesRange") or None,
            "source": "apollo_import",
            "status": "new",
            "pipelineStage": "new",
            "leadScore": int(p.get("apolloScore") or 0),
            "apolloId": p.get("apolloId") or None,
            "apolloScore": p.get("apolloScore") or None,
            "enrichedAt": now,
            "enrichmentSource": "apollo",
            "tags": ["apollo"],
            "notes": None,
            "assignedTo": created_by,
            "activityCount": 0,
            "taskCount": 0,
            "customFields": {},
            "painPoints": [],
            "createdAt": now,
            "updatedAt": now,
            "deletedAt": None,
        }
        await db["leads"].insert_one(doc)
        lead_id = doc["_id"]
        await append_activity(lead_id, {
            "type": "note",
            "title": "Lead importato da Apollo",
            "userId": created_by,
            "metadata": {"apolloId": p.get("apolloId")},
        })
        # GDPR: legitimate interest (public-source B2B data)
        await db["gdpr_consents"].insert_one({
            "_id": new_id(),
            "leadId": lead_id,
            "type": "legitimate_interest",
            "source": "apollo_import",
            "legalBasis": "legitimate_interest",
            "text": "Import prospect Apollo.io — dati B2B da fonti pubbliche",
            "grantedBy": created_by,
            "timestamp": now,
            "createdAt": now,
        })
        imported.append(_to_dict(doc))

    return {
        "imported": imported,
        "importedCount": len(imported),
        "skipped": skipped,
        "skippedCount": len(skipped),
        "errors": errors,
    }


async def usage() -> dict:
    """API usage / mode indicator (no live credits endpoint required)."""
    return {
        "mode": "mock" if is_mock() else "live",
        "provider": "apollo",
        "hasApiKey": not is_mock(),
    }
