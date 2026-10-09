"""
Email sequence service — business logic for drip campaigns.
"""
from datetime import datetime, timezone, timedelta
from typing import Optional
from app.services.db_service import db, new_id, utcnow, _to_dict
from app.services.email_service import send_email
from app.config import settings
import logging

logger = logging.getLogger(__name__)


async def create_sequence(data: dict, created_by: str) -> dict:
    """Create a new email sequence with steps."""
    now = utcnow()
    doc = {
        "_id": new_id(),
        "name": data["name"],
        "description": data.get("description", ""),
        "steps": data.get("steps", []),
        "isActive": False,
        "enrollments": [],
        "createdBy": created_by,
        "createdAt": now,
        "updatedAt": now,
        "deletedAt": None,
    }
    await db["email_sequences"].insert_one(doc)
    return _to_dict(doc)


async def list_sequences(include_deleted: bool = False) -> list[dict]:
    query = {} if include_deleted else {"deletedAt": None}
    cursor = db["email_sequences"].find(query).sort("createdAt", -1)
    docs = await cursor.to_list(length=100)
    return [_to_dict(d) for d in docs]


async def get_sequence(seq_id: str) -> Optional[dict]:
    doc = await db["email_sequences"].find_one({"_id": seq_id, "deletedAt": None})
    return _to_dict(doc) if doc else None


async def update_sequence(seq_id: str, data: dict) -> Optional[dict]:
    now = utcnow()
    update = {**data, "updatedAt": now}
    doc = await db["email_sequences"].find_one_and_update(
        {"_id": seq_id, "deletedAt": None},
        {"$set": update},
        return_document=True,
    )
    return _to_dict(doc) if doc else None


async def delete_sequence(seq_id: str) -> bool:
    now = utcnow()
    result = await db["email_sequences"].update_one(
        {"_id": seq_id, "deletedAt": None},
        {"$set": {"deletedAt": now, "updatedAt": now}},
    )
    return result.modified_count > 0


async def set_active(seq_id: str, active: bool) -> Optional[dict]:
    return await update_sequence(seq_id, {"isActive": active})


async def enroll_lead(seq_id: str, lead_id: str) -> Optional[dict]:
    """Enroll a lead in a sequence. Starts at step 0."""
    seq = await get_sequence(seq_id)
    if not seq:
        return None

    lead = await db["leads"].find_one({"_id": lead_id, "deletedAt": None})
    if not lead:
        return None

    now = utcnow()
    steps = seq.get("steps", [])
    first_send = now if steps else None

    enrollment = {
        "id": new_id(),
        "leadId": lead_id,
        "leadEmail": lead.get("email"),
        "leadName": f"{lead.get('firstName', '')} {lead.get('lastName', '')}".strip() or lead.get("email"),
        "currentStep": 0,
        "status": "active",  # active | paused | completed | unsubscribed
        "startedAt": now,
        "nextSendAt": first_send,
        "completedAt": None,
    }

    await db["email_sequences"].update_one(
        {"_id": seq_id},
        {"$push": {"enrollments": enrollment}, "$set": {"updatedAt": now}},
    )

    # Send first step immediately
    if steps:
        await _send_step(lead, seq, 0)

    return enrollment


async def _send_step(lead: dict, sequence: dict, step_index: int) -> bool:
    """Send a single step email to a lead."""
    steps = sequence.get("steps", [])
    if step_index >= len(steps):
        return False

    step = steps[step_index]
    subject = step.get("subject", "AiChain Solutions")
    body_html = step.get("bodyHtml", "<p>Ciao!</p>")

    # Personalize
    first_name = lead.get("firstName") or ""
    body_html = body_html.replace("{firstName}", first_name)
    body_html = body_html.replace("{company}", lead.get("companyName", ""))
    subject = subject.replace("{firstName}", first_name)

    email_id = await send_email(
        to=lead["email"],
        subject=subject,
        html=body_html,
    )

    if email_id:
        logger.info(f"[SEQUENCE] Sent step {step_index} of '{sequence['name']}' to {lead['email']} (email_id={email_id})")

        # Log the send
        await db["email_sends"].insert_one({
            "_id": new_id(),
            "sequenceId": sequence["_id"],
            "leadId": lead["_id"],
            "stepIndex": step_index,
            "emailId": email_id,
            "subject": subject,
            "sentAt": utcnow(),
        })

    return email_id is not None


