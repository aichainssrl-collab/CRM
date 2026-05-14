from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from typing import Optional
from app.deps import require_sales, require_admin, UserRecord
from app.schemas.lead import LeadCreate, LeadUpdate, LeadStageUpdate
from app.services.lead_service import LeadService
from app.utils.cloud_tasks import enqueue_task

router = APIRouter()


@router.get("")
async def list_leads(
    status: Optional[str] = Query(None),
    pipeline_stage: Optional[str] = Query(None),
    assigned_to: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    last_doc_id: Optional[str] = Query(None),
    user: UserRecord = Depends(require_sales),
):
    service = LeadService()
    return await service.list_leads(
        status=status,
        pipeline_stage=pipeline_stage,
        assigned_to=assigned_to,
        limit=limit,
        last_doc_id=last_doc_id,
    )


@router.post("", status_code=201)
async def create_lead(
    data: LeadCreate,
    user: UserRecord = Depends(require_sales),
):
    service = LeadService()
    existing = await service.find_by_email(data.email)
    if existing:
        raise HTTPException(409, f"Lead con email {data.email} già presente (id: {existing['id']})")

    lead = await service.create_lead(data, created_by=user.uid)
    await enqueue_task("recalculate-score", {"lead_id": lead["id"]})
    return lead


@router.get("/{lead_id}")
async def get_lead(
    lead_id: str,
    user: UserRecord = Depends(require_sales),
):
    service = LeadService()
    lead = await service.get_lead_with_activities(lead_id)
    if not lead:
        raise HTTPException(404, "Lead non trovato")
    return lead


@router.patch("/{lead_id}")
async def update_lead(
    lead_id: str,
    data: LeadUpdate,
    user: UserRecord = Depends(require_sales),
):
    service = LeadService()
    updated = await service.update_lead(lead_id, data, updated_by=user.uid)
    if not updated:
        raise HTTPException(404, "Lead non trovato")
    await enqueue_task("recalculate-score", {"lead_id": lead_id})
    return updated


@router.patch("/{lead_id}/stage")
async def update_stage(
    lead_id: str,
    data: LeadStageUpdate,
    user: UserRecord = Depends(require_sales),
):
    service = LeadService()
    updated = await service.update_stage(lead_id, data, updated_by=user.uid)
    if not updated:
        raise HTTPException(404, "Lead non trovato")
    return updated


@router.delete("/{lead_id}", status_code=204)
async def delete_lead(
    lead_id: str,
    user: UserRecord = Depends(require_admin),
):
    service = LeadService()
    await service.delete_lead(lead_id)


@router.post("/import", status_code=201)
async def import_leads_csv(
    file: UploadFile = File(...),
    user: UserRecord = Depends(require_sales),
):
    if not file.filename.endswith('.csv'):
        raise HTTPException(400, "Il file deve essere in formato CSV")
    
    content = await file.read()
    csv_content = content.decode('utf-8')
    
    service = LeadService()
    results = await service.import_csv(csv_content, user.uid)
    
    return results
