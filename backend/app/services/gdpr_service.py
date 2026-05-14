import hashlib
import json
from app.firebase_admin import db
from app.services.db_service import utcnow, new_id


async def log_consent(
    lead_id: str,
    action: str,
    purpose: str,
    consent_text: str,
    ip: str,
    policy_version: str = "2.1",
    db_client=None,
) -> str:
    """
    Registra consenso in gdpr_consents — APPEND-ONLY.
    In Fase 3: il dataHash verrà ancorato su blockchain via SignSisure.
    """
    client = db_client or db
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
    await client.collection("gdpr_consents").document(consent_id).set(payload)
    return consent_id


async def gdpr_export(lead_id: str) -> dict:
    """Art. 20 GDPR — Portabilità dei dati."""
    snap = await db.collection("leads").document(lead_id).get()
    lead = ({"id": snap.id, **snap.to_dict()} if snap.exists else None)

    activities = []
    async for s in (
        db.collection("leads").document(lead_id).collection("activities").stream()
    ):
        activities.append({"id": s.id, **s.to_dict()})

    tasks = []
    async for s in (
        db.collection("leads").document(lead_id).collection("tasks").stream()
    ):
        tasks.append({"id": s.id, **s.to_dict()})

    consents = []
    from google.cloud.firestore_v1 import FieldFilter
    async for s in (
        db.collection("gdpr_consents")
        .where(filter=FieldFilter("leadId", "==", lead_id))
        .stream()
    ):
        consents.append({"id": s.id, **s.to_dict()})

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
    anonymized = {
        "firstName": "CANCELLATO",
        "lastName": "GDPR",
        "email": f"gdpr-erased-{lead_id}@deleted.invalid",
        "phone": None,
        "linkedinUrl": None,
        "notes": None,
        "customFields": {},
        "deletedAt": now,
        "updatedAt": now,
    }
    await db.collection("leads").document(lead_id).update(anonymized)
    await log_consent(
        lead_id=lead_id,
        action="deletion_completed",
        purpose="all",
        consent_text="GDPR Art.17 — Diritto all'oblio",
        ip="system",
        policy_version="GDPR Art.17",
    )
