"""
Notifications & Activity Feed API — /api/v1/notifications/
"""
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from typing import Optional
from app.deps import require_sales, UserRecord
from app.services import notification_service as svc

router = APIRouter()


class MarkReadBody(BaseModel):
    notificationId: str


# ── Notifications ──────────────────────────────────────────────
@router.get("/")
async def list_notifications(
    unread_only: bool = Query(False),
    limit: int = Query(50, ge=1, le=200),
    user: UserRecord = Depends(require_sales),
):
    return await svc.list_notifications(user.uid, unread_only=unread_only, limit=limit)


@router.get("/unread-count")
async def unread_count(user: UserRecord = Depends(require_sales)):
    count = await svc.get_unread_count(user.uid)
    return {"count": count}


@router.post("/mark-read")
async def mark_read(
    body: MarkReadBody,
    user: UserRecord = Depends(require_sales),
):
    result = await svc.mark_read(body.notificationId, user.uid)
    return {"ok": result is not None}


@router.post("/mark-all-read")
async def mark_all_read(user: UserRecord = Depends(require_sales)):
    count = await svc.mark_all_read(user.uid)
    return {"marked": count}


# ── Activity Feed ──────────────────────────────────────────────
@router.get("/activity-feed")
async def activity_feed(
    limit: int = Query(50, ge=1, le=200),
    user: UserRecord = Depends(require_sales),
):
    return await svc.get_activity_feed(user.uid, limit=limit)


# ── Global Search ──────────────────────────────────────────────
@router.get("/search")
async def global_search(
    q: str = Query(..., min_length=1, max_length=100),
    user: UserRecord = Depends(require_sales),
):
    return await svc.global_search(q, user.uid)