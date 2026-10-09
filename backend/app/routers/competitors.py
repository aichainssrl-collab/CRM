"""
Competitor Intelligence API — /api/v1/competitors/
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.deps import require_sales, UserRecord
from app.services import competitor_service

router = APIRouter()


class CompetitorCreate(BaseModel):
    name: str
    website: str = ""
    description: str = ""
    tags: list[str] = Field(default_factory=list)


class CompetitorUpdate(BaseModel):
    name: Optional[str] = None
    website: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[list[str]] = None
    status: Optional[str] = None


class ScanBody(BaseModel):
    html: Optional[str] = None  # test / offline injection


@router.get("/")
async def list_competitors(
    status: Optional[str] = None,
    tag: Optional[str] = None,
    user: UserRecord = Depends(require_sales),
):
    return await competitor_service.list_competitors(status, tag)


@router.get("/stats")
async def competitor_stats(user: UserRecord = Depends(require_sales)):
    return await competitor_service.competitor_stats()


@router.get("/changes")
async def all_changes(
    limit: int = 50,
    user: UserRecord = Depends(require_sales),
):
    return await competitor_service.list_changes(None, limit=limit)


@router.get("/{competitor_id}")
async def get_competitor(
    competitor_id: str,
    user: UserRecord = Depends(require_sales),
):
    doc = await competitor_service.get_competitor(competitor_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Competitor non trovato")
    return doc


@router.post("/")
async def create_competitor(
    body: CompetitorCreate,
    user: UserRecord = Depends(require_sales),
):
    return await competitor_service.create_competitor(body.model_dump(), user.uid)


@router.patch("/{competitor_id}")
async def update_competitor(
    competitor_id: str,
    body: CompetitorUpdate,
    user: UserRecord = Depends(require_sales),
):
    data = {k: v for k, v in body.model_dump().items() if v is not None}
    doc = await competitor_service.update_competitor(competitor_id, data)
    if not doc:
        raise HTTPException(status_code=404, detail="Competitor non trovato")
    return doc


@router.delete("/{competitor_id}")
async def delete_competitor(
    competitor_id: str,
    user: UserRecord = Depends(require_sales),
):
    ok = await competitor_service.delete_competitor(competitor_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Competitor non trovato")
    return {"ok": True}


@router.post("/{competitor_id}/scan")
async def scan_competitor(
    competitor_id: str,
    body: Optional[ScanBody] = None,
    user: UserRecord = Depends(require_sales),
):
    try:
        result = await competitor_service.scan_competitor(
            competitor_id, html=body.html if body else None
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Scan fallito: {exc}")
    if not result:
        raise HTTPException(status_code=404, detail="Competitor non trovato")
    return result


@router.post("/scan-all")
async def scan_all(user: UserRecord = Depends(require_sales)):
    return await competitor_service.scan_all()


@router.get("/{competitor_id}/snapshots")
async def list_snapshots(
    competitor_id: str,
    limit: int = 20,
    user: UserRecord = Depends(require_sales),
):
    return await competitor_service.list_snapshots(competitor_id, limit=limit)


@router.get("/{competitor_id}/changes")
async def list_changes(
    competitor_id: str,
    limit: int = 50,
    user: UserRecord = Depends(require_sales),
):
    return await competitor_service.list_changes(competitor_id, limit=limit)
