from typing import Optional
from app.schemas.booking import BookingCreate
from app.services.db_service import db, get_document, utcnow, new_id
from pymongo import ASCENDING


async def list_available_slots() -> list[dict]:
    cursor = db["booking_slots"].find({"isAvailable": True}).sort("startTime", ASCENDING)
    results = []
    async for doc in cursor:
        doc = dict(doc)
        doc["id"] = doc.pop("_id")
        results.append(doc)
    return results


async def get_slot(slot_id: str) -> Optional[dict]:
    doc = await db["booking_slots"].find_one({"_id": slot_id})
    if not doc:
        return None
    doc = dict(doc)
    doc["id"] = doc.pop("_id")
    return doc


async def create_booking(data: BookingCreate, lead_id: str = None) -> dict:
    slot = await db["booking_slots"].find_one({"_id": data.slotId, "isAvailable": True})
    if not slot:
        raise ValueError("Slot non disponibile")

    booking_id = new_id()
    now = utcnow()
    payload = {
        "_id": booking_id,
        **data.model_dump(exclude={"consent_given", "consent_text"}),
        "leadId": lead_id,
        "status": "confirmed",
        "createdAt": now,
        "updatedAt": now,
        "deletedAt": None,
    }
    await db["bookings"].insert_one(payload)
    await db["booking_slots"].update_one(
        {"_id": data.slotId},
        {"$set": {"isAvailable": False, "bookedBy": data.email, "bookingId": booking_id, "updatedAt": now}},
    )
    doc = dict(payload)
    doc["id"] = doc.pop("_id")
    return doc


async def get_booking(booking_id: str) -> Optional[dict]:
    return await get_document("bookings", booking_id)


async def cancel_booking(booking_id: str) -> Optional[dict]:
    booking = await get_document("bookings", booking_id)
    if not booking:
        return None

    now = utcnow()
    await db["bookings"].update_one(
        {"_id": booking_id},
        {"$set": {"status": "cancelled", "cancelledAt": now, "updatedAt": now}},
    )
    slot_id = booking.get("slotId")
    if slot_id:
        await db["booking_slots"].update_one(
            {"_id": slot_id},
            {"$set": {"isAvailable": True, "bookedBy": None, "bookingId": None, "updatedAt": now}},
        )
    return await get_document("bookings", booking_id)
