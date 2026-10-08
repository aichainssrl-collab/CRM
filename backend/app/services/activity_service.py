from app.services.db_service import db, utcnow, new_id, increment_field
from pymongo import DESCENDING


async def append_activity(lead_id: str, data: dict) -> dict:
    """Aggiunge un'activity — append-only, mai modificare o cancellare."""
    activity_id = new_id()
    now = utcnow()
    payload = {
        "_id": activity_id,
        "leadId": lead_id,
        **data,
        "createdAt": now,
    }
    await db["activities"].insert_one(payload)
    await db["leads"].update_one(
        {"_id": lead_id},
        {"$inc": {"activityCount": 1}, "$set": {"lastActivityAt": now, "updatedAt": now}},
    )
    doc = dict(payload)
    doc["id"] = doc.pop("_id")
    return doc


async def list_activities(lead_id: str, limit: int = 50) -> list[dict]:
    cursor = (
        db["activities"]
        .find({"leadId": lead_id})
        .sort("createdAt", DESCENDING)
        .limit(limit)
    )
    docs = await cursor.to_list(length=limit)
    return [{**{k: v for k, v in d.items() if k != "_id"}, "id": d["_id"]} for d in docs]
