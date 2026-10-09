"""
Audit Log, System Stats & Saved Filters API — /api/v1/admin/
"""
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from typing import Optional
from app.deps import require_sales, require_admin, UserRecord
from app.services import audit_service, system_service, saved_filter_service

router = APIRouter()


class SavedFilterCreate(BaseModel):
    name: str
    entityType: str
    filters: dict = {}
    isGlobal: bool = False


class SavedFilterUpdate(BaseModel):
    name: Optional[str] = None
    filters: Optional[dict] = None


# ── Audit Log ──────────────────────────────────────────────────
@router.get("/audit-log")
async def list_audit_log(
    user_id: Optional[str] = Query(None),
    entity_type: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    user: UserRecord = Depends(require_admin),
):
    return await audit_service.list_audit_log(
        user_id=user_id, entity_type=entity_type, action=action, limit=limit,
    )


@router.get("/audit-log/stats")
async def audit_stats(
    days: int = Query(30, ge=1, le=365),
    user: UserRecord = Depends(require_admin),
):
    return await audit_service.get_audit_stats(days)


# ── System Stats ──────────────────────────────────────────────
@router.get("/system-stats")
async def system_stats(
    user: UserRecord = Depends(require_admin),
):
    return await system_service.get_system_stats()


# ── Saved Filters ──────────────────────────────────────────────
@router.get("/saved-filters")
async def list_saved_filters(
    entity_type: Optional[str] = Query(None),
    user: UserRecord = Depends(require_sales),
):
    return await saved_filter_service.list_saved_filters(user.uid, entity_type)


@router.post("/saved-filters")
async def create_saved_filter(
    body: SavedFilterCreate,
    user: UserRecord = Depends(require_sales),
):
    return await saved_filter_service.create_saved_filter(user.uid, body.model_dump())


@router.patch("/saved-filters/{filter_id}")
async def update_saved_filter(
    filter_id: str,
    body: SavedFilterUpdate,
    user: UserRecord = Depends(require_sales),
):
    data = {k: v for k, v in body.model_dump().items() if v is not None}
    result = await saved_filter_service.update_saved_filter(filter_id, data)
    return result


@router.delete("/saved-filters/{filter_id}")
async def delete_saved_filter(
    filter_id: str,
    user: UserRecord = Depends(require_sales),
):
    ok = await saved_filter_service.delete_saved_filter(filter_id)
    return {"ok": ok}