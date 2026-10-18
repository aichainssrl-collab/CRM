"""
Agent sessions + run log — fondamenta per un agent multi-turno osservabile.

Collezioni:
- agent_sessions: history conversazioni per utente (ultimi N turni)
- agent_runs: traccia di ogni esecuzione (tool, latenza, errori)

Pattern ispirati ad Agno (sessions / tracing) senza framework esterno.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional

from app.services.db_service import db, new_id, utcnow

logger = logging.getLogger(__name__)

MAX_HISTORY_MESSAGES = 20  # turni mantenuti in sessione (user+assistant)
MAX_CONTEXT_CHARS = 4000


def _to_dict(doc: Optional[dict]) -> Optional[dict]:
    if not doc:
        return None
    d = dict(doc)
    d["id"] = d.pop("_id", None)
    return d


async def get_or_create_session(user_id: str, session_id: Optional[str] = None) -> dict:
    col = db["agent_sessions"]
    if session_id:
        doc = await col.find_one({"_id": session_id, "userId": user_id, "deletedAt": None})
        if doc:
            return _to_dict(doc)
    now = utcnow()
    sid = session_id or new_id()
    payload = {
        "_id": sid,
        "userId": user_id,
        "messages": [],
        "lastEntity": None,  # {type, id, name/email}
        "createdAt": now,
        "updatedAt": now,
        "deletedAt": None,
    }
    await col.insert_one(payload)
    return _to_dict(payload)


async def append_message(
    user_id: str,
    role: str,
    content: str,
    *,
    session_id: Optional[str] = None,
    meta: Optional[dict] = None,
) -> dict:
    """Append a turn to the session and trim history."""
    session = await get_or_create_session(user_id, session_id)
    msg = {
        "role": role,
        "content": (content or "")[:2000],
        "at": utcnow().isoformat(),
    }
    if meta:
        msg["meta"] = meta
    messages = list(session.get("messages") or [])
    messages.append(msg)
    if len(messages) > MAX_HISTORY_MESSAGES:
        messages = messages[-MAX_HISTORY_MESSAGES:]

    updates: dict[str, Any] = {"messages": messages, "updatedAt": utcnow()}
    if meta and meta.get("entity"):
        updates["lastEntity"] = meta["entity"]

    await db["agent_sessions"].update_one(
        {"_id": session["id"]},
        {"$set": updates},
    )
    session["messages"] = messages
    session["lastEntity"] = updates.get("lastEntity", session.get("lastEntity"))
    return session


def history_for_llm(session: dict, max_messages: int = 12) -> list[dict]:
    """Map session messages to OpenAI chat format (user/assistant only)."""
    out = []
    for m in (session.get("messages") or [])[-max_messages:]:
        if m.get("role") not in ("user", "assistant"):
            continue
        out.append({"role": m["role"], "content": m.get("content") or ""})
    return out


def build_system_context(user_id: str, session: dict, user_meta: Optional[dict] = None) -> str:
    """
    System prompt con contesto live (pattern Agno context providers).
    Le istruzioni goal/soul/regole arrivano da agent_config_service.
    """
    now = datetime.now(timezone.utc)
    last = session.get("lastEntity") or {}
    parts = [
        "Sei il CRM Agent di AiChain Solutions.",
        "Usa SEMPRE i tool per leggere o modificare dati CRM. Non inventare email, nomi o valori.",
        "Se la domanda riguarda lead, deal, task, email, fatture o report → chiama il tool appropriato.",
        "Se un tool fallisce o non trova dati, dillo chiaramente e suggerisci il comando giusto.",
        "Rispondi in italiano, in modo breve e operativo.",
        f"Data/ora (UTC): {now.strftime('%Y-%m-%d %H:%M')}.",
    ]
    if user_meta:
        name = user_meta.get("displayName") or user_meta.get("email") or user_id
        role = user_meta.get("role") or "sales"
        parts.append(f"Utente corrente: {name} (ruolo: {role}, id: {user_id}).")
    else:
        parts.append(f"Utente corrente id: {user_id}.")
    if last:
        label = last.get("name") or last.get("email") or last.get("id")
        parts.append(
            f"Ultima entità discussa: {last.get('type') or 'lead'} «{label}». "
            "Se l'utente dice «quel lead / lui / questa azienda» riferisciti a questa."
        )
    return "\n".join(parts)


async def build_system_context_async(user_id: str, session: dict, user_meta: Optional[dict] = None, message: str = "") -> str:
    """Come build_system_context + istruzioni agent_config + skill attive."""
    base = build_system_context(user_id, session, user_meta)
    try:
        from app.services.agent_config_service import build_agent_instructions

        instructions = await build_agent_instructions()
        base = f"{base}\n\n{instructions}"
    except Exception:
        logger.exception("agent_config instructions failed")
    try:
        from app.services.agent_skills_service import skills_prompt_block

        block = await skills_prompt_block(message)
        if block:
            base = f"{base}\n\n{block}"
    except Exception:
        logger.exception("agent_skills block failed")
    try:
        from app.services.agent_goals_service import goals_prompt_block

        gblock = await goals_prompt_block()
        if gblock:
            base = f"{base}\n\n{gblock}"
    except Exception:
        logger.exception("agent_goals block failed")
    return base


# ── Run log ──────────────────────────────────────────────────────────────────

async def log_run(
    *,
    user_id: str,
    message: str,
    mode: str,
    reply: str,
    steps: list[dict],
    ok: bool,
    duration_ms: int,
    session_id: Optional[str] = None,
    error: Optional[str] = None,
) -> str:
    run_id = new_id()
    tool_names = [s.get("name") for s in steps or [] if s.get("type") == "tool"]
    doc = {
        "_id": run_id,
        "userId": user_id,
        "sessionId": session_id,
        "message": (message or "")[:2000],
        "mode": mode,
        "ok": bool(ok),
        "replyPreview": (reply or "")[:500],
        "tools": tool_names,
        "stepCount": len(steps or []),
        "durationMs": duration_ms,
        "error": error,
        "createdAt": utcnow(),
        "deletedAt": None,
    }
    try:
        await db["agent_runs"].insert_one(doc)
    except Exception:
        logger.exception("log_run failed")
    return run_id


async def list_runs(user_id: Optional[str] = None, limit: int = 50) -> list[dict]:
    query: dict = {"deletedAt": None}
    if user_id:
        query["userId"] = user_id
    cursor = db["agent_runs"].find(query).sort("createdAt", -1).limit(min(limit, 200))
    return [_to_dict(d) for d in await cursor.to_list(length=limit)]


# ── Guardrail input ──────────────────────────────────────────────────────────

MAX_MESSAGE_LEN = 4000
_SUSPICIOUS = (
    "ignore previous", "disregard", "system prompt",
    "drop table", "rm -rf", "<script",
)


def validate_message(message: str) -> tuple[bool, str]:
    """Return (ok, error)."""
    m = (message or "").strip()
    if not m:
        return False, "Messaggio vuoto"
    if len(m) > MAX_MESSAGE_LEN:
        return False, f"Messaggio troppo lungo (max {MAX_MESSAGE_LEN} caratteri)"
    low = m.lower()
    for s in _SUSPICIOUS:
        if s in low:
            return False, "Messaggio non consentito"
    return True, ""


def extract_entity_from_steps(steps: list[dict]) -> Optional[dict]:
    """Derive last mentioned entity from tool results (for next-turn context)."""
    for s in reversed(steps or []):
        if s.get("type") != "tool":
            continue
        result = s.get("result") or {}
        lead = result.get("lead")
        if lead:
            return {
                "type": "lead",
                "id": lead.get("id"),
                "name": lead.get("name"),
                "email": lead.get("email"),
            }
        lead_id = result.get("leadId")
        if lead_id:
            return {
                "type": "lead",
                "id": lead_id,
                "email": (s.get("args") or {}).get("email"),
            }
    return None
