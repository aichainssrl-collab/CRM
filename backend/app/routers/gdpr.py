from fastapi import APIRouter, Depends, HTTPException
from app.deps import require_admin, require_sales, UserRecord
from app.schemas.gdpr import GdprEraseRequest
from app.services.gdpr_service import gdpr_export, gdpr_erase, log_consent
from app.services.db_service import get_document

router = APIRouter()


@router.get("/{lead_id}/export")
async def export_lead_data(
    lead_id: str,
    user: UserRecord = Depends(require_sales),
):
    """Art. 20 GDPR — Esporta tutti i dati personali del lead."""
    lead = await get_document("leads", lead_id)
    if not lead:
        raise HTTPException(404, "Lead non trovato")
    return await gdpr_export(lead_id)


@router.post("/{lead_id}/erase", status_code=200)
async def erase_lead_data(
    lead_id: str,
    data: GdprEraseRequest,
    user: UserRecord = Depends(require_admin),
):
    """Art. 17 GDPR — Anonimizza i dati personali del lead. Solo admin."""
    if not data.confirm:
        raise HTTPException(422, "Conferma richiesta: imposta confirm=true")

    lead = await get_document("leads", lead_id)
    if not lead:
        raise HTTPException(404, "Lead non trovato")

    await gdpr_erase(lead_id, erased_by_uid=user.uid)
    return {"success": True, "message": "Dati anonimizzati (GDPR Art.17)"}
