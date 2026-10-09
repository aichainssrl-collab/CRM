"""
Saved filters service — save and reuse filter combinations.
"""
from typing import Optional
from app.services.db_service import db, new_id, utcnow, _to_dict
import logging

logger = logging.getLogger(__name__)


async def create_saved_filter(user_id: str, data: dict) -> dict:
    now = utcnow()
    doc = {
        "_id": new_id(),
        "userId": user_id,
        "name": data["name"],
        "entityType": data["entityType"],  # leads | deals | tasks
        "filters": data.get("filters", {}),
        "isGlobal": data.get("isGlobal", False),
        "createdAt": now,
        "updatedAt": now,
        "deletedAt": None,
    }
    await db["saved_filters"].insert_one(doc)
    return _to_dict(doc)


async def list_saved_filters(user_id: str, entity_type: str = None) -> list[dict]:
    query = {
        "deletedAt": None,
        "$or": [{"userId": user_id}, {"isGlobal": True}],
    }
    if entity_type:
        query["entityType"] = entity_type

    cursor = db["saved_filters"].find(query).sort("createdAt", -1)
    docs = await cursor.to_list(length=50)
    return [_to_dict(d) for d in docs]


async def update_saved_filter(filter_id: str, data: dict) -> Optional[dict]:
    data["updatedAt"] = utcnow()
    doc = await db["saved_filters"].find_one_and_update(
        {"_id": filter_id, "deletedAt": None},
        {"$set": data},
        return_document=True,
    )
    return _to_dict(doc) if doc else None


async def delete_saved_filter(filter_id: str) -> bool:
    now = utcnow()
    result = await db["saved_filters"].update_one(
        {"_id": filter_id, "deletedAt": None},
        {"$set": {"deletedAt": now, "updatedAt": now}},
    )
    return result.modified_count > 0