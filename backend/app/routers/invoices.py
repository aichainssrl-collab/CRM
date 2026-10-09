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
    taxRate: float = 22
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


@router.get("/{invoice_id}/pdf")
async def get_invoice_pdf(
    invoice_id: str,
    lang: str = "it",
    user: UserRecord = Depends(require_sales),
):
    from fastapi.responses import Response
    from app.services import pdf_service, document_service

    locale = "en" if lang == "en" else "it"
    doc = await invoice_service.get_invoice(invoice_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Fattura non trovata")
    data = pdf_service.invoice_pdf(doc, lang=locale)
    number = doc.get("number") or "fattura"
    filename = f"{number}_{locale}.pdf"
    reg = await document_service.record_pdf(
        parent_type="invoice",
        parent_id=invoice_id,
        data=data,
        locale=locale,
        generated_by=user.uid,
        filename=filename,
    )
    return Response(
        content=data,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Document-Version": str(reg.get("version", 1)),
            "X-Document-Checksum": reg.get("checksum", ""),
        },
    )


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


class SendBody(BaseModel):
    lang: str = "it"
    sendEmail: bool = True


@router.post("/{invoice_id}/send")
async def send_invoice(
    invoice_id: str,
    body: Optional[SendBody] = None,
    user: UserRecord = Depends(require_sales),
):
    import base64
    from app.services import pdf_service, document_service, email_service

    locale = "en" if (body and body.lang == "en") else "it"
    doc = await invoice_service.mark_sent(invoice_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Fattura non trovata o non in bozza")

    pdf_bytes = pdf_service.invoice_pdf(doc, lang=locale)
    number = doc.get("number") or "fattura"
    filename = f"{number}_{locale}.pdf"
    await document_service.record_pdf(
        parent_type="invoice",
        parent_id=invoice_id,
        data=pdf_bytes,
        locale=locale,
        generated_by=user.uid,
        filename=filename,
    )

    want_email = body.sendEmail if body else True
    if want_email and doc.get("clientEmail"):
        if locale == "en":
            subject = f"{number} — Invoice from AiChain Solutions"
            html = f"<p>Please find attached invoice <b>{number}</b>.</p><p>Kind regards,<br>AiChain Solutions</p>"
        else:
            subject = f"{number} — Fattura AiChain Solutions"
            html = f"<p>In allegato la fattura <b>{number}</b>.</p><p>Cordiali saluti,<br>AiChain Solutions</p>"
        await email_service.send_email(
            to=doc["clientEmail"],
            subject=subject,
            html=html,
            attachments=[
                {
                    "filename": filename,
                    "content": base64.b64encode(pdf_bytes).decode("ascii"),
                }
            ],
        )
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
