"""
Notification service — in-app notifications + activity feed.
"""
from datetime import datetime, timezone
from typing import Optional
from app.services.db_service import db, new_id, utcnow, _to_dict
import logging

logger = logging.getLogger(__name__)


# ── Notifications ──────────────────────────────────────────────
async def create_notification(
    user_id: str,
    title: str,
    body: str,
    kind: str = "info",  # info | warning | success | error
    link: str = None,
) -> dict:
    """Create an in-app notification for a user."""
    now = utcnow()
    doc = {
        "_id": new_id(),
        "userId": user_id,
        "title": title,
        "body": body,
        "kind": kind,
        "link": link,
        "readAt": None,
        "createdAt": now,
    }
    await db["notifications"].insert_one(doc)
    return _to_dict(doc)


async def list_notifications(
    user_id: str,
    unread_only: bool = False,
    limit: int = 50,
) -> list[dict]:
    query = {"userId": user_id}
    if unread_only:
        query["readAt"] = None
    cursor = db["notifications"].find(query).sort("createdAt", -1).limit(limit)
    docs = await cursor.to_list(length=limit)
    return [_to_dict(d) for d in docs]


async def mark_read(notification_id: str, user_id: str) -> Optional[dict]:
    now = utcnow()
    doc = await db["notifications"].find_one_and_update(
        {"_id": notification_id, "userId": user_id},
        {"$set": {"readAt": now}},
        return_document=True,
    )
    return _to_dict(doc) if doc else None


async def mark_all_read(user_id: str) -> int:
    now = utcnow()
    result = await db["notifications"].update_many(
        {"userId": user_id, "readAt": None},
        {"$set": {"readAt": now}},
    )
    return result.modified_count


async def get_unread_count(user_id: str) -> int:
    return await db["notifications"].count_documents({"userId": user_id, "readAt": None})


# ── Activity Feed ─────────────────────────────────────────────
async def log_activity(
    user_id: str,
    action: str,  # lead.created, deal.won, task.completed, etc.
    entity_type: str,  # lead | deal | task | booking | sequence
    entity_id: str,
    description: str = "",
    metadata: dict = None,
) -> dict:
    """Log an activity for the feed."""
    now = utcnow()
    doc = {
        "_id": new_id(),
        "userId": user_id,
        "action": action,
        "entityType": entity_type,
        "entityId": entity_id,
        "description": description,
        "metadata": metadata or {},
        "createdAt": now,
    }
    await db["activity_feed"].insert_one(doc)
    return _to_dict(doc)


async def get_activity_feed(
    user_id: str = None,
    limit: int = 50,
) -> list[dict]:
    """Get activity feed. If user_id is None, returns all (for admins)."""
    query = {}
    if user_id:
        query["userId"] = user_id
    cursor = db["activity_feed"].find(query).sort("createdAt", -1).limit(limit)
    docs = await cursor.to_list(length=limit)

    # Enrich with user names
    user_ids = list({d.get("userId") for d in docs if d.get("userId")})
    users_map = {}
    if user_ids:
        async for u in db["users"].find({"_id": {"$in": user_ids}}):
            users_map[u["_id"]] = u.get("displayName") or u.get("email", u["_id"])

    results = []
    for d in docs:
        d = _to_dict(d)
        d["userName"] = users_map.get(d.get("userId"), "Sistema")
        results.append(d)
    return results


# ── Global Search ──────────────────────────────────────────────
async def global_search(query: str, user_id: str, limit: int = 10) -> dict:
    """Search across leads, deals, tasks."""
    regex = {"$regex": query, "$options": "i"}
    results = {"leads": [], "deals": [], "tasks": []}

    # Leads
    lead_cursor = db["leads"].find({
        "deletedAt": None,
        "$or": [
            {"firstName": regex},
            {"lastName": regex},
            {"email": regex},
            {"companyName": regex},
        ],
    }).limit(limit)
    async for d in lead_cursor:
        results["leads"].append({
            "id": d["_id"],
            "title": f"{d.get('firstName', '')} {d.get('lastName', '')}".strip() or d.get("email"),
            "subtitle": d.get("companyName") or d.get("email"),
            "status": d.get("status", "new"),
        })

    # Deals
    deal_cursor = db["deals"].find({
        "deletedAt": None,
        "$or": [
            {"title": regex},
            {"notes": regex},
            {"product": regex},
        ],
    }).limit(limit)
    async for d in deal_cursor:
        results["deals"].append({
            "id": d["_id"],
            "title": d.get("title", ""),
            "subtitle": f"€{d.get('value', 0):,.0f}" if d.get("value") else "",
            "status": d.get("stage", "new"),
        })

    # Tasks
    task_cursor = db["tasks"].find({
        "deletedAt": None,
        "$or": [
            {"title": regex},
            {"description": regex},
        ],
    }).limit(limit)
    async for d in task_cursor:
        results["tasks"].append({
            "id": d["_id"],
            "title": d.get("title", ""),
            "subtitle": d.get("description", "")[:50] if d.get("description") else "",
            "status": d.get("status", "open"),
        })

    return results