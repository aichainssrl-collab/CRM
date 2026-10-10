"""
Email Sequences API — /api/v1/email-sequences/
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional
from app.deps import require_sales, require_admin, UserRecord
from app.services import email_sequence_service as svc

router = APIRouter()


# ── Schemas ────────────────────────────────────────────────────
class SequenceStep(BaseModel):
    subject: str
    bodyHtml: str
    delayDays: int = Field(3, ge=0, le=365)


class SequenceCreate(BaseModel):
    name: str
    description: str = ""
    steps: list[SequenceStep] = []


class SequenceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    steps: Optional[list[SequenceStep]] = None


class EnrollRequest(BaseModel):
    leadId: str


# ── CRUD ───────────────────────────────────────────────────────
@router.post("")
@router.post("/")
async def create_sequence(
    body: SequenceCreate,
    user: UserRecord = Depends(require_sales),
):
    data = body.model_dump()
    result = await svc.create_sequence(data, user.uid)
    return result


@router.get("")
@router.get("/")
async def list_sequences(
    user: UserRecord = Depends(require_sales),
):
    sequences = await svc.list_sequences()
    # Attach stats to each
    for seq in sequences:
        seq["stats"] = await svc.get_sequence_stats(seq["id"])
    return sequences


@router.post("/process-due")
async def process_due(
    user: UserRecord = Depends(require_sales),
):
    """Manually process enrollments whose nextSendAt is due (also runs via Cloud Tasks)."""
    processed = await svc.process_due_enrollments()
    return {"processed": processed}


@router.get("/{seq_id}")
async def get_sequence(
    seq_id: str,
    user: UserRecord = Depends(require_sales),
):
    seq = await svc.get_sequence(seq_id)
    if not seq:
        raise HTTPException(status_code=404, detail="Sequenza non trovata")
    seq["stats"] = await svc.get_sequence_stats(seq_id)
    return seq


@router.patch("/{seq_id}")
async def update_sequence(
    seq_id: str,
    body: SequenceUpdate,
    user: UserRecord = Depends(require_sales),
):
    data = {k: v for k, v in body.model_dump().items() if v is not None}
    result = await svc.update_sequence(seq_id, data)
    if not result:
        raise HTTPException(status_code=404, detail="Sequenza non trovata")
    return result


@router.delete("/{seq_id}")
async def delete_sequence(
    seq_id: str,
    user: UserRecord = Depends(require_admin),
):
    ok = await svc.delete_sequence(seq_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Sequenza non trovata")
    return {"ok": True}


# ── Activation ─────────────────────────────────────────────────
@router.post("/{seq_id}/activate")
async def activate_sequence(
    seq_id: str,
    user: UserRecord = Depends(require_sales),
):
    result = await svc.set_active(seq_id, True)
    if not result:
        raise HTTPException(status_code=404, detail="Sequenza non trovata")
    return result


@router.post("/{seq_id}/deactivate")
async def deactivate_sequence(
    seq_id: str,
    user: UserRecord = Depends(require_sales),
):
    result = await svc.set_active(seq_id, False)
    if not result:
        raise HTTPException(status_code=404, detail="Sequenza non trovata")
    return result


# ── Enrollments ────────────────────────────────────────────────
@router.post("/{seq_id}/enroll")
async def enroll_lead(
    seq_id: str,
    body: EnrollRequest,
    user: UserRecord = Depends(require_sales),
):
    result = await svc.enroll_lead(seq_id, body.leadId)
    if result is None:
        raise HTTPException(status_code=404, detail="Sequenza o lead non trovato")
    return result


@router.post("/{seq_id}/enrollments/{enrollment_id}/advance")
async def advance_enrollment(
    seq_id: str,
    enrollment_id: str,
    user: UserRecord = Depends(require_sales),
):
    result = await svc.advance_enrollment(seq_id, enrollment_id)
    if not result:
        raise HTTPException(status_code=404, detail="Enrollment non trovato")
    return result


@router.post("/{seq_id}/enrollments/{enrollment_id}/pause")
async def pause_enrollment(
    seq_id: str,
    enrollment_id: str,
    user: UserRecord = Depends(require_sales),
):
    result = await svc.pause_enrollment(seq_id, enrollment_id)
    if not result:
        raise HTTPException(status_code=404, detail="Enrollment non trovato")
    return result


@router.post("/{seq_id}/enrollments/{enrollment_id}/resume")
async def resume_enrollment(
    seq_id: str,
    enrollment_id: str,
    user: UserRecord = Depends(require_sales),
):
    result = await svc.resume_enrollment(seq_id, enrollment_id)
    if not result:
        raise HTTPException(status_code=404, detail="Enrollment non trovato")
    return result


@router.post("/{seq_id}/enrollments/{enrollment_id}/unsubscribe")
async def unsubscribe_enrollment(
    seq_id: str,
    enrollment_id: str,
    user: UserRecord = Depends(require_sales),
):
    result = await svc.unsubscribe_enrollment(seq_id, enrollment_id)
    if not result:
        raise HTTPException(status_code=404, detail="Enrollment non trovato")
    return result


# ── Stats ──────────────────────────────────────────────────────
@router.get("/{seq_id}/stats")
async def get_stats(
    seq_id: str,
    user: UserRecord = Depends(require_sales),
):
    stats = await svc.get_sequence_stats(seq_id)
    if not stats:
        raise HTTPException(status_code=404, detail="Sequenza non trovata")
    return stats