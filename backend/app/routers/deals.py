from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from app.deps import require_sales, UserRecord
from app.schemas.deal import DealCreate, DealUpdate
from app.services.deal_service import create_deal, get_deal, list_deals, update_deal, delete_deal
from app.services.db_service import get_document

router = APIRouter()


@router.get("")
async def get_deals(
    lead_id: Optional[str] = Query(None),
    stage: Optional[str] = Query(None),
    assigned_to: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    last_doc_id: Optional[str] = Query(None),
    user: UserRecord = Depends(require_sales),
):
    return await list_deals(
        lead_id=lead_id,
        stage=stage,
        assigned_to=assigned_to,
        limit=limit,
        last_doc_id=last_doc_id,
    )


@router.post("", status_code=201)
async def create_new_deal(
    data: DealCreate,
    lead_id: str = Query(..., description="ID del lead associato"),
    user: UserRecord = Depends(require_sales),
):
    lead = await get_document("leads", lead_id)
    if not lead:
        raise HTTPException(404, "Lead non trovato")

    return await create_deal(data, lead_id=lead_id, created_by=user.uid)


@router.get("/{deal_id}")
async def get_deal_by_id(
    deal_id: str,
    user: UserRecord = Depends(require_sales),
):
    deal = await get_deal(deal_id)
    if not deal:
        raise HTTPException(404, "Deal non trovato")
    return deal


@router.patch("/{deal_id}")
async def update_deal_by_id(
    deal_id: str,
    data: DealUpdate,
    user: UserRecord = Depends(require_sales),
):
    deal = await get_deal(deal_id)
    if not deal:
        raise HTTPException(404, "Deal non trovato")
    updated = await update_deal(deal_id, data, updated_by=user.uid)
    return updated


@router.delete("/{deal_id}", status_code=204)
async def delete_deal_by_id(
    deal_id: str,
    user: UserRecord = Depends(require_sales),
):
    deal = await get_deal(deal_id)
    if not deal:
        raise HTTPException(404, "Deal non trovato")
    await delete_deal(deal_id)
