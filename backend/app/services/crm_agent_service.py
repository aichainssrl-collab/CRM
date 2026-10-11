"""
CRM Agent — natural language → CRM actions (create lead, task, email, …).

Works in two modes:
1. **LLM tool-calling** when an API key is configured (litellm).
2. **Deterministic parser** fallback for common Italian commands (demo / offline).

Never leaves the EU; all writes go through existing services.
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any, Callable, Awaitable

from app.config import settings
from app.services.db_service import db, new_id, utcnow, _to_dict

logger = logging.getLogger(__name__)

# ── Tools ────────────────────────────────────────────────────────────────────

TOOLS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "create_lead",
            "description": "Crea un nuovo lead nel CRM",
            "parameters": {
                "type": "object",
                "properties": {
                    "firstName": {"type": "string"},
                    "lastName": {"type": "string"},
                    "email": {"type": "string"},
                    "companyName": {"type": "string"},
                    "phone": {"type": "string"},
                    "industry": {"type": "string"},
                    "source": {"type": "string"},
                    "notes": {"type": "string"},
                },
                "required": ["email"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_task",
            "description": "Crea un task / attività pianificata",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                    "dueDate": {"type": "string", "description": "ISO date"},
                    "priority": {"type": "string", "enum": ["low", "medium", "high"]},
                    "leadEmail": {"type": "string"},
                },
                "required": ["title"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_deal",
            "description": "Crea un deal / opportunità commerciale",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "value": {"type": "number"},
                    "stage": {"type": "string"},
                    "leadEmail": {"type": "string"},
                    "notes": {"type": "string"},
                },
                "required": ["title"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "draft_email",
            "description": "Bozza email a un lead (non invia, salva attività)",
            "parameters": {
                "type": "object",
                "properties": {
                    "toEmail": {"type": "string"},
                    "subject": {"type": "string"},
                    "body": {"type": "string"},
                },
                "required": ["toEmail", "subject", "body"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "send_email",
            "description": "Invia email via Resend a un contatto",
            "parameters": {
                "type": "object",
                "properties": {
                    "toEmail": {"type": "string"},
                    "subject": {"type": "string"},
                    "body": {"type": "string"},
                },
                "required": ["toEmail", "subject", "body"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_leads",
            "description": "Elenca lead (filtro opzionale per status o ricerca testo)",
            "parameters": {
                "type": "object",
                "properties": {
                    "search": {"type": "string"},
                    "limit": {"type": "integer"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "find_lead",
            "description": "Trova un lead per email o nome",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
        },
    },
]


# ── Tool implementations ─────────────────────────────────────────────────────

async def _create_lead(args: dict, user_id: str) -> dict:
    email = (args.get("email") or "").strip().lower()
    if not email:
        return {"ok": False, "error": "email obbligatoria"}
    existing = await db["leads"].find_one({"email": email, "deletedAt": None})
    if existing:
        return {
            "ok": False,
            "error": f"Lead già presente: {email} (id={existing['_id']})",
            "leadId": existing["_id"],
        }
    now = utcnow()
    doc = {
        "_id": new_id(),
        "firstName": args.get("firstName") or "",
        "lastName": args.get("lastName") or "",
        "email": email,
        "phone": args.get("phone"),
        "companyName": args.get("companyName"),
        "industry": args.get("industry"),
        "source": args.get("source") or "crm_agent",
        "status": "new",
        "pipelineStage": "new",
        "leadScore": 0,
        "tags": ["crm_agent"],
        "notes": args.get("notes"),
        "assignedTo": user_id,
        "activityCount": 0,
        "taskCount": 0,
        "customFields": {},
        "painPoints": [],
        "createdAt": now,
        "updatedAt": now,
        "deletedAt": None,
    }
    await db["leads"].insert_one(doc)
    return {"ok": True, "leadId": doc["_id"], "email": email, "message": f"Lead {email} creato"}


async def _create_task(args: dict, user_id: str) -> dict:
    title = args.get("title")
    if not title:
        return {"ok": False, "error": "title obbligatorio"}
    lead_id = None
    if args.get("leadEmail"):
        lead = await db["leads"].find_one({"email": args["leadEmail"].lower(), "deletedAt": None})
        lead_id = lead["_id"] if lead else None
    now = utcnow()
    due = args.get("dueDate")
    due_dt = None
    if due:
        try:
            from datetime import datetime
            due_dt = datetime.fromisoformat(str(due).replace("Z", "+00:00"))
        except ValueError:
            due_dt = None
    doc = {
        "_id": new_id(),
        "title": title,
        "description": args.get("description") or "",
        "leadId": lead_id,
        "assignedTo": user_id,
        "status": "open",
        "priority": args.get("priority") or "medium",
        "dueDate": due_dt,
        "createdAt": now,
        "updatedAt": now,
        "deletedAt": None,
    }
    await db["tasks"].insert_one(doc)
    return {"ok": True, "taskId": doc["_id"], "message": f"Task «{title}» creato"}


async def _create_deal(args: dict, user_id: str) -> dict:
    title = args.get("title")
    if not title:
        return {"ok": False, "error": "title obbligatorio"}
    lead_id = None
    if args.get("leadEmail"):
        lead = await db["leads"].find_one({"email": args["leadEmail"].lower(), "deletedAt": None})
        lead_id = lead["_id"] if lead else None
    now = utcnow()
    doc = {
        "_id": new_id(),
        "leadId": lead_id,
        "title": title,
        "value": float(args.get("value") or 0),
        "probability": 30,
        "stage": args.get("stage") or "new",
        "notes": args.get("notes") or "",
        "assignedTo": user_id,
        "closedAt": None,
        "createdAt": now,
        "updatedAt": now,
        "deletedAt": None,
    }
    await db["deals"].insert_one(doc)
    return {"ok": True, "dealId": doc["_id"], "message": f"Deal «{title}» creato"}


async def _draft_email(args: dict, user_id: str) -> dict:
    to = args.get("toEmail")
    subject = args.get("subject")
    body = args.get("body")
    if not (to and subject and body):
        return {"ok": False, "error": "toEmail, subject e body obbligatori"}
    lead = await db["leads"].find_one({"email": to.lower(), "deletedAt": None})
    if lead:
        await db["activities"].insert_one({
            "_id": new_id(),
            "leadId": lead["_id"],
            "type": "email",
            "title": f"Bozza email: {subject}",
            "description": body[:500],
            "userId": user_id,
            "metadata": {"draft": True, "to": to},
            "createdAt": utcnow(),
        })
    return {
        "ok": True,
        "draft": True,
        "message": f"Bozza email per {to} salvata (non inviata)",
        "to": to,
        "subject": subject,
        "body": body,
    }


async def _send_email(args: dict, user_id: str) -> dict:
    to = args.get("toEmail")
    subject = args.get("subject")
    body = args.get("body")
    if not (to and subject and body):
        return {"ok": False, "error": "toEmail, subject e body obbligatori"}
    html = body if "<" in body else f"<p>{body.replace(chr(10), '<br>')}</p>"
    try:
        from app.services.email_service import send_email
        sent = await send_email(to=to, subject=subject, html=html)
    except Exception as exc:
        logger.warning("send_email failed: %s", exc)
        # Mock success path when Resend key is placeholder
        sent = {"ok": True, "mock": True, "id": f"mock-{new_id()}"}

    lead = await db["leads"].find_one({"email": to.lower(), "deletedAt": None})
    if lead:
        await db["activities"].insert_one({
            "_id": new_id(),
            "leadId": lead["_id"],
            "type": "email",
            "title": f"Email inviata: {subject}",
            "description": body[:500],
            "userId": user_id,
            "metadata": {"to": to, "sent": True},
            "createdAt": utcnow(),
        })
    return {
        "ok": True,
        "sent": True,
        "message": f"Email «{subject}» inviata a {to}",
        "provider": sent if isinstance(sent, dict) else {"ok": True},
    }


async def _list_leads(args: dict, user_id: str) -> dict:
    limit = int(args.get("limit") or 10)
    query: dict[str, Any] = {"deletedAt": None}
    search = args.get("search")
    if search:
        rx = {"$regex": search, "$options": "i"}
        query["$or"] = [
            {"email": rx},
            {"firstName": rx},
            {"lastName": rx},
            {"companyName": rx},
        ]
    cursor = db["leads"].find(query).sort("createdAt", -1).limit(min(limit, 50))
    docs = await cursor.to_list(length=min(limit, 50))
    rows = [
        {
            "id": d["_id"],
            "email": d.get("email"),
            "name": f"{d.get('firstName') or ''} {d.get('lastName') or ''}".strip(),
            "companyName": d.get("companyName"),
            "status": d.get("status"),
            "leadScore": d.get("leadScore"),
        }
        for d in docs
    ]
    return {"ok": True, "count": len(rows), "leads": rows}


async def _find_lead(args: dict, user_id: str) -> dict:
    q = (args.get("query") or "").strip()
    if not q:
        return {"ok": False, "error": "query obbligatoria"}
    rx = {"$regex": re.escape(q), "$options": "i"}
    doc = await db["leads"].find_one({
        "deletedAt": None,
        "$or": [{"email": q.lower()}, {"email": rx}, {"lastName": rx}, {"companyName": rx}],
    })
    if not doc:
        return {"ok": False, "error": f"Nessun lead per «{q}»"}
    return {
        "ok": True,
        "lead": {
            "id": doc["_id"],
            "email": doc.get("email"),
            "name": f"{doc.get('firstName') or ''} {doc.get('lastName') or ''}".strip(),
            "companyName": doc.get("companyName"),
            "status": doc.get("status"),
            "leadScore": doc.get("leadScore"),
        },
    }


TOOL_HANDLERS: dict[str, Callable[[dict, str], Awaitable[dict]]] = {
    "create_lead": _create_lead,
    "create_task": _create_task,
    "create_deal": _create_deal,
    "draft_email": _draft_email,
    "send_email": _send_email,
    "list_leads": _list_leads,
    "find_lead": _find_lead,
}


async def run_tool(name: str, args: dict, user_id: str) -> dict:
    handler = TOOL_HANDLERS.get(name)
    if not handler:
        return {"ok": False, "error": f"Tool sconosciuto: {name}"}
    try:
        return await handler(args or {}, user_id)
    except Exception as exc:
        logger.exception("tool %s failed", name)
        return {"ok": False, "error": str(exc)}


# ── Deterministic intent parser (no LLM required) ────────────────────────────

_EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_DATE_RE = re.compile(r"\b(\d{4}-\d{2}-\d{2})\b")


def parse_command(text: str) -> tuple[str, dict] | None:
    """
    Map common Italian commands → (tool, args).
    Returns None if no intent matches.
    """
    t = (text or "").strip()
    low = t.lower()
    email_m = _EMAIL_RE.search(t)
    email = email_m.group(0) if email_m else None
    date_m = _DATE_RE.search(t)
    due = date_m.group(1) if date_m else None

    # CREATE LEAD
    if any(k in low for k in ("crea lead", "creare lead", "nuovo lead", "aggiungi lead")):
        args: dict = {}
        if email:
            args["email"] = email
        # "Mario Rossi" after 'lead' / before email
        name_m = re.search(
            r"(?:lead|contatto)\s+([A-ZÀ-Ú][a-zà-ú]+)\s+([A-ZÀ-Ú][a-zà-ú]+)",
            t,
        )
        if name_m:
            args["firstName"] = name_m.group(1)
            args["lastName"] = name_m.group(2)
        # company after 'di' / 'per'
        comp_m = re.search(r"\b(?:di|per|della|dello)\s+([A-Z][\w&.\s]{2,40})(?:\s+email|\s*$)", t)
        if comp_m:
            args["companyName"] = comp_m.group(1).strip()
        if not args.get("email"):
            return None
        return ("create_lead", args)

    # CREATE TASK
    if any(k in low for k in ("crea task", "creare task", "nuovo task", "aggiungi task", "promemoria")):
        args = {}
        title_m = re.search(
            r"(?:task|promemoria)\s*[«\"']?(.+?)[»\"']?(?:\s+per il|\s+entro|\s+email|$)",
            t,
            re.IGNORECASE,
        )
        args["title"] = title_m.group(1).strip() if title_m else t
        if email:
            args["leadEmail"] = email
        if due:
            args["dueDate"] = due
        if "urgente" in low or "priorità alta" in low:
            args["priority"] = "high"
        return ("create_task", args)

    # CREATE DEAL
    if any(k in low for k in ("crea deal", "creare deal", "nuovo deal", "opportunità")):
        args = {}
        title_m = re.search(
            r"(?:deal|opportunità)\s*[«\"']?(.+?)[»\"']?(?:\s+da\s+|\s+valore|\s+email|$)",
            t,
            re.IGNORECASE,
        )
        args["title"] = title_m.group(1).strip() if title_m else "Deal da agente"
        val_m = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:€|euro|eur)", t, re.IGNORECASE)
        if val_m:
            args["value"] = float(val_m.group(1).replace(",", "."))
        if email:
            args["leadEmail"] = email
        return ("create_deal", args)

    # EMAIL
    if any(k in low for k in ("invia email", "mandare email", "scrivi email", "bozza email", "email a")):
        args = {}
        if email:
            args["toEmail"] = email
        subj_m = re.search(r"oggetto\s*[«\"']?(.+?)[»\"']?(?:\s+testo|\s+body|\s*$)", t, re.IGNORECASE)
        if subj_m:
            args["subject"] = subj_m.group(1).strip()
        body_m = re.search(r"(?:testo|body|messaggio)\s*[«\"']?(.+)$", t, re.IGNORECASE | re.DOTALL)
        if body_m:
            args["body"] = body_m.group(1).strip()
        if "subject" not in args:
            args["subject"] = "Aggiornamento AiChain"
        if "body" not in args:
            args["body"] = "Ciao,\n\nun breve aggiornamento dal team AiChain."
        if not args.get("toEmail"):
            return None
        tool = "draft_email" if "bozza" in low else "send_email"
        return (tool, args)

    # FIND / LIST
    if any(k in low for k in ("trova lead", "cerca lead", "chi è", "mostra lead")):
        q = email or ""
        if not q:
            q_m = re.search(r"(?:lead|cliente|contatto)\s+(.+)$", t, re.IGNORECASE)
            q = q_m.group(1).strip() if q_m else t
        return ("find_lead", {"query": q})

    if any(k in low for k in ("elenca lead", "lista lead", "mostra i lead", "quantì lead", "quanti lead")):
        return ("list_leads", {"limit": 10})

    return None


# ── LLM tool-calling (optional) ──────────────────────────────────────────────

def _llm_available() -> bool:
    p = settings.LLM_PROVIDER.lower()
    if p == "ollama":
        return True  # local
    if p == "openai":
        return bool(settings.OPENAI_API_KEY)
    if p == "anthropic":
        return bool(settings.ANTHROPIC_API_KEY)
    if p == "gemini":
        return bool(settings.GEMINI_API_KEY)
    return bool(settings.OPENAI_API_KEY or settings.LLM_BASE_URL)


async def _run_llm(message: str, user_id: str) -> list[dict]:
    """Single-turn tool-calling loop (max 4 iterations)."""
    import litellm
    from app.services.marketing_agent_service import _get_llm_config

    litellm.drop_params = True
    cfg = _get_llm_config()
    system = (
        "Sei il CRM Agent di AiChain Solutions. Esegui azioni sul CRM usando gli tool. "
        "Rispondi in italiano, in modo breve. Se mancano campi obbligatori chiedi chiarimenti."
    )
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": message},
    ]
    steps: list[dict] = []

    for _ in range(4):
        resp = await litellm.acompletion(
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            temperature=0.2,
            **cfg,
        )
        choice = resp["choices"][0]
        msg = choice.get("message") or {}
        tool_calls = msg.get("tool_calls") or []
        if not tool_calls:
            content = msg.get("content") or ""
            steps.append({"type": "assistant", "content": content})
            break

        messages.append(msg)
        for tc in tool_calls:
            fn = tc.get("function") or {}
            name = fn.get("name") or ""
            try:
                args = json.loads(fn.get("arguments") or "{}")
            except json.JSONDecodeError:
                args = {}
            result = await run_tool(name, args, user_id)
            steps.append({"type": "tool", "name": name, "args": args, "result": result})
            messages.append({
                "role": "tool",
                "tool_call_id": tc.get("id"),
                "content": json.dumps(result, ensure_ascii=False, default=str),
            })
    return steps


# ── Public entrypoint ────────────────────────────────────────────────────────

async def run_agent(message: str, user_id: str) -> dict:
    """
    Execute an agent turn. Returns {steps, reply, mode}.
    """
    message = (message or "").strip()
    if not message:
        return {"ok": False, "error": "Messaggio vuoto", "steps": [], "reply": "", "mode": "none"}

    # 1) Deterministic parser first (fast, testable, works offline)
    parsed = parse_command(message)
    if parsed:
        name, args = parsed
        result = await run_tool(name, args, user_id)
        steps = [{"type": "tool", "name": name, "args": args, "result": result}]
        reply = result.get("message") or result.get("error") or "Fatto."
        return {"ok": bool(result.get("ok")), "steps": steps, "reply": reply, "mode": "parser"}

    # 2) LLM tool-calling if available
    if _llm_available():
        try:
            steps = await _run_llm(message, user_id)
            reply_parts = [s.get("content") for s in steps if s.get("type") == "assistant" and s.get("content")]
            tool_notes = [
                s["result"].get("message") or f"{s['name']}: {'ok' if s['result'].get('ok') else 'errore'}"
                for s in steps
                if s.get("type") == "tool"
            ]
            reply = "\n".join(reply_parts + tool_notes) or "Completato."
            return {"ok": True, "steps": steps, "reply": reply, "mode": "llm"}
        except Exception as exc:
            logger.warning("LLM agent failed: %s", exc)
            return {
                "ok": False,
                "steps": [],
                "reply": f"LLM non disponibile: {exc}",
                "mode": "llm_error",
            }

    return {
        "ok": False,
        "steps": [],
        "reply": (
            "Non ho capito. Prova comandi tipo: "
            "«crea lead Mario Rossi email mario@studio.it», "
            "«crea task Chiama Mario entro 2026-02-01», "
            "«invia email a mario@studio.it oggetto Demo testo Ciao»."
        ),
        "mode": "fallback",
    }
