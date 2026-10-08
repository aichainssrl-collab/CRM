import hashlib
import json
from app.services.db_service import db, utcnow, new_id
from app.services.activity_service import list_activities
from app.services.task_service import list_tasks


async def log_consent(
    lead_id: str,
    action: str,
    purpose: str,
    consent_text: str,
    ip: str,
    policy_version: str = "2.1",
) -> str:
    """Registra consenso in gdpr_consents — APPEND-ONLY."""
    now = utcnow()
    payload = {
        "leadId": lead_id,
        "action": action,
        "purpose": purpose,
        "consentText": consent_text,
        "policyVersion": policy_version,
        "ipAddress": ip,
        "createdAt": now,
    }
    payload["dataHash"] = hashlib.sha256(
        json.dumps(payload, default=str, sort_keys=True).encode()
    ).hexdigest()

    consent_id = new_id()
    await db["gdpr_consents"].insert_one({"_id": consent_id, **payload})
    return consent_id


async def gdpr_export(lead_id: str) -> dict:
    """Art. 20 GDPR — Portabilità dei dati."""
    doc = await db["leads"].find_one({"_id": lead_id})
    lead = None
    if doc:
        doc = dict(doc)
        doc["id"] = doc.pop("_id")
        lead = doc

    activities = await list_activities(lead_id, limit=1000)

    tasks_cursor = db["tasks"].find({"leadId": lead_id})
    tasks = []
    async for d in tasks_cursor:
        d = dict(d)
        d["id"] = d.pop("_id")
        tasks.append(d)

    consents = []
    async for d in db["gdpr_consents"].find({"leadId": lead_id}):
        d = dict(d)
        d["id"] = d.pop("_id")
        consents.append(d)

    return {
        "exported_at": utcnow().isoformat(),
        "lead": lead,
        "activities": activities,
        "tasks": tasks,
        "gdpr_consents": consents,
    }


async def gdpr_erase(lead_id: str, erased_by_uid: str) -> None:
    """Art. 17 GDPR — Diritto all'oblio. Anonimizza, non cancella."""
    now = utcnow()
    await db["leads"].update_one(
        {"_id": lead_id},
        {"$set": {
            "firstName": "CANCELLATO",
            "lastName": "GDPR",
            "email": f"gdpr-erased-{lead_id}@deleted.invalid",
            "phone": None,
            "linkedinUrl": None,
            "notes": None,
            "customFields": {},
            "deletedAt": now,
            "updatedAt": now,
        }},
    )
    await log_consent(
        lead_id=lead_id,
        action="deletion_completed",
        purpose="all",
        consent_text="GDPR Art.17 — Diritto all'oblio",
        ip="system",
        policy_version="GDPR Art.17",
    )
