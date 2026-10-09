"""
Content Library — reusable marketing content (email, ads, social, landing).
"""
from typing import Optional
from app.services.db_service import db, new_id, utcnow, _to_dict
import logging

logger = logging.getLogger(__name__)

TYPES = ("email", "ad_copy", "social", "landing", "blog", "other")


async def create_content(data: dict, created_by: str) -> dict:
    now = utcnow()
    doc = {
        "_id": new_id(),
        "title": data["title"],
        "type": data.get("type", "other"),
        "body": data.get("body", ""),
        "description": data.get("description", ""),
        "tags": data.get("tags") or [],
        "language": data.get("language", "it"),
        "source": data.get("source", "manual"),  # manual | marketing_agent
        "createdBy": created_by,
        "createdAt": now,
        "updatedAt": now,
        "deletedAt": None,
    }
    await db["content_library"].insert_one(doc)
    return _to_dict(doc)


async def list_content(
    content_type: Optional[str] = None,
    tag: Optional[str] = None,
    search: Optional[str] = None,
) -> list[dict]:
    query: dict = {"deletedAt": None}
    if content_type:
        query["type"] = content_type
    if tag:
        query["tags"] = tag
    if search:
        query["$or"] = [
            {"title": {"$regex": search, "$options": "i"}},
            {"body": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}},
        ]
    cursor = db["content_library"].find(query).sort("updatedAt", -1)
    docs = await cursor.to_list(length=200)
    return [_to_dict(d) for d in docs]


async def get_content(content_id: str) -> Optional[dict]:
    doc = await db["content_library"].find_one({"_id": content_id, "deletedAt": None})
    return _to_dict(doc) if doc else None


async def update_content(content_id: str, data: dict) -> Optional[dict]:
    data["updatedAt"] = utcnow()
    doc = await db["content_library"].find_one_and_update(
        {"_id": content_id, "deletedAt": None},
        {"$set": data},
        return_document=True,
    )
    return _to_dict(doc) if doc else None


async def delete_content(content_id: str) -> bool:
    now = utcnow()
    result = await db["content_library"].update_one(
        {"_id": content_id, "deletedAt": None},
        {"$set": {"deletedAt": now, "updatedAt": now}},
    )
    return result.modified_count > 0


async def content_stats() -> dict:
    pipeline = [
        {"$match": {"deletedAt": None}},
        {"$group": {"_id": "$type", "count": {"$sum": 1}}},
    ]
    rows = await db["content_library"].aggregate(pipeline).to_list(length=20)
    by_type = {r["_id"]: r["count"] for r in rows}
    return {
        "totalCount": sum(by_type.values()),
        "byType": by_type,
    }


async def list_tags() -> list[str]:
    rows = await db["content_library"].aggregate(
        [
            {"$match": {"deletedAt": None}},
            {"$unwind": "$tags"},
            {"$group": {"_id": "$tags", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 30},
        ]
    ).to_list(length=30)
    return [r["_id"] for r in rows if r.get("_id")]