async def advance_enrollment(seq_id: str, enrollment_id: str) -> Optional[dict]:
    """Advance an enrollment to the next step."""
    seq = await get_sequence(seq_id)
    if not seq:
        return None

    enrollments = seq.get("enrollments", [])
    enrollment = next((e for e in enrollments if e["id"] == enrollment_id), None)
    if not enrollment or enrollment["status"] != "active":
        return None

    steps = seq.get("steps", [])
    next_step = enrollment["currentStep"] + 1

    if next_step >= len(steps):
        # Sequence complete
        enrollment["status"] = "completed"
        enrollment["completedAt"] = utcnow()
        enrollment["nextSendAt"] = None
    else:
        enrollment["currentStep"] = next_step
        # Calculate next send time from step delay
        delay_days = steps[next_step].get("delayDays", 3)
        enrollment["nextSendAt"] = utcnow() + timedelta(days=delay_days)

        # Send immediately if delay is 0
        lead = await db["leads"].find_one({"_id": enrollment["leadId"], "deletedAt": None})
        if lead and delay_days == 0:
            await _send_step(lead, seq, next_step)

    # Update enrollment in DB
    await db["email_sequences"].update_one(
        {"_id": seq_id, "enrollments.id": enrollment_id},
        {"$set": {"enrollments.$": enrollment, "updatedAt": utcnow()}},
    )

    return enrollment


async def pause_enrollment(seq_id: str, enrollment_id: str) -> Optional[dict]:
    return await _set_enrollment_status(seq_id, enrollment_id, "paused")


async def resume_enrollment(seq_id: str, enrollment_id: str) -> Optional[dict]:
    return await _set_enrollment_status(seq_id, enrollment_id, "active")


async def unsubscribe_enrollment(seq_id: str, enrollment_id: str) -> Optional[dict]:
    return await _set_enrollment_status(seq_id, enrollment_id, "unsubscribed")


async def _set_enrollment_status(seq_id: str, enrollment_id: str, status: str) -> Optional[dict]:
    seq = await get_sequence(seq_id)
    if not seq:
        return None

    enrollments = seq.get("enrollments", [])
    enrollment = next((e for e in enrollments if e["id"] == enrollment_id), None)
    if not enrollment:
        return None

    enrollment["status"] = status
    if status == "unsubscribed":
        enrollment["completedAt"] = utcnow()
        enrollment["nextSendAt"] = None

    await db["email_sequences"].update_one(
        {"_id": seq_id, "enrollments.id": enrollment_id},
        {"$set": {"enrollments.$": enrollment, "updatedAt": utcnow()}},
    )
    return enrollment


async def process_due_enrollments() -> int:
    """Process enrollments whose nextSendAt is due. Call from cron/handler."""
    now = utcnow()
    processed = 0

    cursor = db["email_sequences"].find({"isActive": True, "deletedAt": None})
    async for seq in cursor:
        seq = _to_dict(seq)
        steps = seq.get("steps", [])
        for enrollment in seq.get("enrollments", []):
            if enrollment["status"] != "active":
                continue
            next_send = enrollment.get("nextSendAt")
            if not next_send or next_send > now:
                continue

            # Send current step
            lead = await db["leads"].find_one({"_id": enrollment["leadId"], "deletedAt": None})
            if not lead:
                enrollment["status"] = "paused"
                continue

            step_idx = enrollment["currentStep"]
            # Check if we already sent this step (don't resend on re-process)
            already_sent = await db["email_sends"].find_one({
                "sequenceId": seq["_id"],
                "leadId": enrollment["leadId"],
                "stepIndex": step_idx,
            })
            if not already_sent:
                await _send_step(lead, seq, step_idx)
                processed += 1

            # Advance to next
            await advance_enrollment(seq["_id"], enrollment["id"])

    return processed


async def get_sequence_stats(seq_id: str) -> dict:
    """Get enrollment statistics for a sequence."""
    seq = await get_sequence(seq_id)
    if not seq:
        return {}

    enrollments = seq.get("enrollments", [])
    total = len(enrollments)
    active = sum(1 for e in enrollments if e["status"] == "active")
    completed = sum(1 for e in enrollments if e["status"] == "completed")
    paused = sum(1 for e in enrollments if e["status"] == "paused")
    unsubscribed = sum(1 for e in enrollments if e["status"] == "unsubscribed")

    return {
        "total": total,
        "active": active,
        "completed": completed,
        "paused": paused,
        "unsubscribed": unsubscribed,
        "completionRate": round(completed / total * 100, 1) if total > 0 else 0,
    }