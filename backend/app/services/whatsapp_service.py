"""
WhatsApp / shared inbox service.

Thin channel layer: conversations + messages linked to leads.
Outbound uses Meta WhatsApp Cloud API when credentials are set,
otherwise mock mode (logs + marks as sent). Inbound via webhook.
"""
from typing import Optional
import httpx
import logging

from app.config import settings
from app.services.db_service import db, new_id, utcnow, _to_dict
from app.services.activity_service import append_activity

logger = logging.getLogger(__name__)

STATUSES = ("open", "closed")


def normalize_phone(raw: str) -> str:
    digits = "".join(c for c in (raw or "") if c.isdigit() or c == "+")
    if digits and not digits.startswith("+"):
        digits = "+" + digits
    return digits


async def list_conversations(status: Optional[str] = None) -> list[dict]:
    query: dict = {"deletedAt": None}
    if status:
        query["status"] = status
    cursor = db["whatsapp_conversations"].find(query).sort("lastMessageAt", -1)
    docs = await cursor.to_list(length=200)
    return [_to_dict(d) for d in docs]


async def get_conversation(conversation_id: str) -> Optional[dict]:
    doc = await db["whatsapp_conversations"].find_one(
        {"_id": conversation_id, "deletedAt": None}
    )
    return _to_dict(doc) if doc else None


async def find_by_phone(phone: str) -> Optional[dict]:
    p = normalize_phone(phone)
    doc = await db["whatsapp_conversations"].find_one(
        {"phone": p, "deletedAt": None}
    )
    return _to_dict(doc) if doc else None


async def create_conversation(data: dict, created_by: str) -> dict:
    now = utcnow()
    phone = normalize_phone(data.get("phone", ""))
    doc = {
        "_id": new_id(),
        "phone": phone,
        "leadId": data.get("leadId"),
        "leadName": data.get("leadName", ""),
        "status": "open",
        "lastMessageAt": now,
        "lastInboundAt": None,
        "lastOutboundAt": None,
        "unreadCount": 0,
        "assignedTo": created_by,
        "createdBy": created_by,
        "createdAt": now,
        "updatedAt": now,
        "deletedAt": None,
    }
    await db["whatsapp_conversations"].insert_one(doc)
    return _to_dict(doc)


async def list_messages(conversation_id: str, limit: int = 100) -> list[dict]:
    cursor = (
        db["whatsapp_messages"]
        .find({"conversationId": conversation_id, "deletedAt": None})
        .sort("createdAt", 1)
        .limit(limit)
    )
    docs = await cursor.to_list(length=limit)
    return [_to_dict(d) for d in docs]


async def _insert_message(
    conversation_id: str,
    direction: str,
    body: str,
    *,
    sent_by: str = "",
    status: str = "sent",
    wa_message_id: str = "",
) -> dict:
    now = utcnow()
    msg = {
        "_id": new_id(),
        "conversationId": conversation_id,
        "direction": direction,
        "body": body,
        "status": status,
        "waMessageId": wa_message_id,
        "sentBy": sent_by,
        "createdAt": now,
        "updatedAt": now,
        "deletedAt": None,
    }
    await db["whatsapp_messages"].insert_one(msg)

    update = {
        "lastMessageAt": now,
        "updatedAt": now,
    }
    if direction == "inbound":
        update["lastInboundAt"] = now
        update["$inc"] = {"unreadCount": 1}
    else:
        update["lastOutboundAt"] = now
    set_doc = {k: v for k, v in update.items() if k != "$inc"}
    inc_doc = update.get("$inc")
    mongo_update: dict = {"$set": set_doc}
    if inc_doc:
        mongo_update["$inc"] = inc_doc
    await db["whatsapp_conversations"].update_one(
        {"_id": conversation_id}, mongo_update
    )
    return _to_dict(msg)


async def mark_read(conversation_id: str) -> Optional[dict]:
    doc = await db["whatsapp_conversations"].find_one_and_update(
        {"_id": conversation_id, "deletedAt": None},
        {"$set": {"unreadCount": 0, "updatedAt": utcnow()}},
        return_document=True,
    )
    return _to_dict(doc) if doc else None


