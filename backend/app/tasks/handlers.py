import asyncio
import functools
from fastapi import APIRouter, Request, HTTPException
from app.firebase_admin import db
from app.config import settings
from app.services.scoring_service import calculate_lead_score
from app.services.email_service import send_welcome_email, send_sequence_email
from app.services.lead_service import LeadService

router = APIRouter()


async def verify_cloud_tasks_request(request: Request) -> None:
    """
    Verifica che la request provenga da Cloud Tasks tramite OIDC token.
    In sviluppo (DEBUG=True) salta la verifica.
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(403, "Richiesta non autorizzata")

    if settings.DEBUG:
        return

    token = auth_header[7:]
    try:
        import google.auth.transport.requests
        import google.oauth2.id_token

        transport = google.auth.transport.requests.Request()
        verify_fn = functools.partial(
            google.oauth2.id_token.verify_oauth2_token, token, transport
        )
        claim = await asyncio.get_event_loop().run_in_executor(None, verify_fn)

        expected_sa = f"crm-backend@{settings.FIREBASE_PROJECT_ID}.iam.gserviceaccount.com"
        if claim.get("email") != expected_sa:
            raise ValueError("Service account non autorizzato")
    except Exception:
        raise HTTPException(403, "Token OIDC non valido")


@router.post("/recalculate-score")
async def handle_recalculate_score(request: Request):
    await verify_cloud_tasks_request(request)
    payload = await request.json()
    lead_id = payload["lead_id"]
    new_score = await calculate_lead_score(lead_id)
    return {"success": True, "score": new_score}


@router.post("/send-welcome-email")
async def handle_send_welcome_email(request: Request):
    await verify_cloud_tasks_request(request)
    payload = await request.json()
    lead_id = payload["lead_id"]

    snap = await db.collection("leads").document(lead_id).get()
    if not snap.exists:
        return {"success": False, "reason": "lead_not_found"}

    lead = {"id": snap.id, **snap.to_dict()}
    await send_welcome_email(lead)
    return {"success": True}


@router.post("/process-form-submission")
async def handle_process_form_submission(request: Request):
    """
    Elabora una form_submission in coda.
    Crea/aggiorna il lead e lancia le azioni downstream.
    """
    await verify_cloud_tasks_request(request)
    payload = await request.json()

    submission_id = payload.get("submission_id")
    if not submission_id:
        raise HTTPException(400, "submission_id richiesto")

    snap = await db.collection("form_submissions").document(submission_id).get()
    if not snap.exists:
        return {"success": False, "reason": "submission_not_found"}

    sub = snap.to_dict()
    service = LeadService()
    lead = await service.create_or_update_from_form(
        email=sub["email"],
        form_data=sub.get("data", {}),
        form_type=sub.get("formType", "unknown"),
        source=sub.get("source", "form"),
        ip=sub.get("ip", ""),
        user_agent=sub.get("userAgent", ""),
    )

    # Marca submission come processata
    from app.services.db_service import utcnow
    await db.collection("form_submissions").document(submission_id).update({
        "processedAt": utcnow(),
        "leadId": lead["id"],
    })
    return {"success": True, "lead_id": lead["id"]}


@router.post("/email-sequence")
async def handle_email_sequence(request: Request):
    await verify_cloud_tasks_request(request)
    payload = await request.json()
    await send_sequence_email(
        lead_id=payload["lead_id"],
        sequence=payload["sequence"],
        step=payload.get("step", 0),
        db=db,
    )
    return {"success": True}


@router.post("/notify-sales")
async def handle_notify_sales(request: Request):
    await verify_cloud_tasks_request(request)
    payload = await request.json()
    lead_id = payload.get("lead_id")

    snap = await db.collection("leads").document(lead_id).get()
    if snap.exists:
        from app.services.email_service import send_sales_notification
        await send_sales_notification({"id": snap.id, **snap.to_dict()})

    return {"success": True}
