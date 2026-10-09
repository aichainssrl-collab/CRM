"""
Segmentation service — dynamic lead segments and smart lists.
"""
from datetime import datetime, timezone, timedelta
from typing import Optional
from app.services.db_service import db, new_id, utcnow, _to_dict
import logging

logger = logging.getLogger(__name__)


# ── Segments (dynamic definitions) ─────────────────────────────
async def create_segment(user_id: str, data: dict) -> dict:
    now = utcnow()
    doc = {
        "_id": new_id(),
        "userId": user_id,
        "name": data["name"],
        "description": data.get("description", ""),
        "rules": data.get("rules", {}),  # filter rules
        "entityType": data.get("entityType", "leads"),
        "isGlobal": data.get("isGlobal", False),
        "createdAt": now,
        "updatedAt": now,
        "deletedAt": None,
    }
    await db["segments"].insert_one(doc)
    return _to_dict(doc)


async def list_segments(user_id: str) -> list[dict]:
    query = {
        "deletedAt": None,
        "$or": [{"userId": user_id}, {"isGlobal": True}],
    }
    cursor = db["segments"].find(query).sort("createdAt", -1)
    docs = await cursor.to_list(length=50)

    # Count matching entities for each segment
    results = []
    for d in docs:
        d = _to_dict(d)
        match_query = {"deletedAt": None}
        rules = d.get("rules", {})
        if rules.get("status"):
            match_query["status"] = rules["status"]
        if rules.get("source"):
            match_query["source"] = rules["source"]
        if rules.get("industry"):
            match_query["industry"] = rules["industry"]
        if rules.get("minScore"):
            match_query["leadScore"] = {"$gte": rules["minScore"]}
        if rules.get("maxScore"):
            match_query.setdefault("leadScore", {})["$lte"] = rules["maxScore"]

        d["matchCount"] = await db["leads"].count_documents(match_query)
        results.append(d)

    return results


async def get_segment_results(segment_id: str, limit: int = 100) -> list[dict]:
    """Get entities matching a segment's rules."""
    seg = await db["segments"].find_one({"_id": segment_id, "deletedAt": None})
    if not seg:
        return []

    rules = seg.get("rules", {})
    query = {"deletedAt": None}
    if rules.get("status"):
        query["status"] = rules["status"]
    if rules.get("source"):
        query["source"] = rules["source"]
    if rules.get("industry"):
        query["industry"] = rules["industry"]
    if rules.get("minScore"):
        query["leadScore"] = {"$gte": rules["minScore"]}
    if rules.get("maxScore"):
        query.setdefault("leadScore", {})["$lte"] = rules["maxScore"]

    cursor = db["leads"].find(query).sort("leadScore", -1).limit(limit)
    docs = await cursor.to_list(length=limit)
    return [_to_dict(d) for d in docs]


async def delete_segment(segment_id: str) -> bool:
    now = utcnow()
    result = await db["segments"].update_one(
        {"_id": segment_id, "deletedAt": None},
        {"$set": {"deletedAt": now, "updatedAt": now}},
    )
    return result.modified_count > 0


# ── Tag Analytics ──────────────────────────────────────────────
async def get_tag_analytics() -> list[dict]:
    """Get tag usage statistics across leads."""
    pipeline = [
        {"$match": {"deletedAt": None}},
        {"$unwind": "$tags"},
        {"$group": {
            "_id": "$tags",
            "count": {"$sum": 1},
            "avgScore": {"$avg": "$leadScore"},
        }},
        {"$sort": {"count": -1}},
        {"$limit": 20},
    ]
    results = []
    async for row in db["leads"].aggregate(pipeline):
        results.append({
            "tag": row["_id"],
            "count": row["count"],
            "avgScore": round(float(row.get("avgScore") or 0), 1),
        })
    return results


# ── Industry Segmentation ─────────────────────────────────────
async def get_industry_segments() -> list[dict]:
    """Get lead counts by industry with status breakdown."""
    pipeline = [
        {"$match": {"deletedAt": None}},
        {"$group": {
            "_id": "$industry",
            "total": {"$sum": 1},
            "avgScore": {"$avg": "$leadScore"},
            "statuses": {"$push": "$status"},
        }},
        {"$sort": {"total": -1}},
    ]
    results = []
    async for row in db["leads"].aggregate(pipeline):
        statuses = row.get("statuses", [])
        status_counts = {}
        for s in statuses:
            status_counts[s] = status_counts.get(s, 0) + 1
        results.append({
            "industry": row["_id"] or "Non specificato",
            "total": row["total"],
            "avgScore": round(float(row.get("avgScore") or 0), 1),
            "statusBreakdown": status_counts,
        })
    return results


# ── Source Performance ─────────────────────────────────────────
async def get_source_performance() -> list[dict]:
    """Get conversion rates by lead source."""
    # Total leads by source
    source_pipeline = [
        {"$match": {"deletedAt": None}},
        {"$group": {"_id": "$source", "count": {"$sum": 1}}},
    ]
    sources = {}
    async for row in db["leads"].aggregate(source_pipeline):
        sources[row["_id"] or "direct"] = row["count"]

    # Converted leads (have won deals) by source
    won_pipeline = [
        {"$match": {"deletedAt": None, "status": {"$in": ["won", "proposal", "negotiation", "qualified"]}}},
        {"$group": {"_id": "$source", "count": {"$sum": 1}}},
    ]
    converted = {}
    async for row in db["leads"].aggregate(won_pipeline):
        converted[row["_id"] or "direct"] = row["count"]

    results = []
    for source, total in sources.items():
        conv = converted.get(source, 0)
        results.append({
            "source": source,
            "total": total,
            "converted": conv,
            "conversionRate": round(conv / total * 100, 1) if total > 0 else 0,
        })

    results.sort(key=lambda x: x["conversionRate"], reverse=True)
    return results