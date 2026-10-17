"""
Agent governance — HITL approvals, business guardrails, rate limits (Fase C).

Pattern Agno: Human-in-the-Loop + Guardrails, senza framework.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from app.services.db_service import db, new_id, utcnow

logger = logging.getLogger(__name__)

# Tool che richiedono approvazione umana prima dell'esecuzione
APPROVAL_TOOLS = {
    "send_email",
    "send_whatsapp",
    "delete_lead",
    "delete_deal",
    "delete_task",
    "mark_invoice",  # sent/paid/cancelled
}

# Limiti business (configurabili via env in futuro)
MAX_EMAILS_PER_DAY = 50
MAX_WHATSAPP_PER_DAY = 30
DEAL_VALUE_REQUIRES_APPROVAL = 50_000


def _day_start() -> datetime:
    now = datetime.now(timezone.utc)
    return now.replace(hour=0, minute=0, second=0, microsecond=0)


async def count_actions_today(user_id: str, action: str) -> int:
    return await db["agent_actions"].count_documents({
        "userId": user_id,
        "action": action,
        "createdAt": {"$gte": _day_start()},
        "deletedAt": None,
    })


async def record_action(user_id: str, action: str, meta: Optional[dict] = None) -> None:
    try:
        await db["agent_actions"].insert_one({
            "_id": new_id(),
            "userId": user_id,
            "action": action,
            "meta": meta or {},
            "createdAt": utcnow(),
            "deletedAt": None,
        })
    except Exception:
        logger.exception("record_action failed")


async def check_business_guardrails(tool: str, args: dict, user_id: str, user_role: str) -> tuple[bool, str]:
    """
    Return (allowed, reason).
    Se non allowed e reason contiene 'approval', il tool deve passare da HITL.
    """
    # Quota email
    if tool == "send_email":
        n = await count_actions_today(user_id, "send_email")
        if n >= MAX_EMAILS_PER_DAY:
            return False, f"Quota email giornaliera raggiunta ({MAX_EMAILS_PER_DAY})"
        to = (args.get("toEmail") or "").strip().lower()
        if not to or "@" not in to:
            return False, "toEmail non valida"

    if tool == "send_whatsapp":
        n = await count_actions_today(user_id, "send_whatsapp")
        if n >= MAX_WHATSAPP_PER_DAY:
            return False, f"Quota WhatsApp giornaliera raggiunta ({MAX_WHATSAPP_PER_DAY})"

    # Deal di grande valore → approval
    if tool in ("create_deal", "update_deal"):
        try:
            value = float(args.get("value") or 0)
        except (TypeError, ValueError):
            value = 0
        if value >= DEAL_VALUE_REQUIRES_APPROVAL:
            return False, (
                f"Deal da €{value:,.0f} ≥ soglia €{DEAL_VALUE_REQUIRES_APPROVAL:,.0f}: "
                "richiede approvazione (approval=true)"
            )

    # Non-admin non può cancellare lead con conferma leggera
    if tool in ("delete_lead", "delete_deal") and user_role not in ("admin", "sales"):
        return False, "Permesso insufficiente per eliminare"

    return True, ""


# ── HITL pending approvals ───────────────────────────────────────────────────

async def create_approval(
    user_id: str,
    tool: str,
    args: dict,
    reason: str,
    *,
    message: Optional[str] = None,
) -> dict:
    now = utcnow()
    doc = {
        "_id": new_id(),
        "userId": user_id,
        "tool": tool,
        "args": args,
        "reason": reason,
        "message": message,
        "status": "pending",  # pending | approved | rejected
        "createdAt": now,
        "updatedAt": now,
        "deletedAt": None,
    }
    try:
        await db["agent_approvals"].insert_one(doc)
    except Exception:
        logger.exception("create_approval persist failed")
    return {
        "id": doc["_id"],
        "tool": tool,
        "reason": reason,
        "status": "pending",
    }


async def resolve_approval(approval_id: str, user_id: str, approve: bool) -> Optional[dict]:
    status = "approved" if approve else "rejected"
    doc = await db["agent_approvals"].find_one_and_update(
        {"_id": approval_id, "status": "pending", "deletedAt": None},
        {"$set": {"status": status, "updatedAt": utcnow(), "resolvedBy": user_id}},
    )
    return doc


async def list_pending_approvals(user_id: Optional[str] = None) -> list[dict]:
    query = {"status": "pending", "deletedAt": None}
    if user_id:
        query["userId"] = user_id
    cursor = db["agent_approvals"].find(query).sort("createdAt", -1).limit(50)
    out = []
    async for d in cursor:
        out.append({
            "id": d["_id"],
            "tool": d.get("tool"),
            "reason": d.get("reason"),
            "args": {k: v for k, v in (d.get("args") or {}).items() if k != "body"},
            "createdAt": str(d.get("createdAt")),
            "userId": d.get("userId"),
        })
    return out


def requires_approval(tool: str, args: dict, guard_reason: str) -> bool:
    """True if this tool invocation must be paused for human approval."""
    if tool not in APPROVAL_TOOLS:
        # deal di grande valore con reason approval
        return "approvazione" in (guard_reason or "").lower() or "approval" in (guard_reason or "").lower()
    # confirm=true esplicito = l'utente ha già approvato in chat
    if args.get("confirm") is True:
        return False
    return True
