"""
Invoices API — /api/v1/invoices/
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from app.deps import require_sales, UserRecord
from app.services import invoice_service

router = APIRouter()


class InvoiceItem(BaseModel):
    productId: Optional[str] = None
    name: str = ""
    description: str = ""
    quantity: float = 1
    unitPrice: float = 0


class InvoiceCreate(BaseModel):
    title: str
    clientName: str = ""
    clientEmail: str = ""
    leadId: Optional[str] = None
    dealId: Optional[str] = None
    proposalId: Optional[str] = None
    items: list[InvoiceItem] = Field(default_factory=list)
    taxRate: float = 0
    currency: str = "EUR"
    issueDate: Optional[str] = None
    dueDate: Optional[str] = None
    notes: str = ""


class InvoiceUpdate(BaseModel):
    title: Optional[str] = None
    clientName: Optional[str] = None
    clientEmail: Optional[str] = None
    items: Optional[list[InvoiceItem]] = None
    taxRate: Optional[float] = None
    currency: Optional[str] = None
    dueDate: Optional[str] = None
    notes: Optional[str] = None


@router.get("/")
async def list_invoices(
    status: Optional[str] = None,
    user: UserRecord = Depends(require_sales),
):
    return await invoice_service.list_invoices(status)


@router.get("/stats")
async def invoice_stats(user: UserRecord = Depends(require_sales)):
    return await invoice_service.invoice_stats()


@router.post("/from-proposal/{proposal_id}")
async def invoice_from_proposal(
    proposal_id: str,
    user: UserRecord = Depends(require_sales),
):
    doc = await invoice_service.create_from_proposal(proposal_id, user.uid)
    if not doc:
        raise HTTPException(
            status_code=404,
            detail="Proposta non trovata o non accettata",
        )
    return doc


@router.get("/{invoice_id}")
async def get_invoice(
    invoice_id: str,
    user: UserRecord = Depends(require_sales),
):
    doc = await invoice_service.get_invoice(invoice_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Fattura non trovata")
    return doc


@router.post("/")
async def create_invoice(
    body: InvoiceCreate,
    user: UserRecord = Depends(require_sales),
):
    return await invoice_service.create_invoice(body.model_dump(), user.uid)


@router.patch("/{invoice_id}")
async def update_invoice(
    invoice_id: str,
    body: InvoiceUpdate,
    user: UserRecord = Depends(require_sales),
):
    data = {k: v for k, v in body.model_dump().items() if v is not None}
    doc = await invoice_service.update_invoice(invoice_id, data)
    if not doc:
        raise HTTPException(status_code=404, detail="Fattura non trovata")
    return doc


@router.delete("/{invoice_id}")
async def delete_invoice(
    invoice_id: str,
    user: UserRecord = Depends(require_sales),
):
    ok = await invoice_service.delete_invoice(invoice_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Fattura non trovata")
    return {"ok": True}


@router.post("/{invoice_id}/send")
async def send_invoice(
    invoice_id: str,
    user: UserRecord = Depends(require_sales),
):
    doc = await invoice_service.mark_sent(invoice_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Fattura non trovata o non in bozza")
    return doc


@router.post("/{invoice_id}/mark-paid")
async def pay_invoice(
    invoice_id: str,
    user: UserRecord = Depends(require_sales),
):
    doc = await invoice_service.mark_paid(invoice_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Fattura non trovata o stato non valido")
    return doc


@router.post("/{invoice_id}/cancel")
async def cancel_invoice(
    invoice_id: str,
    user: UserRecord = Depends(require_sales),
):
    doc = await invoice_service.mark_cancelled(invoice_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Fattura non trovata o già pagata")
    return doc
