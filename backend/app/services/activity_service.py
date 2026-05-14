from typing import Optional
from app.services.db_service import utcnow, new_id, increment_field
from app.firebase_admin import db


async def append_activity(lead_id: str, data: dict) -> dict:
    """
    Aggiunge un'activity alla subcollection leads/{id}/activities.
    Append-only: mai modificare o cancellare.
    """
    activity_id = new_id()
    now = utcnow()
    payload = {
        "leadId": lead_id,
        **data,
        "createdAt": now,
    }
    ref = (
        db.collection("leads")
        .document(lead_id)
        .collection("activities")
        .document(activity_id)
    )
    await ref.set(payload)

    # Aggiorna contatori sul lead padre
    await db.collection("leads").document(lead_id).update({
        "activityCount": _increment(1),
        "lastActivityAt": now,
    })

    return {"id": activity_id, **payload}


async def list_activities(lead_id: str, limit: int = 50) -> list[dict]:
    query = (
        db.collection("leads")
        .document(lead_id)
        .collection("activities")
        .order_by("createdAt", direction="DESCENDING")
        .limit(limit)
    )
    results = []
    async for snap in query.stream():
        results.append({"id": snap.id, **snap.to_dict()})
    return results


def _increment(amount: int):
    from google.cloud.firestore_v1 import Increment
    return Increment(amount)
