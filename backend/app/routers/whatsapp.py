"""
WhatsApp / Inbox API — /api/v1/whatsapp/
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field

from app.deps import require_sales, UserRecord
from app.services import whatsapp_service

router = APIRouter()
public_router = APIRouter()


class ConversationCreate(BaseModel):
    phone: str
    leadId: Optional[str] = None
    leadName: str = ""


class MessageSend(BaseModel):
    body: str = Field(min_length=1, max_length=4096)


class InboundBody(BaseModel):
    phone: str
    body: str = ""
    waMessageId: str = ""


@router.get("/conversations")
async def list_conversations(
    status: Optional[str] = None,
    user: UserRecord = Depends(require_sales),
):
    return await whatsapp_service.list_conversations(status)


@router.get("/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    user: UserRecord = Depends(require_sales),
):
    doc = await whatsapp_service.get_conversation(conversation_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Conversazione non trovata")
    return doc


@router.post("/conversations")
async def create_conversation(
    body: ConversationCreate,
    user: UserRecord = Depends(require_sales),
):
    return await whatsapp_service.create_conversation(body.model_dump(), user.uid)


@router.get("/conversations/{conversation_id}/messages")
async def list_messages(
    conversation_id: str,
    limit: int = Query(100, ge=1, le=500),
    user: UserRecord = Depends(require_sales),
):
    return await whatsapp_service.list_messages(conversation_id, limit=limit)


@router.post("/conversations/{conversation_id}/messages")
async def send_message(
    conversation_id: str,
    body: MessageSend,
    user: UserRecord = Depends(require_sales),
):
    msg = await whatsapp_service.send_message(conversation_id, body.body, user.uid)
    if not msg:
        raise HTTPException(status_code=404, detail="Conversazione non trovata")
    return msg


@router.post("/conversations/{conversation_id}/read")
async def mark_read(
    conversation_id: str,
    user: UserRecord = Depends(require_sales),
):
    doc = await whatsapp_service.mark_read(conversation_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Conversazione non trovata")
    return doc


@router.post("/conversations/{conversation_id}/close")
async def close_conversation(
    conversation_id: str,
    user: UserRecord = Depends(require_sales),
):
    doc = await whatsapp_service.close_conversation(conversation_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Conversazione non trovata")
    return doc


@router.post("/conversations/{conversation_id}/reopen")
async def reopen_conversation(
    conversation_id: str,
    user: UserRecord = Depends(require_sales),
):
    doc = await whatsapp_service.reopen_conversation(conversation_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Conversazione non trovata")
    return doc


@router.get("/stats")
async def inbox_stats(user: UserRecord = Depends(require_sales)):
    return await whatsapp_service.inbox_stats()


# ── Public webhook (Meta Cloud API style) ───────────────────────
@public_router.get("/webhook")
async def webhook_verify(
    hub_mode: Optional[str] = Query(None, alias="hub.mode"),
    hub_verify_token: Optional[str] = Query(None, alias="hub.verify_token"),
    hub_challenge: Optional[str] = Query(None, alias="hub.challenge"),
):
    """Meta subscription verification handshake."""
    from app.config import settings

    if hub_mode == "subscribe" and hub_verify_token == settings.WHATSAPP_VERIFY_TOKEN:
        return int(hub_challenge or 0)
    raise HTTPException(status_code=403, detail="Verification failed")


@public_router.post("/webhook")
async def webhook_inbound(request: Request):
    """Inbound WhatsApp messages from Meta (or manual injection in tests)."""
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    # Meta Cloud API envelope or simple {phone, body}
    phone = ""
    body = ""
    wa_id = ""
    entry = (payload.get("entry") or [{}])[0]
    changes = (entry.get("changes") or [{}])[0]
    value = changes.get("value") or {}
    messages = value.get("messages") or []
    if messages:
        m = messages[0]
        phone = m.get("from", "")
        wa_id = m.get("id", "")
        body = (m.get("text") or {}).get("body", "")
    else:
        phone = payload.get("phone", "")
        body = payload.get("body", "")
        wa_id = payload.get("waMessageId", "")

    if not phone:
        raise HTTPException(status_code=400, detail="Missing phone")
    result = await whatsapp_service.receive_inbound(phone, body, wa_id)
    return {"ok": True, "conversationId": result["conversation"].get("id")}
