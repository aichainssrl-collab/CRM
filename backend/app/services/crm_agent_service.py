"""
CRM Agent — natural language → CRM actions (create lead, task, email, …).

Works in two modes:
1. **LLM tool-calling** when an API key is configured (litellm).
2. **Deterministic parser** fallback for common Italian commands (demo / offline).

Never leaves the EU; all writes go through existing services.
"""
from __future__ import annotations

import asyncio
import json
import logging
import re
from typing import Any, Callable, Awaitable

from app.config import settings
from app.services.db_service import db, new_id, utcnow, _to_dict
from app.services.activity_service import append_activity

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
            "name": "list_deals",
            "description": "Elenca deal / pipeline commerciale",
            "parameters": {
                "type": "object",
                "properties": {
                    "stage": {"type": "string"},
                    "search": {"type": "string"},
                    "limit": {"type": "integer"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_deal",
            "description": "Aggiorna un deal (stage, valore, chiusura prevista, note)",
            "parameters": {
                "type": "object",
                "properties": {
                    "dealId": {"type": "string"},
                    "title": {"type": "string", "description": "Cerca deal per titolo se manca dealId"},
                    "stage": {"type": "string", "enum": ["new", "qualified", "proposal", "negotiation", "won", "lost"]},
                    "value": {"type": "number"},
                    "expectedClose": {"type": "string", "description": "ISO date"},
                    "notes": {"type": "string"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_deadlines",
            "description": "Elenca scadenze imminenti (task con dueDate e deal con expectedClose)",
            "parameters": {
                "type": "object",
                "properties": {
                    "days": {"type": "integer", "description": "Finestra in giorni (default 7)"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "reschedule_task",
            "description": "Sposta la scadenza di un task",
            "parameters": {
                "type": "object",
                "properties": {
                    "taskId": {"type": "string"},
                    "title": {"type": "string", "description": "Cerca task per titolo se manca taskId"},
                    "dueDate": {"type": "string", "description": "Nuova data ISO"},
                },
                "required": ["dueDate"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "set_reminder",
            "description": "Crea un promemoria con notifica in-app (task + notification)",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "dueDate": {"type": "string", "description": "ISO date/datetime"},
                    "note": {"type": "string"},
                    "leadEmail": {"type": "string"},
                    "priority": {"type": "string", "enum": ["low", "medium", "high"]},
                },
                "required": ["title", "dueDate"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "notify",
            "description": "Crea una notifica in-app per l'utente corrente",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "body": {"type": "string"},
                    "kind": {"type": "string", "enum": ["info", "warning", "success", "error"]},
                    "link": {"type": "string"},
                },
                "required": ["title"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_notifications",
            "description": "Elenca notifiche in-app (opzionale solo non lette)",
            "parameters": {
                "type": "object",
                "properties": {
                    "unreadOnly": {"type": "boolean"},
                    "limit": {"type": "integer"},
                },
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
            "description": "Trova un lead per email o nome (restituisce tutti i campi, incluso industry/settore)",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_lead",
            "description": "Aggiorna i campi di un lead esistente (settore/industry, azienda, telefono, note, stato, nome, cognome)",
            "parameters": {
                "type": "object",
                "properties": {
                    "email": {"type": "string", "description": "Email del lead da aggiornare"},
                    "fields": {
                        "type": "object",
                        "description": "Campi da aggiornare. Chiavi: industry, companyName, phone, notes, status, firstName, lastName, roleTitle",
                    },
                },
                "required": ["email", "fields"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "crm_summary",
            "description": "Riepilogo CRM: lead, deal, pipeline, ricavi e task aperti",
            "parameters": {
                "type": "object",
                "properties": {
                    "days": {
                        "type": "integer",
                        "description": "Finestra in giorni per i nuovi lead (default 30)",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "book_demo",
            "description": "Prenota una demo / appuntamento con un contatto",
            "parameters": {
                "type": "object",
                "properties": {
                    "firstName": {"type": "string"},
                    "lastName": {"type": "string"},
                    "email": {"type": "string"},
                    "companyName": {"type": "string"},
                    "preferredDate": {"type": "string", "description": "ISO date"},
                    "timeSlot": {"type": "string", "description": "es. 15:00"},
                    "notes": {"type": "string"},
                },
                "required": ["email", "preferredDate"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "generate_report",
            "description": "Genera un report CRM con sintesi narrativa (KPI + insight)",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "timeRange": {"type": "string", "enum": ["7d", "30d", "90d"]},
                },
            },
        },
    },
]

# Phase B — copertura moduli CRM (task, billing, content, comms, ops)
from app.services.agent_tools_phase_b import (  # noqa: E402
    PHASE_B_TOOL_DEFS,
    PHASE_B_HANDLERS,
    PHASE_D_TOOL_DEFS,
    PHASE_D_HANDLERS,
    PHASE_F_TOOL_DEFS,
    PHASE_F_HANDLERS,
)

TOOLS = TOOLS + PHASE_B_TOOL_DEFS + PHASE_D_TOOL_DEFS + PHASE_F_TOOL_DEFS


# ── Tool implementations ─────────────────────────────────────────────────────

async def _create_lead(args: dict, user_id: str) -> dict:
    email = (args.get("email") or "").strip().lower().rstrip(".")
    if not email:
        return {"ok": False, "error": "email obbligatoria"}

    existing = await db["leads"].find_one({
        "email": {"$regex": f"^{re.escape(email)}$", "$options": "i"},
        "deletedAt": None,
    })
    if existing:
        # Upsert: completa i campi mancanti invece di fallire
        updates = {}
        for key in ("firstName", "lastName", "phone", "companyName", "industry", "notes"):
            val = args.get(key)
            if val and not existing.get(key):
                updates[key] = val
        if updates:
            updates["updatedAt"] = utcnow()
            await db["leads"].update_one({"_id": existing["_id"]}, {"$set": updates})
            existing.update(updates)

        name = f"{existing.get('firstName') or ''} {existing.get('lastName') or ''}".strip() or email
        filled = ", ".join(sorted(k for k in updates if k != "updatedAt")) if updates else ""
        if filled:
            message = f"Lead già presente: {name} <{email}> — aggiornati i campi: {filled}"
        else:
            message = (
                f"Lead già presente: {name} <{email}> "
                f"(azienda: {existing.get('companyName') or '—'}, settore: {existing.get('industry') or '—'})"
            )
        return {
            "ok": True,
            "leadId": existing["_id"],
            "email": existing.get("email") or email,
            "existing": True,
            "updatedFields": sorted(k for k in updates if k != "updatedAt"),
            "message": message,
            "lead": {
                "id": existing["_id"],
                "email": existing.get("email"),
                "name": name,
                "companyName": existing.get("companyName"),
                "industry": existing.get("industry"),
                "phone": existing.get("phone"),
                "status": existing.get("status"),
            },
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
    return {
        "ok": True,
        "leadId": doc["_id"],
        "email": email,
        "existing": False,
        "message": f"Lead {email} creato",
        "lead": {
            "id": doc["_id"],
            "email": email,
            "name": f"{doc['firstName']} {doc['lastName']}".strip(),
            "companyName": doc.get("companyName"),
            "industry": doc.get("industry"),
        },
    }


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
    expected = None
    if args.get("expectedClose"):
        try:
            from datetime import datetime
            expected = datetime.fromisoformat(str(args["expectedClose"]).replace("Z", "+00:00"))
        except ValueError:
            expected = None
    doc = {
        "_id": new_id(),
        "leadId": lead_id,
        "title": title,
        "value": float(args.get("value") or 0),
        "probability": 30,
        "stage": args.get("stage") or "new",
        "expectedClose": expected,
        "notes": args.get("notes") or "",
        "assignedTo": user_id,
        "closedAt": None,
        "createdAt": now,
        "updatedAt": now,
        "deletedAt": None,
    }
    await db["deals"].insert_one(doc)
    detail = []
    if args.get("stage"):
        detail.append(str(args["stage"]))
    if args.get("value"):
        detail.append(f"€{float(args['value']):,.0f}")
    suffix = f" ({', '.join(detail)})" if detail else ""
    return {
        "ok": True,
        "dealId": doc["_id"],
        "message": f"Deal «{title}» creato{suffix}",
    }


def _parse_iso(value: str | None):
    if not value:
        return None
    try:
        from datetime import datetime
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


async def _list_deals(args: dict, user_id: str) -> dict:
    limit = min(int(args.get("limit") or 10), 50)
    query: dict[str, Any] = {"deletedAt": None}
    if args.get("stage"):
        query["stage"] = args["stage"]
    search = args.get("search")
    if search:
        query["title"] = {"$regex": re.escape(search), "$options": "i"}
    cursor = db["deals"].find(query).sort("updatedAt", -1).limit(limit)
    docs = await cursor.to_list(length=limit)
    rows = [
        {
            "id": d["_id"],
            "title": d.get("title"),
            "stage": d.get("stage"),
            "value": d.get("value"),
            "expectedClose": d["expectedClose"].isoformat() if d.get("expectedClose") else None,
            "leadId": d.get("leadId"),
        }
        for d in docs
    ]
    total_value = sum(float(r.get("value") or 0) for r in rows)
    return {
        "ok": True,
        "count": len(rows),
        "totalValue": total_value,
        "deals": rows,
        "message": f"{len(rows)} deal trovati (valore totale €{total_value:,.0f})",
    }


async def _update_deal(args: dict, user_id: str) -> dict:
    deal = None
    if args.get("dealId"):
        deal = await db["deals"].find_one({"_id": args["dealId"], "deletedAt": None})
    if not deal and args.get("title"):
        deal = await db["deals"].find_one({
            "deletedAt": None,
            "title": {"$regex": re.escape(args["title"]), "$options": "i"},
        })
    if not deal:
        return {"ok": False, "error": "Deal non trovato (specifica dealId o title)"}

    updates: dict[str, Any] = {"updatedAt": utcnow()}
    if args.get("stage"):
        updates["stage"] = args["stage"]
        if args["stage"] in ("won", "lost"):
            updates["closedAt"] = utcnow()
            updates["probability"] = 100 if args["stage"] == "won" else 0
    if args.get("value") is not None:
        updates["value"] = float(args["value"])
    expected = _parse_iso(args.get("expectedClose"))
    if expected:
        updates["expectedClose"] = expected
    if args.get("notes"):
        updates["notes"] = args["notes"]

    await db["deals"].update_one({"_id": deal["_id"]}, {"$set": updates})
    merged = {**deal, **updates}
    parts = []
    if updates.get("stage"):
        parts.append(f"stage={updates['stage']}")
    if updates.get("value") is not None:
        parts.append(f"€{updates['value']:,.0f}")
    if expected:
        parts.append(f"chiusura {expected.date()}")
    return {
        "ok": True,
        "dealId": deal["_id"],
        "title": deal.get("title"),
        "message": f"Deal «{deal.get('title')}» aggiornato ({', '.join(parts) or 'ok'})",
        "deal": {
            "id": deal["_id"],
            "title": merged.get("title"),
            "stage": merged.get("stage"),
            "value": merged.get("value"),
            "expectedClose": merged["expectedClose"].isoformat() if merged.get("expectedClose") else None,
        },
    }


async def _list_deadlines(args: dict, user_id: str) -> dict:
    from datetime import timedelta

    days = max(1, min(int(args.get("days") or 7), 90))
    now = utcnow()
    end = now + timedelta(days=days)

    task_cursor = db["tasks"].find({
        "deletedAt": None,
        "status": "open",
        "dueDate": {"$gte": now, "$lte": end},
    }).sort("dueDate", 1).limit(50)
    tasks = await task_cursor.to_list(length=50)

    deal_cursor = db["deals"].find({
        "deletedAt": None,
        "stage": {"$nin": ["won", "lost"]},
        "expectedClose": {"$gte": now, "$lte": end},
    }).sort("expectedClose", 1).limit(50)
    deals = await deal_cursor.to_list(length=50)

    items = []
    for t in tasks:
        items.append({
            "kind": "task",
            "id": t["_id"],
            "title": t.get("title"),
            "date": t["dueDate"].isoformat() if t.get("dueDate") else None,
            "priority": t.get("priority"),
            "status": t.get("status"),
        })
    for d in deals:
        items.append({
            "kind": "deal",
            "id": d["_id"],
            "title": d.get("title"),
            "date": d["expectedClose"].isoformat() if d.get("expectedClose") else None,
            "stage": d.get("stage"),
            "value": d.get("value"),
        })
    items.sort(key=lambda x: x.get("date") or "")

    notified = 0
    if args.get("notify"):
        from app.services.notification_service import create_notification

        for it in items[:5]:
            await create_notification(
                user_id,
                title=f"Scadenza {it.get('kind')}: {it.get('title')}",
                body=f"In scadenza il {str(it.get('date') or '')[:10]}",
                kind="warning",
                link="/crm/calendar" if it.get("kind") == "booking" else "/crm/tasks",
            )
            notified += 1

    return {
        "ok": True,
        "days": days,
        "count": len(items),
        "notified": notified,
        "items": items,
        "message": f"{len(items)} scadenze nei prossimi {days} giorni"
        + (f" · {notified} notifiche create" if notified else ""),
    }


async def _reschedule_task(args: dict, user_id: str) -> dict:
    due = _parse_iso(args.get("dueDate"))
    if not due:
        return {"ok": False, "error": "dueDate ISO obbligatoria (es. 2026-03-01)"}

    task = None
    if args.get("taskId"):
        task = await db["tasks"].find_one({"_id": args["taskId"], "deletedAt": None})
    if not task and args.get("title"):
        task = await db["tasks"].find_one({
            "deletedAt": None,
            "status": "open",
            "title": {"$regex": re.escape(args["title"]), "$options": "i"},
        })
    if not task:
        return {"ok": False, "error": "Task non trovato (specifica taskId o title)"}

    await db["tasks"].update_one(
        {"_id": task["_id"]},
        {"$set": {"dueDate": due, "updatedAt": utcnow()}},
    )
    return {
        "ok": True,
        "taskId": task["_id"],
        "message": f"Task «{task.get('title')}» spostato al {due.date()}",
    }


async def _set_reminder(args: dict, user_id: str) -> dict:
    """Task + notification in-app per una scadenza."""
    from app.services.notification_service import create_notification

    title = args.get("title")
    due = _parse_iso(args.get("dueDate"))
    if not title or not due:
        return {"ok": False, "error": "title e dueDate obbligatori"}

    lead_id = None
    if args.get("leadEmail"):
        lead = await db["leads"].find_one({"email": args["leadEmail"].lower(), "deletedAt": None})
        lead_id = lead["_id"] if lead else None

    now = utcnow()
    task = {
        "_id": new_id(),
        "title": title,
        "description": args.get("note") or "",
        "leadId": lead_id,
        "assignedTo": user_id,
        "status": "open",
        "priority": args.get("priority") or "medium",
        "dueDate": due,
        "createdAt": now,
        "updatedAt": now,
        "deletedAt": None,
    }
    await db["tasks"].insert_one(task)

    notif = await create_notification(
        user_id,
        title=f"Promemoria: {title}",
        body=(
            f"Scadenza il {due.date()}."
            + (f" {args.get('note')}" if args.get("note") else "")
        ),
        kind="warning" if args.get("priority") == "high" else "info",
        link=f"/crm/tasks",
    )
    return {
        "ok": True,
        "taskId": task["_id"],
        "notificationId": notif.get("id"),
        "dueDate": due.isoformat(),
        "message": f"Promemoria «{title}» creato per il {due.date()} (notifica in-app)",
    }


async def _notify(args: dict, user_id: str) -> dict:
    from app.services.notification_service import create_notification

    title = args.get("title")
    if not title:
        return {"ok": False, "error": "title obbligatorio"}
    notif = await create_notification(
        user_id,
        title=title,
        body=args.get("body") or "",
        kind=args.get("kind") or "info",
        link=args.get("link"),
    )
    return {
        "ok": True,
        "notificationId": notif.get("id"),
        "message": f"Notifica «{title}» creata",
    }


async def _list_notifications(args: dict, user_id: str) -> dict:
    from app.services.notification_service import list_notifications, get_unread_count

    limit = min(int(args.get("limit") or 10), 50)
    unread_only = bool(args.get("unreadOnly"))
    items = await list_notifications(user_id, unread_only=unread_only, limit=limit)
    unread = await get_unread_count(user_id)
    return {
        "ok": True,
        "unreadCount": unread,
        "count": len(items),
        "notifications": [
            {
                "id": n.get("id"),
                "title": n.get("title"),
                "body": n.get("body"),
                "kind": n.get("kind"),
                "readAt": n.get("readAt"),
                "createdAt": n.get("createdAt").isoformat() if n.get("createdAt") else None,
            }
            for n in items
        ],
        "message": f"{len(items)} notifiche ({unread} non lette)",
    }


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

    from app.services.email_service import send_email_ex

    try:
        sent = await send_email_ex(to=to, subject=subject, html=html)
    except Exception as exc:
        logger.warning("Resend send_email_ex failed: %s", exc)
        sent = {"ok": False, "id": None, "mock": False, "error": str(exc)}

    email_id = sent.get("id")
    mock = bool(sent.get("mock"))
    send_error = sent.get("error")

    lead = await db["leads"].find_one({"email": to.lower(), "deletedAt": None})
    if lead:
        await db["activities"].insert_one({
            "_id": new_id(),
            "leadId": lead["_id"],
            "type": "email",
            "title": f"Email {'inviata' if sent.get('ok') else 'fallita'}: {subject}",
            "description": body[:500],
            "userId": user_id,
            "metadata": {
                "to": to,
                "sent": bool(sent.get("ok")),
                "mock": mock,
                "emailId": email_id,
                "provider": "resend" if not mock else "mock",
                "error": send_error,
            },
            "createdAt": utcnow(),
        })

    if not sent.get("ok"):
        return {
            "ok": False,
            "sent": False,
            "error": send_error or "Invio fallito",
            "message": f"Invio a {to} non riuscito" + (f": {send_error}" if send_error else ""),
        }

    return {
        "ok": True,
        "sent": True,
        "mock": mock,
        "emailId": email_id,
        "to": to,
        "subject": subject,
        "from": sent.get("from") or settings.EMAIL_FROM,
        "provider": "resend" if not mock else "mock",
        "message": (
            f"Email «{subject}» inviata a {to}"
            + (f" (id {email_id})" if email_id and not mock else "")
            + (" [mock Resend]" if mock else "")
        ),
    }


async def _list_leads(args: dict, user_id: str) -> dict:
    limit = int(args.get("limit") or 10)
    query: dict[str, Any] = {"deletedAt": None}
    search = args.get("search")
    if search:
        rx = {"$regex": re.escape(search), "$options": "i"}
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


async def _help(args: dict, user_id: str) -> dict:
    from app.services.agent_config_service import get_agent_config
    from app.services.agent_skills_service import list_skills

    try:
        cfg = await get_agent_config()
    except Exception:
        cfg = {}
    try:
        skills = await list_skills(include_inactive=False)
    except Exception:
        skills = []

    name = cfg.get("agentName") or "CRM Agent"
    goal_lines = (cfg.get("goal") or "").strip().splitlines()
    goal_summary = goal_lines[0][:120] if goal_lines else ""

    skill_lines = [
        f"  • {s.get('title')} — {s.get('description') or ''}".rstrip(" —")
        for s in skills[:8]
    ]

    return {
        "ok": True,
        "message": (
            f"Sono **{name}**. {cfg.get('soul') or ''}\n\n"
            f"Goal: {goal_summary}\n\n"
            "Ecco cosa so fare:\n"
            "• «crea lead Mario Rossi email mario@studio.it»\n"
            "• «dammi il settore di mario@studio.it» / «mostra info sul lead …»\n"
            "• «imposta settore marketing sul lead mario@studio.it»\n"
            "• «inserisci media nel lead mario@studio.it»\n"
            "• «prenota demo con Mario Rossi email mario@studio.it il 2026-02-01 alle 15:00»\n"
            "• «riepilogo CRM»\n"
            "• «invia email a mario@studio.it oggetto Demo testo Ciao»\n"
            "• «mostra deal», «crea task …», «promemoria …»\n"
            "• «mostra i task», «mostra fatture», «mostra proposte», «pipeline»\n"
            "• «mostra prodotti», «export csv», «kpi», «mostra report»\n"
            "• «workflow inbound per …», «genera contenuto marketing per …»\n\n"
            + (
                "Skill attive:\n" + "\n".join(skill_lines) + "\n"
                if skill_lines
                else ""
            )
            + (
                "Regole:\n" + (cfg.get("rules") or "")[:500]
                if cfg.get("rules")
                else ""
            )
        ),
    }


async def _find_lead(args: dict, user_id: str) -> dict:
    q = (args.get("query") or "").strip().rstrip(".")
    if not q:
        return {"ok": False, "error": "query obbligatoria"}
    rx = {"$regex": re.escape(q), "$options": "i"}
    doc = await db["leads"].find_one({
        "deletedAt": None,
        "$or": [
            {"email": q.lower()},
            {"email": rx},
            {"firstName": rx},
            {"lastName": rx},
            {"companyName": rx},
            # «Mock Match» → firstName+lastName
            {"$expr": {"$regexMatch": {
                "input": {"$concat": [{"$ifNull": ["$firstName", ""]}, " ", {"$ifNull": ["$lastName", ""]}]},
                "regex": re.escape(q),
                "options": "i",
            }}},
        ],
    })
    if not doc:
        return {"ok": False, "error": f"Nessun lead per «{q}»"}
    industry = doc.get("industry") or "(non imposto)"
    name = f"{doc.get('firstName') or ''} {doc.get('lastName') or ''}".strip() or doc.get("email")
    return {
        "ok": True,
        "message": (
            f"Lead {name} <{doc.get('email')}>\n"
            f"• Email: {doc.get('email')}\n"
            f"• Settore: {industry}\n"
            f"• Azienda: {doc.get('companyName') or '—'}\n"
            f"• Telefono: {doc.get('phone') or '—'}\n"
            f"• Ruolo: {doc.get('roleTitle') or '—'}\n"
            f"• Stato: {doc.get('status') or '—'} · Score: {doc.get('leadScore', 0)}"
        ),
        "lead": {
            "id": doc["_id"],
            "email": doc.get("email"),
            "name": name,
            "companyName": doc.get("companyName"),
            "industry": doc.get("industry"),
            "phone": doc.get("phone"),
            "roleTitle": doc.get("roleTitle"),
            "status": doc.get("status"),
            "notes": doc.get("notes"),
            "leadScore": doc.get("leadScore"),
        },
    }


async def _update_lead(args: dict, user_id: str) -> dict:
    email = (args.get("email") or "").strip().lower().rstrip(".")
    fields = args.get("fields") or {}
    if not email:
        return {"ok": False, "error": "email obbligatoria"}
    if not fields:
        return {"ok": False, "error": "nessun campo da aggiornare"}

    doc = await db["leads"].find_one({"email": {"$regex": f"^{re.escape(email)}$", "$options": "i"}, "deletedAt": None})
    if not doc:
        return {"ok": False, "error": f"Lead non trovato: {email}"}

    allowed = {
        "industry", "companyName", "phone", "notes", "status",
        "firstName", "lastName", "roleTitle", "roleSeniority",
        "companySize", "source", "linkedinUrl",
    }
    updates = {k: v for k, v in fields.items() if k in allowed and v is not None}
    if not updates:
        return {"ok": False, "error": f"Nessun campo valido tra {sorted(fields.keys())}"}

    updates["updatedAt"] = utcnow()
    await db["leads"].update_one({"_id": doc["_id"]}, {"$set": updates})

    await append_activity(doc["_id"], {
        "type": "note",
        "title": f"Lead aggiornato via agent: {', '.join(updates.keys())}",
        "userId": user_id,
        "metadata": {"fields": {k: str(v) for k, v in updates.items() if k != "updatedAt"}},
    })

    return {
        "ok": True,
        "leadId": doc["_id"],
        "updated": sorted(k for k in updates if k != "updatedAt"),
        "message": f"Lead {email} aggiornato: {', '.join(sorted(k for k in updates if k != 'updatedAt'))}",
    }


async def _generate_report(args: dict, user_id: str) -> dict:
    from datetime import timedelta

    from app.services import analytics_service, report_service

    time_range = args.get("timeRange") or "30d"
    days_map = {"7d": 7, "30d": 30, "90d": 90}
    days = days_map.get(time_range, 30)
    since = utcnow() - timedelta(days=days)

    report_data = {
        "kpis": await analytics_service.get_kpi_summary(since=since),
        "funnel": await analytics_service.get_conversion_funnel(since),
    }
    narrative = await report_service.generate_narrative(report_data, time_range=time_range)
    report_data["narrative"] = narrative

    title = args.get("title") or f"Report CRM {time_range}"
    now = utcnow()
    doc = {
        "_id": new_id(),
        "title": title,
        "timeRange": time_range,
        "generatedBy": user_id,
        "generatedByName": "CRM Agent",
        "data": report_data,
        "createdAt": now,
        "updatedAt": now,
        "deletedAt": None,
    }
    await db["reports"].insert_one(doc)

    return {
        "ok": True,
        "reportId": doc["_id"],
        "title": title,
        "narrative": narrative,
        "message": (
            f"Report «{title}» generato.\n\n{narrative.get('narrative') or ''}"
            + (
                "\n\nAzioni: " + "; ".join(narrative.get("actions") or [])
                if narrative.get("actions")
                else ""
            )
        ),
    }


async def _crm_summary(args: dict, user_id: str) -> dict:
    from datetime import timedelta

    from app.services.analytics_service import get_kpi_summary

    days = max(1, min(int(args.get("days") or 30), 365))
    since = utcnow() - timedelta(days=days)
    kpi = await get_kpi_summary(since=since)

    open_tasks = await db["tasks"].count_documents({"deletedAt": None, "status": "open"})
    overdue_tasks = await db["tasks"].count_documents({
        "deletedAt": None,
        "status": "open",
        "dueDate": {"$lt": utcnow()},
    })

    status_rows = []
    async for row in db["leads"].aggregate([
        {"$match": {"deletedAt": None}},
        {"$group": {"_id": "$status", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
    ]):
        status_rows.append({"status": row["_id"] or "new", "count": row["count"]})

    stage_rows = []
    async for row in db["deals"].aggregate([
        {"$match": {"deletedAt": None}},
        {"$group": {"_id": "$stage", "count": {"$sum": 1}, "value": {"$sum": "$value"}}},
        {"$sort": {"count": -1}},
    ]):
        stage_rows.append({
            "stage": row["_id"] or "new",
            "count": row["count"],
            "value": float(row.get("value") or 0),
        })

    parts = [
        f"Lead totali: {kpi['totalLeads']} (nuovi ultimi {days}gg: {kpi['newLeads']})",
        f"Deal attivi: {kpi['activeDeals']} · vinti: {kpi['wonDeals']} · persi: {kpi['lostDeals']}",
        f"Pipeline: €{kpi['pipelineValue']:,.0f} · ricavi: €{kpi['revenue']:,.0f}",
        f"Tasso conversione: {kpi['conversionRate']}%",
        f"Task aperti: {open_tasks}" + (f" ({overdue_tasks} in ritardo)" if overdue_tasks else ""),
    ]
    if status_rows:
        top = ", ".join(f"{s['status']}={s['count']}" for s in status_rows[:4])
        parts.append(f"Lead per status: {top}")
    if stage_rows:
        top = ", ".join(f"{s['stage']}={s['count']}" for s in stage_rows[:5])
        parts.append(f"Deal per stage: {top}")

    return {
        "ok": True,
        "kpi": kpi,
        "openTasks": open_tasks,
        "overdueTasks": overdue_tasks,
        "leadStatus": status_rows,
        "dealStages": stage_rows,
        "message": "Situazione CRM:\n" + "\n".join(f"• {p}" for p in parts),
    }


async def _book_demo(args: dict, user_id: str) -> dict:
    email = (args.get("email") or "").strip().lower()
    preferred = _parse_iso(args.get("preferredDate"))
    if not email:
        return {"ok": False, "error": "email obbligatoria"}
    if not preferred:
        return {"ok": False, "error": "preferredDate obbligatoria (ISO date)"}

    first = args.get("firstName") or ""
    last = args.get("lastName") or ""
    if not first or not last:
        lead = await db["leads"].find_one({"email": email, "deletedAt": None})
        if lead:
            first = first or lead.get("firstName") or ""
            last = last or lead.get("lastName") or ""

    if not first:
        first = email.split("@")[0]
    if not last:
        last = "—"

    lead_id = None
    lead = await db["leads"].find_one({"email": email, "deletedAt": None})
    if lead:
        lead_id = lead["_id"]
    else:
        created = await _create_lead(
            {
                "email": email,
                "firstName": first,
                "lastName": last,
                "companyName": args.get("companyName"),
                "source": "crm_agent_booking",
                "notes": args.get("notes"),
            },
            user_id,
        )
        if not created.get("ok"):
            return created
        lead_id = created.get("leadId")

    now = utcnow()
    booking_id = new_id()
    doc = {
        "_id": booking_id,
        "leadId": lead_id,
        "slotId": None,
        "status": "confirmed",
        "firstName": first,
        "lastName": last,
        "email": email,
        "companyName": args.get("companyName"),
        "preferredDate": preferred,
        "timeSlot": args.get("timeSlot") or "10:00",
        "notes": args.get("notes") or "Demo prenotata da CRM Agent",
        "message": args.get("notes"),
        "createdBy": user_id,
        "createdAt": now,
        "updatedAt": now,
        "deletedAt": None,
    }
    await db["bookings"].insert_one(doc)

    if lead_id:
        await db["activities"].insert_one({
            "_id": new_id(),
            "leadId": lead_id,
            "type": "booking",
            "title": f"Demo prenotata — {doc['preferredDate'].date()} {doc['timeSlot']}",
            "description": doc.get("notes") or "",
            "userId": user_id,
            "metadata": {"bookingId": booking_id},
            "createdAt": now,
        })

    when = f"{doc['preferredDate'].date()} alle {doc['timeSlot']}"
    return {
        "ok": True,
        "bookingId": booking_id,
        "leadId": lead_id,
        "email": email,
        "preferredDate": doc["preferredDate"].isoformat(),
        "timeSlot": doc["timeSlot"],
        "message": f"Demo confermata per {first} {last} ({email}) — {when}",
        "booking": {
            "id": booking_id,
            "email": email,
            "firstName": first,
            "lastName": last,
            "preferredDate": doc["preferredDate"].isoformat(),
            "timeSlot": doc["timeSlot"],
            "status": "confirmed",
        },
    }


TOOL_HANDLERS: dict[str, Callable[[dict, str], Awaitable[dict]]] = {
    "create_lead": _create_lead,
    "create_task": _create_task,
    "create_deal": _create_deal,
    "list_deals": _list_deals,
    "update_deal": _update_deal,
    "list_deadlines": _list_deadlines,
    "reschedule_task": _reschedule_task,
    "set_reminder": _set_reminder,
    "notify": _notify,
    "list_notifications": _list_notifications,
    "draft_email": _draft_email,
    "send_email": _send_email,
    "list_leads": _list_leads,
    "find_lead": _find_lead,
    "update_lead": _update_lead,
    "help": _help,
    "crm_summary": _crm_summary,
    "book_demo": _book_demo,
    "generate_report": _generate_report,
    **PHASE_B_HANDLERS,
    **PHASE_D_HANDLERS,
    **PHASE_F_HANDLERS,
}


async def run_tool(name: str, args: dict, user_id: str, user_role: str = "sales") -> dict:
    handler = TOOL_HANDLERS.get(name)
    if not handler:
        return {"ok": False, "error": f"Tool sconosciuto: {name}"}
    args = args or {}

    from app.services import agent_governance as gov

    # Business guardrails + HITL
    allowed, reason = await gov.check_business_guardrails(name, args, user_id, user_role)
    if not allowed:
        if gov.requires_approval(name, args, reason):
            approval = await gov.create_approval(user_id, name, args, reason)
            return {
                "ok": False,
                "approvalRequired": True,
                "approvalId": approval["id"],
                "message": f"⚠️ Azione in attesa di approvazione: {reason}",
                "error": reason,
            }
        return {"ok": False, "error": reason}

    if gov.requires_approval(name, args, "") and args.get("confirm") is not True:
        approval = await gov.create_approval(
            user_id, name, args,
            f"«{name}» richiede conferma umana (invio esterno o eliminazione)",
        )
        return {
            "ok": False,
            "approvalRequired": True,
            "approvalId": approval["id"],
            "message": (
                f"⚠️ Azione sensibile «{name}» messa in coda per approvazione "
                f"(id {approval['id']}). Rispondi con confirm=true per procedere."
            ),
            "error": "approval_required",
        }

    try:
        result = await handler(args, user_id)
    except Exception as exc:
        logger.exception("tool %s failed", name)
        return {"ok": False, "error": str(exc)}

    # Post-hook: registra azioni mutanti (audit / rate-limit)
    if result.get("ok") and name in (
        "send_email", "send_whatsapp", "create_lead", "create_deal",
        "delete_lead", "delete_deal", "mark_invoice",
    ):
        await gov.record_action(user_id, name, {"args": {k: v for k, v in args.items() if k != "body"}})
    return result


# ── Deterministic intent parser (no LLM required) ────────────────────────────

_EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]*[a-zA-Z]")
_DATE_RE = re.compile(r"\b(\d{4}-\d{2}-\d{2})\b")
_PERSON_NAME_RE = re.compile(r"\b([A-ZÀ-Ú][a-zà-ú]{1,20}(?:\s+[A-ZÀ-Ú][a-zà-ú]{1,20}){1,2})\b")


def _extract_person_name(text: str) -> str | None:
    """Estrae un Nome Cognome in maiuscolo dal testo (es. «Danilo Zanni»)."""
    t = (text or "").strip()
    m = _PERSON_NAME_RE.search(t)
    return m.group(1).strip() if m else None


def parse_command(text: str) -> tuple[str, dict] | None:
    """
    Map common Italian commands → (tool, args).
    Returns None if no intent matches.
    """
    t = (text or "").strip()
    low = t.lower()
    email_m = _EMAIL_RE.search(t)
    email = email_m.group(0).rstrip(".") if email_m else None
    date_m = _DATE_RE.search(t)
    due = date_m.group(1) if date_m else None

    # HELP
    if low in ("aiuto", "help", "?", "cosa sai fare", "cosa puoi fare", "comandi"):
        return ("help", {})

    # PHASE B quick intents
    if any(k in low for k in ("mostra i task", "elenca task", "lista task", "i miei task", "task aperti")):
        args = {}
        if "miei" in low:
            args["assignedTo"] = "me"
        if "aperti" in low:
            args["status"] = "open"
        return ("list_tasks", args)
    if any(k in low for k in ("completa task", "task completato", "segna completato", "chiudi task")):
        m = re.search(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b", t)
        return ("complete_task", {"taskId": m.group(0) if m else ""})
    if any(k in low for k in ("mostra fatture", "elenca fatture", "lista fatture", "le fatture")):
        return ("list_invoices", {})
    if any(k in low for k in ("mostra proposte", "elenca proposte", "lista proposte", "le proposte")):
        return ("list_proposals", {})
    if any(k in low for k in ("statistiche fatture", "kpi fatture", "fatture totali")):
        return ("invoice_stats", {})
    if any(k in low for k in ("pipeline", "valore pipeline", "deal per stage")):
        return ("deal_pipeline", {})
    if any(k in low for k in ("mostra prodotti", "elenca prodotti", "lista prodotti", "listino")):
        return ("list_products", {})
    if any(k in low for k in ("mostra report", "elenca report", "lista report")):
        return ("list_reports", {})
    if (low.strip() in ("kpi", "kpi crm", "i kpi") or any(k in low for k in ("indicatori", "metriche crm"))) and "fattur" not in low:
        return ("crm_kpi", {"days": 30})
    if any(k in low for k in ("export csv", "esporta csv", "scarica csv")):
        kind = "deals" if "deal" in low else "contacts" if "contatt" in low else "leads"
        return ("export_csv", {"kind": kind})
    if any(k in low for k in ("mostra competitor", "monitoraggio competitor", "status competitor")):
        return ("competitor_status", {})
    if any(k in low for k in ("mostra calendario", "eventi del mese")):
        return ("list_calendar_events", {})

    # Phase D — workflow & team
    if any(k in low for k in ("workflow lead", "workflow inbound", "processa il lead", "gestisci inbound")):
        args = {}
        if email:
            args["leadEmail"] = email
        return ("workflow_inbound_lead", args)
    if any(k in low for k in ("genera contenuto marketing", "crea post", "crea email marketing", "contenuto marketing")):
        topic = t.split("per", 1)[-1].strip() if "per" in t.lower() else t
        return ("marketing_content", {"topic": topic, "contentType": "email"})
    if any(k in low for k in ("insight marketing", "suggerimenti marketing", "analisi marketing")):
        return ("marketing_insights", {})

    # Phase F — knowledge & follow-up
    if any(k in low for k in ("cerca nel knowledge", "cerca knowledge", "knowledge", "documenti su", "contenuti su", "template per")):
        q = t
        for prefix in ("cerca nel knowledge", "cerca knowledge", "knowledge", "documenti su", "contenuti su", "template per"):
            if prefix in low:
                idx = low.find(prefix)
                q = t[idx + len(prefix):].strip(" :«»\"'.")
                break
        return ("search_knowledge", {"query": q or t})
    if any(k in low for k in ("crea follow-up", "follow-up su", "follow up su", "promemoria follow")):
        args = {}
        if email:
            args["leadEmail"] = email
        return ("schedule_followup", args)

    # FIND LEAD / READ FIELD (es. «dammi il settore di x@y.it», «quale settore ha x@y.it»)
    if email and any(k in low for k in (
        "dammi il", "dammi l'", "dammi la", "quale è", "qual è", "qual'e", "qual e",
        "quale settore", "quale azienda", "quale telefono", "quale stato",
        "mostra il", "mostra l'", "mostra la", "dimmi il", "dimmi l'", "dimmi la",
        "che settore", "che azienda", "che telefono", "che stato",
        "settore di", "azienda di", "telefono di", "stato di",
        "info sul lead", "dettagli del lead", "scheda del lead", "mostra lead", "mostra il lead",
    )):
        return ("find_lead", {"query": email})

    # FIND LEAD BY NAME/COMPANY (es. «dammi email di Mock Match», «trova Rossi», «chi è Mario»)
    if any(k in low for k in (
        "dammi email", "dammi l'email", "dammi la mail", "dammi il contatto",
        "email di", "mail di", "e-mail di", "contatto di", "recapito di",
        "trova il lead", "trova lead", "trova il contatto", "cerca il lead", "cerca lead",
        "chi è", "chi e'", "chi è il lead", "scheda di", "info su",
        "in quale azienda", "in che azienda", "dove lavora", "dove lavorano",
        "azienda di", "azienda del", "azienda della", "ditta di", "società di", "societa di",
        "quali aziende", "che lavoro fa", "che lavoro fanno",
    )):
        query = email
        if not query:
            # nome prima della domanda: «Danilo Zanni in quale azienda lavora?»
            m = re.search(
                r"^([A-ZÀ-Ú][a-zà-ú]+(?:\s+[A-ZÀ-Ú][a-zà-ú]+){1,2})\s+(?:in quale|in che|dove|che|qual)",
                t.strip(),
            )
            if m:
                query = m.group(1).strip()
            else:
                # nome dopo «lavora» / verbo + nome proprio
                m = re.search(
                    r"\b(?:lavora|lavorano|indirizzo|recapito)\s+(?:di\s+|del\s+|della\s+)?([A-ZÀ-Ú][a-zà-ú]+(?:\s+[A-ZÀ-Ú][a-zà-ú]+){1,2})",
                    t.strip(),
                )
                if m:
                    query = m.group(1).strip()
                else:
                    # nome dopo «di» / «su» / «azienda»
                    m = re.search(
                        r"(?:di|su|del|della|per|azienda|email|mail|contatto|lead|trova|cerca|chi è|scheda|info su)\s+(?:di\s+|del\s+|della\s+|su\s+)?[«\"']?([A-ZÀ-Úa-zà-ú][\wÀ-ú&.' -]{1,60})[»\"']?\s*[?.!]*$",
                        t.strip(),
                        re.IGNORECASE,
                    )
                    if m:
                        query = m.group(1).strip().strip("«»\"'.")
                        query = re.sub(
                            r"^(?:il |lo |la |i |le )?(?:lead|contatto|cliente)\s+",
                            "", query, flags=re.IGNORECASE,
                        ).strip()
            if not query:
                query = _extract_person_name(t)
        if query and len(query) >= 2:
            return ("find_lead", {"query": query})

    # UPDATE LEAD FIELD (es. «imposta settore marketing sul lead x@y.it», «aggiorna settore …»)
    if email and any(k in low for k in (
        "imposta", "aggiorna", "inserisci", "metti", "cambia", "setta", "modifica", "manca",
    )):
        field_aliases = {
            "settore": "industry", "industry": "industry", "settori": "industry",
            "azienda": "companyName", "company": "companyName", "ragione sociale": "companyName",
            "telefono": "phone", "tel": "phone", "cellulare": "phone",
            "note": "notes", "nota": "notes",
            "stato": "status", "status": "status",
            "nome": "firstName", "cognome": "lastName",
            "ruolo": "roleTitle", "qualifica": "roleTitle",
        }
        fields = {}
        skip_vals = {
            "il", "l'", "la", "lo", "un", "una", "i", "le",
            "inserisci", "inserisce", "inserire", "inserimento",
            "imposta", "impostare", "impostazione",
            "aggiorna", "aggiornare", "aggiornamento",
            "metti", "mette", "mettere",
            "cambia", "cambiare", "setta", "settare",
            "modifica", "modificare", "manca", "mancano", "mancante",
            "nel", "nella", "sul", "sulla", "per", "del", "della", "dello",
            "al", "alla", "a", "in", "su", "di", "che", "e",
        }
        for alias, key in field_aliases.items():
            m = re.search(
                rf"(?:{re.escape(alias)})\s+(?:a\s+|in\s+|su\s+|per\s+|:\s*)?[«\"']?([^»\"'\n]+?)[»\"']?(?:\s+(?:sul|sulla|nel|nella|per|del|della|al|alla|a)\s+|$)",
                low,
                re.IGNORECASE,
            )
            if m:
                val = m.group(1).strip().strip("«»\"'.")
                # scarta match spurii tipo «settore inserisci media»
                tokens = [w for w in val.split() if w not in skip_vals]
                if tokens and "@" not in val:
                    fields[key] = " ".join(tokens)
                    break
        if not fields:
            # «inserisci media», «metti legal», «imposta finance» → industry
            m = re.search(
                r"(?:imposta|aggiorna|inserisci|metti|cambia|setta|modifica)\s+(?:il\s+|l'|la\s+|il\s+settore\s+|industry\s+)?[«\"']?([a-zà-ú][\wà-ú]{1,40})[»\"']?(?:\s+(?:sul|sulla|nel|nella|per|del|della|al|alla|a|email|il lead|la lead)|\s*$)",
                low,
                re.IGNORECASE,
            )
            if m:
                raw = m.group(1).strip().strip("«»\"'.")
                if raw and raw not in skip_vals and "@" not in raw:
                    fields["industry"] = raw
        if fields:
            return ("update_lead", {"email": email, "fields": fields})
        return None

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
    if any(k in low for k in ("crea task", "creare task", "nuovo task", "aggiungi task")):
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

    # REMINDER / NOTIFICATION
    if any(k in low for k in ("ricordami", "crea promemoria", "segna promemoria", "imposta promemoria", "promemoria per")):
        args = {}
        title_m = re.search(
            r"(?:ricordami|promemoria)\s+(?:di\s+|per\s+)?[«\"']?(.+?)[»\"']?(?:\s+entro|\s+il |\s+al |\s+per il|\s+email|$)",
            t,
            re.IGNORECASE,
        )
        args["title"] = (title_m.group(1).strip() if title_m else "Promemoria").strip("«»\"'")
        if due:
            args["dueDate"] = due
        else:
            args["dueDate"] = utcnow().isoformat()
        if email:
            args["leadEmail"] = email
        if "urgente" in low or "importante" in low:
            args["priority"] = "high"
        return ("set_reminder", args)

    if any(k in low for k in ("mostra notifiche", "notifiche non lette", "elenca notifiche", "cosa non ho letto")):
        return ("list_notifications", {"unreadOnly": "non lette" in low or "non letto" in low, "limit": 10})

    if any(k in low for k in ("notifica ", "invia notifica", "crea notifica")):
        args = {}
        title_m = re.search(
            r"notifica\s*[«\"']?(.+?)[»\"']?(?:\s+testo|\s+body|\s+descrizione|$)",
            t,
            re.IGNORECASE,
        )
        args["title"] = (title_m.group(1).strip() if title_m else "Notifica").strip("«»\"'")
        body_m = re.search(r"(?:testo|body|descrizione)\s*[«\"']?(.+)$", t, re.IGNORECASE)
        if body_m:
            args["body"] = body_m.group(1).strip()
        if "allarme" in low or "attenzione" in low or "warning" in low:
            args["kind"] = "warning"
        return ("notify", args)

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
        if not val_m:
            val_m = re.search(r"\bda\s+(\d+(?:[.,]\d+)?)\b", t, re.IGNORECASE)
        if val_m:
            args["value"] = float(val_m.group(1).replace(",", "."))
        if email:
            args["leadEmail"] = email
        return ("create_deal", args)

    # LIST / UPDATE DEALS
    if any(k in low for k in ("mostra deal", "elenca deal", "lista deal", "mostra i deal", "deal aperti")):
        args = {}
        for stage in ("new", "qualified", "proposal", "negotiation", "won", "lost"):
            if stage in low:
                args["stage"] = stage
                break
        # "deal in proposta" / "in trattativa"
        if "propost" in low:
            args["stage"] = "proposal"
        if "trattativa" in low or "negoziazione" in low:
            args["stage"] = "negotiation"
        return ("list_deals", args)

    if any(k in low for k in ("sposta deal", "aggiorna deal", "deal in ", "segna deal", "chiudi deal", "imposta deal")):
        args = {}
        id_m = re.search(r"\bdeal[ _]?([0-9a-f-]{8,})\b", low)
        if id_m:
            args["dealId"] = id_m.group(1)
        else:
            title_m = re.search(
                r"deal\s+[«\"']?(.+?)[»\"']?\s+(?:in|a|come|stage|valore|del|da)\b",
                t,
                re.IGNORECASE,
            )
            if title_m:
                args["title"] = title_m.group(1).strip()
        for stage, keys in {
            "won": ("vinto", "won"),
            "lost": ("perso", "lost"),
            "proposal": ("proposta", "proposal"),
            "negotiation": ("trattativa", "negoziazione", "negotiation"),
            "qualified": ("qualificato", "qualified"),
            "new": ("nuovo", "new"),
        }.items():
            if any(k in low for k in keys):
                args["stage"] = stage
                break
        val_m = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:€|euro|eur)", t, re.IGNORECASE)
        if val_m:
            args["value"] = float(val_m.group(1).replace(",", "."))
        if due:
            args["expectedClose"] = due
        if args:
            return ("update_deal", args)

    # DEADLINES / SCADENZE
    if any(k in low for k in ("scadenz", "cosa scade", "prossime scadenze", "impegni in scadenza")):
        args = {}
        n_m = re.search(r"(\d+)\s*giorn", low)
        if n_m:
            args["days"] = int(n_m.group(1))
        elif "settimana" in low:
            args["days"] = 7
        elif "mese" in low:
            args["days"] = 30
        return ("list_deadlines", args)

    # RESCHEDULE TASK
    if any(k in low for k in ("proroga task", "sposta task", "rimanda task", "cambia scadenza", "sposta scadenza")):
        if not due:
            return None
        args = {"dueDate": due}
        id_m = re.search(r"\btask[ _]?([0-9a-f-]{8,})\b", low)
        if id_m:
            args["taskId"] = id_m.group(1)
        else:
            title_m = re.search(
                r"task\s+[«\"']?(.+?)[»\"']?\s+(?:a|al|entro|del)\b",
                t,
                re.IGNORECASE,
            )
            if title_m:
                args["title"] = title_m.group(1).strip()
        return ("reschedule_task", args)

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

    # CRM SUMMARY / REPORT
    if any(k in low for k in (
        "riepilogo", "sommario", "situazione", "panoramica",
        "come va il crm", "come sta il crm", "report crm", "stato crm",
        "dashboard", "kpi", "sintesi crm", "riporta la situazione",
    )):
        args = {}
        n_m = re.search(r"(\d+)\s*giorn", low)
        if n_m:
            args["days"] = int(n_m.group(1))
        elif "settimana" in low:
            args["days"] = 7
        elif "mese" in low:
            args["days"] = 30
        return ("crm_summary", args)

    # GENERATE REPORT
    if any(k in low for k in (
        "genera report", "generare report", "crea report", "report settimanale",
        "report mensile", "report del crm", "scrivi report", "report executive",
    )):
        args = {}
        if "settiman" in low:
            args["timeRange"] = "7d"
        elif "mensil" in low or "mese" in low:
            args["timeRange"] = "30d"
        elif "trimestr" in low or "90" in low:
            args["timeRange"] = "90d"
        title_m = re.search(
            r"report\s+[«\"']?(.+?)[»\"']?(?:\s+per il|\s+del |\s*$)",
            t,
            re.IGNORECASE,
        )
        if title_m and title_m.group(1).strip().lower() not in (
            "settimanale", "mensile", "del crm", "crm", "executive",
        ):
            args["title"] = title_m.group(1).strip()
        return ("generate_report", args)

    # BOOK DEMO / APPOINTMENT
    if any(k in low for k in (
        "prenota demo", "prenota una demo", "prenota la demo",
        "fissa demo", "fissa una demo", "fissa appuntamento",
        "prenota appuntamento", "prenota incontro", "schedula demo",
        "schedula appuntamento", "prenota un incontro", "booking demo",
    )):
        args = {}
        if email:
            args["email"] = email
        name_m = re.search(
            r"(?:demo|appuntamento|incontro)\s+(?:con|per)\s+([A-ZÀ-Ú][a-zà-ú]+)\s+([A-ZÀ-Ú][a-zà-ú]+)",
            t,
        )
        if name_m:
            args["firstName"] = name_m.group(1)
            args["lastName"] = name_m.group(2)
        if due:
            args["preferredDate"] = due
        time_m = re.search(r"\b(?:alle|ore|h)\s*(\d{1,2}[:.]?\d{0,2})\b", low)
        if time_m:
            slot = time_m.group(1).replace(".", ":")
            if ":" not in slot:
                slot = f"{slot}:00"
            args["timeSlot"] = slot
        comp_m = re.search(r"\b(?:di|per|della)\s+([A-Z][\w&.\s]{2,40})(?:\s+email|\s+il |\s+alle|\s*$)", t)
        if comp_m:
            args["companyName"] = comp_m.group(1).strip()
        if not args.get("email") or not args.get("preferredDate"):
            return None
        return ("book_demo", args)

    return None


# ── LLM tool-calling (optional) ──────────────────────────────────────────────

async def _llm_available() -> bool:
    """True if an LLM can be reached — DB settings win over env defaults."""
    from app.services.llm_settings_service import get_llm_runtime_config

    try:
        cfg = await get_llm_runtime_config()
    except Exception:
        cfg = {}
    if cfg.get("api_base") or cfg.get("api_key"):
        return True

    p = (settings.LLM_PROVIDER or "").lower()
    if p == "ollama":
        return True  # local
    if p == "openai":
        return bool(settings.OPENAI_API_KEY)
    if p == "anthropic":
        return bool(settings.ANTHROPIC_API_KEY)
    if p == "gemini":
        return bool(settings.GEMINI_API_KEY)
    return bool(settings.OPENAI_API_KEY or settings.LLM_BASE_URL)


async def _run_llm(message: str, user_id: str, session: dict | None = None) -> list[dict]:
    """Tool-calling loop with session history (max 4 iterations)."""
    import litellm
    from app.services.agent_session_service import build_system_context_async, history_for_llm
    from app.services.llm_settings_service import get_llm_runtime_config

    litellm.drop_params = True
    cfg = await get_llm_runtime_config()

    user_meta = None
    try:
        user_doc = await db["users"].find_one({"_id": user_id}) or {}
        user_meta = {
            "displayName": user_doc.get("displayName"),
            "email": user_doc.get("email"),
            "role": user_doc.get("role"),
        }
    except Exception:
        pass

    system = await build_system_context_async(user_id, session or {}, user_meta, message=message)
    try:
        from app.services import agent_memory as mem
        facts = await mem.list_facts(user_id, limit=8)
        block = mem.facts_prompt_block(facts)
        if block:
            system = f"{system}\n\n{block}"
    except Exception:
        pass
    messages = [{"role": "system", "content": system}]
    if session:
        messages.extend(history_for_llm(session))
    messages.append({"role": "user", "content": message})
    steps: list[dict] = []

    for _ in range(4):
        resp = await litellm.acompletion(
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            temperature=0.2,
            timeout=45,
            **cfg,
        )
        choice = resp["choices"][0]
        msg = choice.get("message") or {}
        tool_calls = msg.get("tool_calls") or []
        if not tool_calls:
            content = msg.get("content") or msg.get("reasoning_content") or ""
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

async def run_agent(message: str, user_id: str, session_id: str | None = None, user_role: str = "sales") -> dict:
    """
    Execute an agent turn. Returns {steps, reply, mode, sessionId}.
    """
    import time

    from app.services import agent_memory as mem
    from app.services import agent_session_service as sess

    started = time.monotonic()
    ok, err = sess.validate_message(message)
    if not ok:
        return {
            "ok": False,
            "error": err,
            "steps": [],
            "reply": err,
            "mode": "invalid",
            "sessionId": session_id,
        }
    message = message.strip()

    session = await sess.get_or_create_session(user_id, session_id)
    sid = session["id"]

    async def _finish(result: dict, mode: str, steps: list[dict], reply: str, ok_flag: bool, error: str | None = None) -> dict:
        duration_ms = int((time.monotonic() - started) * 1000)
        entity = sess.extract_entity_from_steps(steps)
        try:
            await sess.append_message(
                user_id, "user", message,
                session_id=sid, meta={"entity": entity} if entity else None,
            )
            await sess.append_message(
                user_id, "assistant", reply or "",
                session_id=sid,
                meta={"mode": mode, "tools": [s.get("name") for s in steps if s.get("type") == "tool"]},
            )
        except Exception:
            logger.exception("session persist failed")
        await sess.log_run(
            user_id=user_id,
            message=message,
            mode=mode,
            reply=reply or "",
            steps=steps,
            ok=ok_flag,
            duration_ms=duration_ms,
            session_id=sid,
            error=error,
        )
        out = dict(result)
        out.setdefault("ok", ok_flag)
        out.setdefault("steps", steps)
        out.setdefault("reply", reply)
        out.setdefault("mode", mode)
        out["sessionId"] = sid
        out["durationMs"] = duration_ms
        return out

    # 0) Memory commands («ricorda che…» / «preferisco…»)
    mem_cmd = mem.maybe_extract_memory_command(message)
    if mem_cmd:
        fact = await mem.remember_fact(user_id, mem_cmd["text"], mem_cmd["kind"])
        reply = f"Memorizzato: «{fact['text']}»"
        steps = [{"type": "tool", "name": "remember_fact", "args": mem_cmd, "result": {"ok": True, "fact": fact}}]
        return await _finish({"ok": True, "steps": steps, "reply": reply, "mode": "parser"}, "parser", steps, reply, True)

    async def _skill_hint(msg: str) -> str:
        """Prima skill con trigger nel messaggio → consiglio operativo."""
        try:
            from app.services.agent_skills_service import list_skills, match_skills

            skills = await list_skills(include_inactive=False)
            matched = match_skills(msg, skills, limit=1)
            if not matched:
                return ""
            s = matched[0]
            body_line = next(
                (ln.strip(" -•") for ln in (s.get("body") or "").splitlines() if ln.strip()),
                s.get("description") or "",
            )
            return f"💡 Skill «{s.get('title')}»: {body_line[:160]}"
        except Exception:
            return ""

    # 1b) Planner — richieste composte («crea lead X e poi crea task Y»)
    try:
        from app.services.agent_planner import format_action_summary, plan_message

        plan = plan_message(message, parse_command)
    except Exception:
        plan = []
    if plan:
        steps = []
        for step in plan:
            result = await run_tool(step["tool"], step.get("args") or {}, user_id, user_role=user_role)
            steps.append({"type": "tool", "name": step["tool"], "args": step.get("args"), "result": result})
        summary = format_action_summary(steps)
        ok_flag = any(s["result"].get("ok") for s in steps)
        return await _finish(
            {"ok": ok_flag, "steps": steps, "reply": summary, "mode": "parser", "plan": plan},
            "parser", steps, summary, ok_flag,
        )

    # 1) Deterministic parser first (fast, testable, works offline)
    try:
        parsed = parse_command(message)
    except Exception as exc:
        logger.exception("parse_command failed")
        parsed = None
        parse_error = str(exc)
    else:
        parse_error = None

    if parsed:
        name, args = parsed
        result = await run_tool(name, args, user_id, user_role=user_role)
        steps = [{"type": "tool", "name": name, "args": args, "result": result}]
        reply = result.get("message") or result.get("error") or "Fatto."
        if result.get("approvalRequired"):
            reply = result.get("message") or "Azione in attesa di approvazione."
        hint = await _skill_hint(message)
        if hint:
            reply = f"{reply}\n\n{hint}"
        return await _finish(
            {"ok": bool(result.get("ok") or result.get("approvalRequired")), "steps": steps, "reply": reply, "mode": "parser"},
            "parser", steps, reply, bool(result.get("ok")),
        )

    # 2) LLM tool-calling if available
    if await _llm_available():
        llm_error = None
        for attempt in range(2):
            try:
                steps = await _run_llm(message, user_id, session)
                reply_parts = []
                for s in steps:
                    if s.get("type") != "assistant":
                        continue
                    text = s.get("content") or s.get("reasoning_content") or ""
                    if text:
                        reply_parts.append(text)
                tool_notes = [
                    s["result"].get("message") or f"{s['name']}: {'ok' if s['result'].get('ok') else 'errore'}"
                    for s in steps
                    if s.get("type") == "tool"
                ]
                reply = "\n".join(reply_parts + tool_notes) or "Completato."
                # Se l'LLM ha solo chiacchierato senza usare tool su una richiesta dati CRM,
                # prova comunque un find_lead con l'entità nominata.
                if not tool_notes and any(k in message.lower() for k in (
                    "email", "settore", "telefono", "azienda", "lead", "contatto", "chi è", "chi e",
                )):
                    q = message
                    m = re.search(
                        r"(?:di|su|del|della|per)\s+[«\"']?(.+?)[»\"']?\s*[?.!]*$",
                        message.strip(),
                        re.IGNORECASE,
                    )
                    if m:
                        q = m.group(1).strip().strip("«»\"'.")
                    found = await _find_lead({"query": q}, user_id)
                    if found.get("ok"):
                        steps = steps + [{"type": "tool", "name": "find_lead", "args": {"query": q}, "result": found}]
                        reply = found.get("message") or reply
                        return await _finish(
                            {"ok": True, "steps": steps, "reply": reply, "mode": "llm"},
                            "llm", steps, reply, True,
                        )
                return await _finish(
                    {"ok": True, "steps": steps, "reply": reply, "mode": "llm"},
                    "llm", steps, reply, True,
                )
            except Exception as exc:
                llm_error = exc
                logger.warning("LLM agent attempt %s failed: %s", attempt + 1, exc)
                await asyncio.sleep(0.4)

        # Fallback: mai restituire solo l'errore grezzo
        q = _extract_person_name(message) or ""
        if not q:
            m = re.search(
                r"(?:di|su|del|della|per)\s+[«\"']?(.+?)[»\"']?\s*[?.!]*$",
                message.strip(),
                re.IGNORECASE,
            )
            if m:
                q = m.group(1).strip().strip("«»\"'.")
        if not q and session.get("lastEntity"):
            # «dammi la sua email» → ultima entità della sessione
            ent = session["lastEntity"]
            q = ent.get("email") or ent.get("name") or ent.get("id") or ""
        if not q:
            q = message
        found = await _find_lead({"query": q}, user_id)
        if found.get("ok"):
            steps = [{"type": "tool", "name": "find_lead", "args": {"query": q}, "result": found}]
            reply = found.get("message") or "Ecco cosa ho trovato."
            return await _finish(
                {"ok": True, "steps": steps, "reply": reply, "mode": "parser"},
                "parser", steps, reply, True,
            )

        help_res = await _help({}, user_id)
        reply = (
            f"Non sono riuscito a consultare il modello LLM ({type(llm_error).__name__}).\n\n"
            f"{help_res.get('message') or ''}"
        )
        hint = await _skill_hint(message)
        if hint:
            reply = f"{hint}\n\n{reply}"
        return await _finish(
            {"ok": False, "steps": [], "reply": reply, "mode": "llm_error"},
            "llm_error", [], reply, False, error=str(llm_error),
        )

    reply = (
        "Non ho capito. Prova comandi tipo: "
        "«crea lead Mario Rossi email mario@studio.it», "
        "«prenota demo con Mario Rossi email mario@studio.it il 2026-02-01 alle 15:00», "
        "«riepilogo CRM», "
        "«invia email a mario@studio.it oggetto Demo testo Ciao»."
    )
    try:
        from app.services.agent_config_service import get_agent_config

        _cfg = await get_agent_config()
        if _cfg.get("agentName"):
            reply = f"[{_cfg['agentName']}] {reply}"
    except Exception:
        pass
    hint = await _skill_hint(message)
    if hint:
        reply = f"{reply}\n\n{hint}"
    return await _finish(
        {"ok": False, "steps": [], "reply": reply, "mode": "fallback"},
        "fallback", [], reply, False,
    )
