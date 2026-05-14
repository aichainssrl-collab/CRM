import httpx
import logging
from app.config import settings

logger = logging.getLogger(__name__)

RESEND_EU_URL = "https://api.eu.resend.com/emails"


async def send_email(
    to: str,
    subject: str,
    html: str,
    reply_to: str = None,
) -> str | None:
    """Invia email tramite Resend API EU. Ritorna l'ID email o None se fallisce."""
    if not settings.RESEND_API_KEY or settings.RESEND_API_KEY.startswith("re_fake"):
        logger.info(f"[EMAIL MOCK] to={to} subject={subject}")
        return "mock-email-id"

    payload = {
        "from": settings.EMAIL_FROM,
        "to": [to],
        "subject": subject,
        "html": html,
    }
    if reply_to:
        payload["reply_to"] = reply_to

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                RESEND_EU_URL,
                headers={"Authorization": f"Bearer {settings.RESEND_API_KEY}"},
                json=payload,
            )
            resp.raise_for_status()
            return resp.json().get("id")
    except Exception as exc:
        logger.error(f"Errore invio email a {to}: {exc}")
        return None


async def send_welcome_email(lead: dict) -> str | None:
    first_name = lead.get("firstName") or "Ciao"
    return await send_email(
        to=lead["email"],
        subject="Ecco il tuo AiChain Playbook",
        html=f"""
        <p>Ciao {first_name},</p>
        <p>grazie per aver scaricato il nostro Playbook sull'automazione AI per studi legali e professionisti.</p>
        <p>Trovi il download al link: <a href="https://crm.aichainsolutions.net/downloads/aichain-playbook.pdf">Scarica Playbook</a></p>
        <p>Se hai domande o vuoi scoprire come AiChain può aiutare il tuo studio,
        <a href="https://crm.aichainsolutions.net/forms/booking">prenota una demo gratuita</a>.</p>
        <p>A presto,<br>Il team AiChain Solutions</p>
        """,
    )


async def send_sequence_email(lead_id: str, sequence: str, step: int, db) -> bool:
    """Placeholder per sequenze drip — implementazione completa in Fase 2."""
    logger.info(f"[SEQUENCE] lead={lead_id} sequence={sequence} step={step}")
    return True


async def send_sales_notification(lead: dict) -> str | None:
    """Notifica al team sales di un nuovo lead entrante."""
    return await send_email(
        to=settings.EMAIL_FROM,
        subject=f"[CRM] Nuovo lead: {lead.get('email')}",
        html=f"""
        <p>Nuovo lead registrato nel CRM:</p>
        <ul>
            <li><b>Email:</b> {lead.get('email')}</li>
            <li><b>Nome:</b> {lead.get('firstName', '')} {lead.get('lastName', '')}</li>
            <li><b>Azienda:</b> {lead.get('companyName', 'N/D')}</li>
            <li><b>Fonte:</b> {lead.get('source', 'N/D')}</li>
        </ul>
        """,
    )
