from fastapi import APIRouter, Depends, HTTPException, Request
from app.deps import require_sales, UserRecord
from app.schemas.booking import BookingCreate, BookingCancelRequest
from app.services.booking_service import (
    list_available_slots, get_slot, create_booking,
    get_booking, cancel_booking,
)
from app.services.lead_service import LeadService
from app.services.gdpr_service import log_consent
from app.services.email_service import send_email
from app.utils.cloud_tasks import enqueue_task
from app.limiter import limiter

router = APIRouter()


@router.get("/slots")
async def get_available_slots():
    """Endpoint pubblico — lettura slot disponibili."""
    return await list_available_slots()


@router.post("", status_code=201)
@limiter.limit("3/minute")
async def create_new_booking(request: Request, data: BookingCreate):
    """Endpoint pubblico — crea prenotazione demo."""
    ip = request.client.host if request.client else "127.0.0.1"

    if not data.consent_given:
        raise HTTPException(422, "Consenso GDPR obbligatorio")

    slot = await get_slot(data.slotId)
    if not slot or not slot.get("isAvailable"):
        raise HTTPException(409, "Slot non disponibile")

    # Trova o crea lead
    service = LeadService()
    lead = await service.create_or_update_from_form(
        email=data.email,
        form_data=data.model_dump(),
        form_type="booking_request",
        source="booking",
        ip=ip,
        user_agent=request.headers.get("user-agent", ""),
    )

    try:
        booking = await create_booking(data, lead_id=lead["id"])
    except ValueError as exc:
        raise HTTPException(409, str(exc))

    await log_consent(lead["id"], "granted", "service_communication", data.consent_text, ip)
    await enqueue_task("recalculate-score", {"lead_id": lead["id"]})

    return {"success": True, "bookingId": booking["id"]}


@router.get("/{booking_id}")
async def get_booking_by_id(
    booking_id: str,
    user: UserRecord = Depends(require_sales),
):
    booking = await get_booking(booking_id)
    if not booking:
        raise HTTPException(404, "Prenotazione non trovata")
    return booking


@router.post("/{booking_id}/cancel", status_code=200)
async def cancel_booking_by_id(
    booking_id: str,
    data: BookingCancelRequest,
    user: UserRecord = Depends(require_sales),
):
    booking = await get_booking(booking_id)
    if not booking:
        raise HTTPException(404, "Prenotazione non trovata")
    if booking["status"] == "cancelled":
        raise HTTPException(409, "Prenotazione già annullata")
    return await cancel_booking(booking_id)