async def close_conversation(conversation_id: str) -> Optional[dict]:
    doc = await db["whatsapp_conversations"].find_one_and_update(
        {"_id": conversation_id, "deletedAt": None},
        {"$set": {"status": "closed", "updatedAt": utcnow()}},
        return_document=True,
    )
    return _to_dict(doc) if doc else None


async def reopen_conversation(conversation_id: str) -> Optional[dict]:
    doc = await db["whatsapp_conversations"].find_one_and_update(
        {"_id": conversation_id, "deletedAt": None},
        {"$set": {"status": "open", "updatedAt": utcnow()}},
        return_document=True,
    )
    return _to_dict(doc) if doc else None


async def send_message(
    conversation_id: str,
    body: str,
    sent_by: str,
) -> Optional[dict]:
    conv = await get_conversation(conversation_id)
    if not conv:
        return None

    wa_id = ""
    status = "sent"
    if settings.WHATSAPP_ACCESS_TOKEN and settings.WHATSAPP_PHONE_NUMBER_ID:
        wa_id, status = await _send_meta(conv.get("phone", ""), body)
    else:
        logger.info(
            "[WHATSAPP MOCK] to=%s body=%s", conv.get("phone"), body[:80]
        )

    msg = await _insert_message(
        conversation_id,
        "outbound",
        body,
        sent_by=sent_by,
        status=status,
        wa_message_id=wa_id,
    )

    if conv.get("leadId"):
        try:
            await append_activity(
                conv["leadId"],
                {
                    "type": "whatsapp_outbound",
                    "description": f"WhatsApp inviato: {body[:120]}",
                    "userId": sent_by,
                },
            )
        except Exception as exc:  # non-blocking for send path
            logger.warning("activity log failed: %s", exc)
    return msg


async def receive_inbound(phone: str, body: str, wa_message_id: str = "") -> dict:
    """Webhook path: create conversation if needed, store inbound message."""
    p = normalize_phone(phone)
    conv = await find_by_phone(p)
    if not conv:
        conv = await create_conversation({"phone": p}, created_by="system")

    msg = await _insert_message(
        conv["id"],
        "inbound",
        body,
        status="received",
        wa_message_id=wa_message_id,
    )

    if conv.get("leadId"):
        try:
            await append_activity(
                conv["leadId"],
                {
                    "type": "whatsapp_inbound",
                    "description": f"WhatsApp ricevuto: {body[:120]}",
                    "userId": "system",
                },
            )
        except Exception as exc:
            logger.warning("activity log failed: %s", exc)
    return {"conversation": conv, "message": msg}


async def _send_meta(to: str, body: str) -> tuple[str, str]:
    """Send via Meta WhatsApp Cloud API. Returns (wa_message_id, status)."""
    url = (
        f"https://graph.facebook.com/{settings.WHATSAPP_API_VERSION}/"
        f"{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"
    )
    payload = {
        "messaging_product": "whatsapp",
        "to": normalize_phone(to).lstrip("+"),
        "type": "text",
        "text": {"body": body},
    }
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                url,
                headers={"Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}"},
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            messages = data.get("messages") or []
            return (messages[0].get("id", "") if messages else "", "sent")
    except Exception as exc:
        logger.error("WhatsApp send failed: %s", exc)
        return ("", "failed")


async def inbox_stats() -> dict:
    total = await db["whatsapp_conversations"].count_documents({"deletedAt": None})
    open_count = await db["whatsapp_conversations"].count_documents(
        {"deletedAt": None, "status": "open"}
    )
    unread = await db["whatsapp_conversations"].aggregate(
        [
            {"$match": {"deletedAt": None}},
            {"$group": {"_id": None, "sum": {"$sum": "$unreadCount"}}},
        ]
    ).to_list(length=1)
    return {
        "totalConversations": total,
        "openConversations": open_count,
        "unreadMessages": unread[0]["sum"] if unread else 0,
    }
