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
            "description": "Trova un lead per email o nome",
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
    "crm_summary": _crm_summary,
    "book_demo": _book_demo,
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
    from app.services.llm_settings_service import get_llm_runtime_config

    litellm.drop_params = True
    cfg = await get_llm_runtime_config()
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
            "«prenota demo con Mario Rossi email mario@studio.it il 2026-02-01 alle 15:00», "
            "«riepilogo CRM», "
            "«invia email a mario@studio.it oggetto Demo testo Ciao»."
        ),
        "mode": "fallback",
    }
