from fastapi import APIRouter, Depends, HTTPException
from app.deps import require_sales, UserRecord
from app.schemas.activity import ActivityCreate, ActivityResponse
from app.services.activity_service import append_activity, list_activities
from app.services.db_service import get_document

router = APIRouter()


@router.get("/{lead_id}/activities")
async def get_activities(
    lead_id: str,
    user: UserRecord = Depends(require_sales),
):
    lead = await get_document("leads", lead_id)
    if not lead:
        raise HTTPException(404, "Lead non trovato")
    return await list_activities(lead_id)


@router.post("/{lead_id}/activities", status_code=201)
async def add_activity(
    lead_id: str,
    data: ActivityCreate,
    user: UserRecord = Depends(require_sales),
):
    lead = await get_document("leads", lead_id)
    if not lead:
        raise HTTPException(404, "Lead non trovato")

    activity = await append_activity(lead_id, {
        **data.model_dump(),
        "userId": data.userId or user.uid,
    })
    return activity
