"""
Data Export API — /api/v1/export/
"""
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from typing import Optional
from app.deps import require_sales, UserRecord
from app.services import export_service
import io

router = APIRouter()


@router.get("/leads")
async def export_leads(
    status: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    user: UserRecord = Depends(require_sales),
):
    filters = {}
    if status:
        filters["status"] = status
    if source:
        filters["source"] = source

    csv_content = await export_service.export_leads_csv(filters)
    return StreamingResponse(
        io.BytesIO(csv_content.encode("utf-8-sig")),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=leads_export.csv"},
    )


@router.get("/deals")
async def export_deals(
    stage: Optional[str] = Query(None),
    user: UserRecord = Depends(require_sales),
):
    filters = {}
    if stage:
        filters["stage"] = stage

    csv_content = await export_service.export_deals_csv(filters)
    return StreamingResponse(
        io.BytesIO(csv_content.encode("utf-8-sig")),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=deals_export.csv"},
    )


@router.get("/contacts")
async def export_contacts(
    user: UserRecord = Depends(require_sales),
):
    csv_content = await export_service.export_contacts_csv()
    return StreamingResponse(
        io.BytesIO(csv_content.encode("utf-8-sig")),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=contacts_export.csv"},
    )