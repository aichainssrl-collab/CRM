"""
Audit log service — track all CRUD operations across entities.
"""
from datetime import datetime, timezone
from typing import Optional
from app.services.db_service import db, new_id, utcnow, _to_dict
import logging

logger = logging.getLogger(__name__)


async def log_action(
    user_id: str,
    action: str,  # create | update | delete | soft_delete | login | export | enroll
    entity_type: str,  # lead | deal | task | user | sequence | report | booking
    entity_id: str,
    description: str = "",
    changes: dict = None,
) -> dict:
    """Log an audit trail entry."""
    now = utcnow()
    doc = {
        "_id": new_id(),
        "userId": user_id,
        "action": action,
        "entityType": entity_type,
        "entityId": entity_id,
        "description": description,
        "changes": changes or {},
        "ipAddress": None,
        "createdAt": now,
    }
    await db["audit_log"].insert_one(doc)
    return _to_dict(doc)


async def list_audit_log(
    user_id: str = None,
    entity_type: str = None,
    action: str = None,
    limit: int = 100,
) -> list[dict]:
    """List audit log entries with optional filters."""
    query = {}
    if user_id:
        query["userId"] = user_id
    if entity_type:
        query["entityType"] = entity_type
    if action:
        query["action"] = action

    cursor = db["audit_log"].find(query).sort("createdAt", -1).limit(limit)
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


async def get_audit_stats(days: int = 30) -> dict:
    """Get audit statistics for the last N days."""
    since = datetime.now(timezone.utc) - __import__("datetime").timedelta(days=days)

    # Actions by type
    action_pipeline = [
        {"$match": {"createdAt": {"$gte": since}}},
        {"$group": {"_id": "$action", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
    ]
    by_action = {}
    async for row in db["audit_log"].aggregate(action_pipeline):
        by_action[row["_id"]] = row["count"]

    # Actions by entity
    entity_pipeline = [
        {"$match": {"createdAt": {"$gte": since}}},
        {"$group": {"_id": "$entityType", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
    ]
    by_entity = {}
    async for row in db["audit_log"].aggregate(entity_pipeline):
        by_entity[row["_id"]] = row["count"]

    # Top users
    user_pipeline = [
        {"$match": {"createdAt": {"$gte": since}, "userId": {"$ne": None}}},
        {"$group": {"_id": "$userId", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10},
    ]
    top_users = []
    async for row in db["audit_log"].aggregate(user_pipeline):
        top_users.append({"userId": row["_id"], "count": row["count"]})

    total = await db["audit_log"].count_documents({"createdAt": {"$gte": since}})

    return {
        "total": total,
        "byAction": by_action,
        "byEntity": by_entity,
        "topUsers": top_users,
    }