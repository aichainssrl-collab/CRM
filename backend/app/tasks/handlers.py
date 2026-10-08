import asyncio
import functools
from fastapi import APIRouter, Request, HTTPException
from app.services.db_service import db, utcnow
from app.config import settings
from app.services.scoring_service import calculate_lead_score
from app.services.email_service import send_welcome_email, send_sequence_email
from app.services.lead_service import LeadService
from app.services.enrichment_service import EnrichmentService

router = APIRouter()


async def verify_cloud_tasks_request(request: Request) -> None:
    """Verifica OIDC token Cloud Tasks. In DEBUG mode salta la verifica."""
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
    new_score = await calculate_lead_score(payload["lead_id"])
    return {"success": True, "score": new_score}


@router.post("/send-welcome-email")
async def handle_send_welcome_email(request: Request):
    await verify_cloud_tasks_request(request)
    payload = await request.json()
    lead_id = payload["lead_id"]

    lead = await db["leads"].find_one({"_id": lead_id})
    if not lead:
        return {"success": False, "reason": "lead_not_found"}

    lead = dict(lead)
    lead["id"] = lead.pop("_id")
    await send_welcome_email(lead)
    return {"success": True}


@router.post("/process-form-submission")
async def handle_process_form_submission(request: Request):
    await verify_cloud_tasks_request(request)
    payload = await request.json()

    submission_id = payload.get("submission_id")
    if not submission_id:
        raise HTTPException(400, "submission_id richiesto")

    sub_doc = await db["form_submissions"].find_one({"_id": submission_id})
    if not sub_doc:
        return {"success": False, "reason": "submission_not_found"}

    service = LeadService()
    lead = await service.create_or_update_from_form(
        email=sub_doc["email"],
        form_data=sub_doc.get("data", {}),
        form_type=sub_doc.get("formType", "unknown"),
        source=sub_doc.get("source", "form"),
        ip=sub_doc.get("ip", ""),
        user_agent=sub_doc.get("userAgent", ""),
    )

    await db["form_submissions"].update_one(
        {"_id": submission_id},
        {"$set": {"processedAt": utcnow(), "leadId": lead["id"]}},
    )
    return {"success": True, "lead_id": lead["id"]}


@router.post("/email-sequence")
async def handle_email_sequence(request: Request):
    await verify_cloud_tasks_request(request)
    payload = await request.json()
    await send_sequence_email(
        lead_id=payload["lead_id"],
        sequence=payload["sequence"],
        step=payload.get("step", 0),
    )
    return {"success": True}


@router.post("/enrich-lead")
async def handle_enrich_lead(request: Request):
    """
    Arricchisce un lead con dati estratti dal web tramite Scrapling.
    Chiamato automaticamente alla creazione del lead (delay 5s) o manualmente
    tramite POST /api/v1/leads/{id}/enrich.
    """
    await verify_cloud_tasks_request(request)
    payload = await request.json()
    lead_id = payload.get("lead_id")
    if not lead_id:
        return {"success": False, "reason": "missing lead_id"}

    service = EnrichmentService()
    updates = await service.enrich(lead_id)
    return {
        "success": True,
        "lead_id": lead_id,
        "fields_updated": [k for k in updates if k not in ("enrichedAt", "enrichmentSource", "updatedAt")],
    }


@router.post("/notify-sales")
async def handle_notify_sales(request: Request):
    await verify_cloud_tasks_request(request)
    payload = await request.json()
    lead_id = payload.get("lead_id")

    lead = await db["leads"].find_one({"_id": lead_id})
    if lead:
        from app.services.email_service import send_sales_notification
        lead = dict(lead)
        lead["id"] = lead.pop("_id")
        await send_sales_notification(lead)

    return {"success": True}
