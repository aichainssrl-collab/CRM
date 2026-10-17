"""
Agent user memory — fatti e preferenze persistenti (Fase C, pattern Agno Memory).
"""
from __future__ import annotations

import logging
import re
from typing import Any, Optional

from app.services.db_service import db, new_id, utcnow

logger = logging.getLogger(__name__)

MAX_FACTS = 50

# Pattern IT per estrarre preferenze («preferisco le email formali», «ricorda che il cliente Y…»)
_REMEMBER_RE = re.compile(
    r"(?:ricorda(?:mi)?|memorizza|nota che|tieni a mente)\s+(?:che\s+)?(.+)$",
    re.IGNORECASE,
)
_PREF_RE = re.compile(
    r"(?:preferisco|mi piace|non mi piace|evita|usa sempre)\s+(.+)$",
    re.IGNORECASE,
)


async def remember_fact(user_id: str, text: str, kind: str = "note") -> dict:
    fact = {
        "_id": new_id(),
        "userId": user_id,
        "kind": kind,  # note | preference | contact
        "text": (text or "").strip()[:500],
        "createdAt": utcnow(),
        "updatedAt": utcnow(),
        "deletedAt": None,
    }
    await db["agent_memory"].insert_one(fact)
    # trim
    cursor = db["agent_memory"].find({"userId": user_id, "deletedAt": None}).sort("createdAt", -1)
    docs = await cursor.to_list(length=MAX_FACTS + 10)
    if len(docs) > MAX_FACTS:
        for old in docs[MAX_FACTS:]:
            await db["agent_memory"].update_one({"_id": old["_id"]}, {"$set": {"deletedAt": utcnow()}})
    return {"id": fact["_id"], "text": fact["text"], "kind": kind}


async def list_facts(user_id: str, limit: int = 20) -> list[dict]:
    cursor = (
        db["agent_memory"]
        .find({"userId": user_id, "deletedAt": None})
        .sort("createdAt", -1)
        .limit(min(limit, MAX_FACTS))
    )
    return [
        {"id": d["_id"], "text": d.get("text"), "kind": d.get("kind"), "at": str(d.get("createdAt"))}
        async for d in cursor
    ]


def facts_prompt_block(facts: list[dict]) -> str:
    if not facts:
        return ""
    lines = ["Preferenze / fatti ricordati dell'utente:"]
    for f in facts[:10]:
        lines.append(f"- [{f.get('kind')}] {f.get('text')}")
    return "\n".join(lines)


def maybe_extract_memory_command(message: str) -> Optional[dict]:
    """
    Se il messaggio è una richiesta di memoria, ritorna {text, kind}.
    Altrimenti None.
    """
    m = _REMEMBER_RE.search(message or "")
    if m:
        return {"text": m.group(1).strip().strip("«»\"'."), "kind": "note"}
    m = _PREF_RE.search(message or "")
    if m and len(m.group(1).strip()) > 3:
        return {"text": m.group(1).strip().strip("«»\"'."), "kind": "preference"}
    return None
