from fastapi import APIRouter, Request, HTTPException
from app.schemas.forms import PlaybookFormData, ContactFormData
from app.services.lead_service import LeadService
from app.services.gdpr_service import log_consent
from app.services.email_service import send_welcome_email, send_sales_notification
from app.utils.cloud_tasks import enqueue_task
from app.limiter import limiter

router = APIRouter()


@router.post("/playbook", status_code=201)
@limiter.limit("5/minute")
async def submit_playbook(request: Request, data: PlaybookFormData):
    ip = request.client.host if request.client else "127.0.0.1"

    if not data.consent_given:
        raise HTTPException(422, "Consenso GDPR obbligatorio")

    service = LeadService()
    lead = await service.create_or_update_from_form(
        email=data.email,
        form_data=data.model_dump(),
        form_type="playbook_download",
        source="playbook",
        ip=ip,
        user_agent=request.headers.get("user-agent", ""),
    )

    await log_consent(lead["id"], "granted", "marketing", data.consent_text, ip)
    await enqueue_task("recalculate-score", {"lead_id": lead["id"]})
    await enqueue_task("send-welcome-email", {"lead_id": lead["id"], "type": "playbook"})

    return {"success": True, "download_url": "/downloads/aichain-playbook.pdf"}


@router.post("/contact", status_code=201)
@limiter.limit("5/minute")
async def submit_contact(request: Request, data: ContactFormData):
    ip = request.client.host if request.client else "127.0.0.1"

    if not data.consent_given:
        raise HTTPException(422, "Consenso GDPR obbligatorio")

    service = LeadService()
    lead = await service.create_or_update_from_form(
        email=data.email,
        form_data=data.model_dump(),
        form_type="contact",
        source="direct",
        ip=ip,
        user_agent=request.headers.get("user-agent", ""),
    )
    await log_consent(lead["id"], "granted", "service_communication", data.consent_text, ip)
    await enqueue_task("recalculate-score", {"lead_id": lead["id"]})
    await send_sales_notification(lead)

    return {"success": True}
