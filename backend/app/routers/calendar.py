"""
Calendar & Bulk Operations API — /api/v1/calendar/
"""
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from typing import Optional
from app.deps import require_sales, UserRecord
from app.services import calendar_service, db_service
from app.services.db_service import db, utcnow

router = APIRouter()


# ── Calendar ───────────────────────────────────────────────────
@router.get("/events")
async def calendar_events(
    year: int = Query(..., ge=2020, le=2040),
    month: int = Query(..., ge=1, le=12),
    user: UserRecord = Depends(require_sales),
):
    return await calendar_service.get_calendar_events(year, month)


@router.get("/upcoming")
async def upcoming_events(
    days: int = Query(7, ge=1, le=90),
    user: UserRecord = Depends(require_sales),
):
    return await calendar_service.get_upcoming_events(days)


# ── Bulk Operations ────────────────────────────────────────────
class BulkAssignRequest(BaseModel):
    leadIds: list[str]
    assignedTo: str


class BulkStatusRequest(BaseModel):
    leadIds: list[str]
    status: str


class BulkTagRequest(BaseModel):
    leadIds: list[str]
    tags: list[str]


@router.post("/bulk/assign")
async def bulk_assign_leads(
    body: BulkAssignRequest,
    user: UserRecord = Depends(require_sales),
):
    """Bulk assign leads to a user."""
    now = utcnow()
    result = await db["leads"].update_many(
        {"_id": {"$in": body.leadIds}, "deletedAt": None},
        {"$set": {"assignedTo": body.assignedTo, "updatedAt": now}},
    )
    return {"updated": result.modified_count}


@router.post("/bulk/status")
async def bulk_update_status(
    body: BulkStatusRequest,
    user: UserRecord = Depends(require_sales),
):
    """Bulk update lead status."""
    now = utcnow()
    result = await db["leads"].update_many(
        {"_id": {"$in": body.leadIds}, "deletedAt": None},
        {"$set": {"status": body.status, "updatedAt": now}},
    )
    return {"updated": result.modified_count}


@router.post("/bulk/tags")
async def bulk_add_tags(
    body: BulkTagRequest,
    user: UserRecord = Depends(require_sales),
):
    """Bulk add tags to leads."""
    now = utcnow()
    result = await db["leads"].update_many(
        {"_id": {"$in": body.leadIds}, "deletedAt": None},
        {"$addToSet": {"tags": {"$each": body.tags}}, "$set": {"updatedAt": now}},
    )
    return {"updated": result.modified_count}


@router.post("/bulk/delete")
async def bulk_soft_delete(
    body: BulkAssignRequest,  # reuse schema — just needs leadIds
    user: UserRecord = Depends(require_sales),
):
    """Bulk soft delete leads."""
    now = utcnow()
    result = await db["leads"].update_many(
        {"_id": {"$in": body.leadIds}, "deletedAt": None},
        {"$set": {"deletedAt": now, "updatedAt": now}},
    )
    return {"deleted": result.modified_count}


# ── Team Leaderboard ───────────────────────────────────────────
@router.get("/leaderboard")
async def team_leaderboard(
    days: int = Query(30, ge=1, le=365),
    user: UserRecord = Depends(require_sales),
):
    """Team performance leaderboard."""
    from datetime import datetime, timezone, timedelta
    since = datetime.now(timezone.utc) - timedelta(days=days)

    # Deals won per user
    pipeline = [
        {"$match": {"deletedAt": None, "stage": "won", "closedAt": {"$gte": since}}},
        {"$group": {
            "_id": "$assignedTo",
            "dealsWon": {"$sum": 1},
            "revenue": {"$sum": "$value"},
        }},
        {"$sort": {"revenue": -1}},
        {"$limit": 10},
    ]
    won_by_user = {}
    async for row in db["deals"].aggregate(pipeline):
        won_by_user[row["_id"]] = {"dealsWon": row["dealsWon"], "revenue": float(row.get("revenue") or 0)}

    # Tasks completed per user
    task_pipeline = [
        {"$match": {"deletedAt": None, "status": "completed", "updatedAt": {"$gte": since}}},
        {"$group": {"_id": "$assignedTo", "tasksCompleted": {"$sum": 1}}},
    ]
    tasks_by_user = {}
    async for row in db["tasks"].aggregate(task_pipeline):
        tasks_by_user[row["_id"]] = row["tasksCompleted"]

    # Leads assigned per user
    lead_pipeline = [
        {"$match": {"deletedAt": None, "assignedTo": {"$ne": None}}},
        {"$group": {"_id": "$assignedTo", "leadsAssigned": {"$sum": 1}}},
    ]
    leads_by_user = {}
    async for row in db["leads"].aggregate(lead_pipeline):
        leads_by_user[row["_id"]] = row["leadsAssigned"]

    # Combine
    all_users = set(list(won_by_user.keys()) + list(tasks_by_user.keys()) + list(leads_by_user.keys()))
    users_map = {}
    if all_users:
        async for u in db["users"].find({"_id": {"$in": list(all_users)}}):
            users_map[u["_id"]] = u.get("displayName") or u.get("email", u["_id"])

    result = []
    for uid in all_users:
        if not uid:
            continue
        w = won_by_user.get(uid, {"dealsWon": 0, "revenue": 0})
        result.append({
            "userId": uid,
            "userName": users_map.get(uid, uid),
            "dealsWon": w["dealsWon"],
            "revenue": w["revenue"],
            "tasksCompleted": tasks_by_user.get(uid, 0),
            "leadsAssigned": leads_by_user.get(uid, 0),
            "score": w["revenue"] / 1000 + tasks_by_user.get(uid, 0) * 2,
        })

    result.sort(key=lambda x: x["score"], reverse=True)
    return result