from typing import Optional
from app.schemas.deal import DealCreate, DealUpdate
from app.services.db_service import (
    create_document, update_document, get_document,
    list_collection, soft_delete,
)
from app.services.activity_service import append_activity
from app.services import workflow_service


async def create_deal(data: DealCreate, lead_id: str, created_by: str) -> dict:
    payload = {**data.model_dump(), "leadId": lead_id, "createdBy": created_by}
    deal = await create_document("deals", payload)
    await append_activity(lead_id, {
        "type": "deal_created",
        "title": f"Opportunità creata: {deal['title']}",
        "userId": created_by,
        "metadata": {"dealId": deal["id"]},
    })
    return deal


async def get_deal(deal_id: str) -> Optional[dict]:
    return await get_document("deals", deal_id)


async def list_deals(
    lead_id: str = None,
    stage: str = None,
    assigned_to: str = None,
    last_doc_id: str = None,
    limit: int = 20,
) -> list[dict]:
    filters = []
    if lead_id:
        filters.append(("leadId", "==", lead_id))
    if stage:
        filters.append(("stage", "==", stage))
    if assigned_to:
        filters.append(("assignedTo", "==", assigned_to))
    return await list_collection(
        "deals",
        filters=filters,
        order_by="createdAt",
        descending=True,
        limit=limit,
        last_doc_id=last_doc_id,
    )


async def update_deal(deal_id: str, data: DealUpdate, updated_by: str) -> Optional[dict]:
    update_data = data.model_dump(exclude_unset=True)
    deal = await update_document("deals", deal_id, update_data)

    if "stage" in update_data and deal:
        await append_activity(deal["leadId"], {
            "type": "stage_changed",
            "title": f"Opportunità: stadio → {update_data['stage']}",
            "userId": updated_by,
            "metadata": {"dealId": deal_id, "to": update_data["stage"]},
        })
        try:
            await workflow_service.run_workflows("deal_stage_changed", deal, updated_by)
        except Exception:
            pass  # workflow failure must not break deal update
    return deal


async def delete_deal(deal_id: str) -> None:
    await soft_delete("deals", deal_id)
