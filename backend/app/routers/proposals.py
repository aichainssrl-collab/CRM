"""
Proposals API — /api/v1/proposals/
Commercial quotes with product line items.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from app.deps import require_sales, UserRecord
from app.services import proposal_service

router = APIRouter()


class ProposalItem(BaseModel):
    productId: Optional[str] = None
    name: str = ""
    description: str = ""
    quantity: float = 1
    unitPrice: float = 0


class ProposalCreate(BaseModel):
    title: str
    clientName: str = ""
    clientEmail: str = ""
    leadId: Optional[str] = None
    dealId: Optional[str] = None
    items: list[ProposalItem] = Field(default_factory=list)
    taxRate: float = 0
    currency: str = "EUR"
    validUntil: Optional[str] = None
    notes: str = ""


class ProposalUpdate(BaseModel):
    title: Optional[str] = None
    clientName: Optional[str] = None
    clientEmail: Optional[str] = None
    leadId: Optional[str] = None
    dealId: Optional[str] = None
    items: Optional[list[ProposalItem]] = None
    taxRate: Optional[float] = None
    currency: Optional[str] = None
    validUntil: Optional[str] = None
    notes: Optional[str] = None


@router.get("/")
async def list_proposals(
    status: Optional[str] = None,
    user: UserRecord = Depends(require_sales),
):
    return await proposal_service.list_proposals(status)


@router.get("/stats")
async def proposal_stats(user: UserRecord = Depends(require_sales)):
    return await proposal_service.proposal_stats()


@router.get("/{proposal_id}")
async def get_proposal(
    proposal_id: str,
    user: UserRecord = Depends(require_sales),
):
    doc = await proposal_service.get_proposal(proposal_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Proposta non trovata")
    return doc


@router.post("/")
async def create_proposal(
    body: ProposalCreate,
    user: UserRecord = Depends(require_sales),
):
    data = body.model_dump()
    data["items"] = [i if isinstance(i, dict) else i for i in data.get("items", [])]
    return await proposal_service.create_proposal(data, user.uid)


@router.patch("/{proposal_id}")
async def update_proposal(
    proposal_id: str,
    body: ProposalUpdate,
    user: UserRecord = Depends(require_sales),
):
    data = {k: v for k, v in body.model_dump().items() if v is not None}
    doc = await proposal_service.update_proposal(proposal_id, data)
    if not doc:
        raise HTTPException(status_code=404, detail="Proposta non trovata")
    return doc


@router.delete("/{proposal_id}")
async def delete_proposal(
    proposal_id: str,
    user: UserRecord = Depends(require_sales),
):
    ok = await proposal_service.delete_proposal(proposal_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Proposta non trovata")
    return {"ok": True}


@router.post("/{proposal_id}/send")
async def send_proposal(
    proposal_id: str,
    user: UserRecord = Depends(require_sales),
):
    doc = await proposal_service.mark_sent(proposal_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Proposta non trovata o non in bozza")
    return doc


@router.post("/{proposal_id}/accept")
async def accept_proposal(
    proposal_id: str,
    user: UserRecord = Depends(require_sales),
):
    doc = await proposal_service.mark_accepted(proposal_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Proposta non trovata o stato non valido")
    return doc


@router.post("/{proposal_id}/reject")
async def reject_proposal(
    proposal_id: str,
    user: UserRecord = Depends(require_sales),
):
    doc = await proposal_service.mark_rejected(proposal_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Proposta non trovata o stato non valido")
    return doc
