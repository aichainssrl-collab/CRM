from typing import Optional
from app.schemas.booking import BookingCreate
from app.services.db_service import (
    create_document, update_document, get_document,
    list_collection, utcnow, new_id,
)
from app.firebase_admin import db
from google.cloud.firestore_v1 import FieldFilter


async def list_available_slots() -> list[dict]:
    query = (
        db.collection("booking_slots")
        .where(filter=FieldFilter("isAvailable", "==", True))
        .order_by("startTime")
    )
    results = []
    async for snap in query.stream():
        results.append({"id": snap.id, **snap.to_dict()})
    return results


async def get_slot(slot_id: str) -> Optional[dict]:
    snap = await db.collection("booking_slots").document(slot_id).get()
    return {"id": snap.id, **snap.to_dict()} if snap.exists else None


async def create_booking(data: BookingCreate, lead_id: str = None) -> dict:
    # Verifica slot disponibile (transazione per evitare doppia prenotazione)
    slot_ref = db.collection("booking_slots").document(data.slotId)

    @db.transaction
    async def _book(transaction):
        snap = await transaction.get(slot_ref)
        if not snap.exists or not snap.to_dict().get("isAvailable", False):
            raise ValueError("Slot non disponibile")
        booking_id = new_id()
        booking_ref = db.collection("bookings").document(booking_id)
        now = utcnow()
        payload = {
            **data.model_dump(exclude={"consent_given", "consent_text"}),
            "leadId": lead_id,
            "status": "confirmed",
            "createdAt": now,
            "updatedAt": now,
        }
        transaction.set(booking_ref, payload)
        transaction.update(slot_ref, {
            "isAvailable": False,
            "bookedBy": data.email,
            "bookingId": booking_id,
            "updatedAt": now,
        })
        return {"id": booking_id, **payload}

    return await _book()


async def get_booking(booking_id: str) -> Optional[dict]:
    return await get_document("bookings", booking_id)


async def cancel_booking(booking_id: str) -> Optional[dict]:
    now = utcnow()
    booking = await get_document("bookings", booking_id)
    if not booking:
        return None

    await db.collection("bookings").document(booking_id).update({
        "status": "cancelled",
        "cancelledAt": now,
        "updatedAt": now,
    })
    # Libera lo slot
    await db.collection("booking_slots").document(booking["slotId"]).update({
        "isAvailable": True,
        "bookedBy": None,
        "bookingId": None,
        "updatedAt": now,
    })
    return await get_document("bookings", booking_id)
