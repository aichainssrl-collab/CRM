"""
Phase B agent tools — copertura moduli CRM (task, lead, deal, billing, content, comms, ops).

Pattern Agno toolkit: logica in funzioni isolate, registrate in TOOL_HANDLERS.
I tool mutanti usano i service esistenti (mai Mongo grezzo per le scritture complesse).
"""
from __future__ import annotations

import logging
from typing import Any

from app.services.db_service import db, utcnow, new_id
from app.services.activity_service import append_activity

logger = logging.getLogger(__name__)


def _ok(message: str, **data) -> dict:
    return {"ok": True, "message": message, **data}


def _err(message: str, **data) -> dict:
    return {"ok": False, "error": message, **data}


def _doc(d: dict | None) -> dict | None:
    if not d:
        return None
    out = dict(d)
    out["id"] = out.pop("_id", None)
    return out


async def _find_lead_doc(email: str | None, query: str | None = None) -> dict | None:
    if email:
        return await db["leads"].find_one({
            "email": {"$regex": f"^{__import__('re').escape(email.strip().lower())}$", "$options": "i"},
            "deletedAt": None,
        })
    if query:
        import re as _re
        rx = {"$regex": _re.escape(query), "$options": "i"}
        return await db["leads"].find_one({
            "deletedAt": None,
            "$or": [{"email": rx}, {"firstName": rx}, {"lastName": rx}, {"companyName": rx}],
        })
    return None


# ── B1 Task & attività ───────────────────────────────────────────────────────

async def _list_tasks(args: dict, user_id: str) -> dict:
    import re as _re
    query: dict[str, Any] = {"deletedAt": None}
    status = args.get("status")
    if status:
        query["status"] = status
    lead = await _find_lead_doc(args.get("leadEmail"), args.get("leadQuery"))
    if lead:
        query["leadId"] = lead["_id"]
    elif args.get("leadEmail") or args.get("leadQuery"):
        return _err("Lead non trovato")
    if args.get("assignedTo") == "me":
        query["assignedTo"] = user_id
    limit = min(int(args.get("limit") or 20), 100)
    cursor = db["tasks"].find(query).sort("dueDate", 1).limit(limit)
    rows = []
    async for d in cursor:
        rows.append({
            "id": d["_id"],
            "title": d.get("title"),
            "status": d.get("status"),
            "dueDate": str(d.get("dueDate") or ""),
            "priority": d.get("priority"),
            "leadId": d.get("leadId"),
        })
    return _ok(f"{len(rows)} task", tasks=rows, count=len(rows))


async def _complete_task(args: dict, user_id: str) -> dict:
    task_id = args.get("taskId")
    if not task_id:
        return _err("taskId obbligatorio")
    doc = await db["tasks"].find_one({"_id": task_id, "deletedAt": None})
    if not doc:
        return _err(f"Task non trovato: {task_id}")
    new_status = "completed" if args.get("status", "completed") == "completed" else "open"
    await db["tasks"].update_one(
        {"_id": task_id},
        {"$set": {"status": new_status, "updatedAt": utcnow(), "completedAt": utcnow() if new_status == "completed" else None}},
    )
    if doc.get("leadId"):
        await append_activity(doc["leadId"], {
            "type": "task",
            "title": f"Task «{doc.get('title')}» → {new_status}",
            "userId": user_id,
        })
    return _ok(f"Task «{doc.get('title')}» → {new_status}", taskId=task_id, status=new_status)


async def _delete_task(args: dict, user_id: str) -> dict:
    task_id = args.get("taskId")
    if not task_id:
        return _err("taskId obbligatorio")
    res = await db["tasks"].update_one(
        {"_id": task_id, "deletedAt": None},
        {"$set": {"deletedAt": utcnow(), "updatedAt": utcnow()}},
    )
    if res.modified_count == 0:
        return _err(f"Task non trovato: {task_id}")
    return _ok(f"Task {task_id} eliminato", taskId=task_id)


async def _add_activity(args: dict, user_id: str) -> dict:
    lead = await _find_lead_doc(args.get("leadEmail"), args.get("leadQuery"))
    if not lead:
        return _err("Lead non trovato")
    body = (args.get("body") or "").strip()
    if not body:
        return _err("body obbligatorio")
    act = await append_activity(lead["_id"], {
        "type": args.get("type") or "note",
        "title": body[:120],
        "body": body,
        "userId": user_id,
    })
    return _ok(f"Attività aggiunta su {lead.get('email')}", activityId=(act or {}).get("id"), leadId=lead["_id"])


# ── B2 Lead ──────────────────────────────────────────────────────────────────

async def _search_leads(args: dict, user_id: str) -> dict:
    import re as _re
    query: dict[str, Any] = {"deletedAt": None}
    for field in ("status", "industry", "source"):
        if args.get(field):
            query[field] = args[field]
    if args.get("assignedTo") == "me":
        query["assignedTo"] = user_id
    if args.get("minScore") is not None:
        query["leadScore"] = {"$gte": int(args["minScore"])}
    if args.get("q"):
        rx = {"$regex": _re.escape(str(args["q"])), "$options": "i"}
        query["$or"] = [{"email": rx}, {"firstName": rx}, {"lastName": rx}, {"companyName": rx}]
    limit = min(int(args.get("limit") or 15), 50)
    cursor = db["leads"].find(query).sort("leadScore", -1).limit(limit)
    rows = []
    async for d in cursor:
        rows.append({
            "id": d["_id"],
            "email": d.get("email"),
            "name": f"{d.get('firstName') or ''} {d.get('lastName') or ''}".strip(),
            "companyName": d.get("companyName"),
            "industry": d.get("industry"),
            "status": d.get("status"),
            "leadScore": d.get("leadScore"),
        })
    return _ok(f"{len(rows)} lead", leads=rows, count=len(rows))


async def _delete_lead(args: dict, user_id: str) -> dict:
    """Soft delete — richiede confirm=true (guardrail HITL-lite)."""
    if not args.get("confirm"):
        return _err("Azione distruttiva: ripeti con confirm=true dopo conferma dell'utente")
    lead = await _find_lead_doc(args.get("email"), args.get("query"))
    if not lead:
        return _err("Lead non trovato")
    await db["leads"].update_one(
        {"_id": lead["_id"]},
        {"$set": {"deletedAt": utcnow(), "updatedAt": utcnow()}},
    )
    return _ok(f"Lead {lead.get('email')} eliminato (soft delete)", leadId=lead["_id"])


# ── B3 Deal ──────────────────────────────────────────────────────────────────

async def _delete_deal(args: dict, user_id: str) -> dict:
    if not args.get("confirm"):
        return _err("Azione distruttiva: ripeti con confirm=true")
    deal_id = args.get("dealId")
    if not deal_id:
        return _err("dealId obbligatorio")
    res = await db["deals"].update_one(
        {"_id": deal_id, "deletedAt": None},
        {"$set": {"deletedAt": utcnow(), "updatedAt": utcnow()}},
    )
    if res.modified_count == 0:
        return _err(f"Deal non trovato: {deal_id}")
    return _ok(f"Deal {deal_id} eliminato", dealId=deal_id)


async def _move_deal_stage(args: dict, user_id: str) -> dict:
    stage = args.get("stage")
    if stage not in ("new", "qualified", "proposal", "negotiation", "won", "lost"):
        return _err("stage non valido (new|qualified|proposal|negotiation|won|lost)")
    deal_id = args.get("dealId")
    query = {"deletedAt": None}
    if deal_id:
        query["_id"] = deal_id
    elif args.get("title"):
        import re as _re
        query["title"] = {"$regex": _re.escape(args["title"]), "$options": "i"}
    else:
        return _err("dealId o title obbligatorio")
    doc = await db["deals"].find_one_and_update(
        query,
        {"$set": {"stage": stage, "updatedAt": utcnow()}},
    )
    if not doc:
        return _err("Deal non trovato")
    return _ok(f"Deal «{doc.get('title')}» → {stage}", dealId=doc["_id"], stage=stage)


async def _deal_pipeline(args: dict, user_id: str) -> dict:
    pipeline = [
        {"$match": {"deletedAt": None}},
        {"$group": {"_id": "$stage", "count": {"$sum": 1}, "value": {"$sum": "$value"}}},
    ]
    rows = []
    async for r in db["deals"].aggregate(pipeline):
        rows.append({"stage": r["_id"] or "?", "count": r["count"], "value": float(r.get("value") or 0)})
    rows.sort(key=lambda x: x["stage"])
    return _ok(f"{len(rows)} stage", stages=rows)


# ── B4 Proposte & fatture ────────────────────────────────────────────────────

async def _list_proposals(args: dict, user_id: str) -> dict:
    from app.services import proposal_service
    status = args.get("status")
    docs = await proposal_service.list_proposals(status)
    summary = [
        {
            "id": d.get("id"),
            "title": d.get("title"),
            "clientName": d.get("clientName"),
            "clientEmail": d.get("clientEmail"),
            "status": d.get("status"),
            "total": d.get("total"),
        }
        for d in (docs or [])[:20]
    ]
    return _ok(f"{len(summary)} proposte", proposals=summary, count=len(summary))


async def _create_proposal(args: dict, user_id: str) -> dict:
    from app.services import proposal_service
    if not args.get("title") or not args.get("clientName"):
        return _err("title e clientName obbligatori")
    items = args.get("items") or []
    if not items:
        return _err("almeno una riga items [{name, quantity, unitPrice}]")
    data = {
        "title": args["title"],
        "clientName": args["clientName"],
        "clientEmail": args.get("clientEmail") or "",
        "taxRate": float(args.get("taxRate") or 22),
        "notes": args.get("notes"),
        "items": items,
    }
    doc = await proposal_service.create_proposal(data, user_id)
    return _ok(f"Proposta «{doc.get('title')}» creata", proposalId=doc.get("id"), number=doc.get("number"))


async def _mark_proposal(args: dict, user_id: str) -> dict:
    from app.services import proposal_service
    pid = args.get("proposalId")
    action = args.get("action")
    if not pid or action not in ("sent", "accepted", "rejected"):
        return _err("proposalId e action (sent|accepted|rejected) obbligatori")
    fn = {"sent": proposal_service.mark_sent, "accepted": proposal_service.mark_accepted, "rejected": proposal_service.mark_rejected}[action]
    if action != "accepted" and action != "rejected" and args.get("confirm") is False:
        pass
    doc = await fn(pid)
    if not doc:
        return _err("Proposta non trovata")
    return _ok(f"Proposta → {action}", proposalId=pid, status=action)


async def _list_invoices(args: dict, user_id: str) -> dict:
    from app.services import invoice_service
    docs = await invoice_service.list_invoices(args.get("status"))
    summary = [
        {
            "id": d.get("id"),
            "number": d.get("number"),
            "title": d.get("title"),
            "clientName": d.get("clientName"),
            "status": d.get("status"),
            "total": d.get("total"),
        }
        for d in (docs or [])[:20]
    ]
    return _ok(f"{len(summary)} fatture", invoices=summary, count=len(summary))


async def _create_invoice(args: dict, user_id: str) -> dict:
    from app.services import invoice_service
    if args.get("fromProposalId"):
        doc = await invoice_service.create_from_proposal(args["fromProposalId"], user_id)
        if not doc:
            return _err("Proposta non trovata o non accettata")
        return _ok(f"Fattura {doc.get('number')} creata da proposta", invoiceId=doc.get("id"))
    if not args.get("title") or not args.get("clientName"):
        return _err("title e clientName obbligatori (oppure fromProposalId)")
    items = args.get("items") or []
    data = {
        "title": args["title"],
        "clientName": args["clientName"],
        "clientEmail": args.get("clientEmail") or "",
        "taxRate": float(args.get("taxRate") or 22),
        "dueDate": args.get("dueDate"),
        "notes": args.get("notes"),
        "items": items,
    }
    doc = await invoice_service.create_invoice(data, user_id)
    return _ok(f"Fattura {doc.get('number')} creata", invoiceId=doc.get("id"))


async def _mark_invoice(args: dict, user_id: str) -> dict:
    from app.services import invoice_service
    iid = args.get("invoiceId")
    action = args.get("action")
    if not iid or action not in ("sent", "paid", "cancelled"):
        return _err("invoiceId e action (sent|paid|cancelled) obbligatori")
    fn = {"sent": invoice_service.mark_sent, "paid": invoice_service.mark_paid, "cancelled": invoice_service.mark_cancelled}[action]
    doc = await fn(iid)
    if not doc:
        return _err("Fattura non trovata o stato non valido")
    return _ok(f"Fattura → {action}", invoiceId=iid, status=action)


async def _invoice_stats(args: dict, user_id: str) -> dict:
    from app.services import invoice_service
    stats = await invoice_service.invoice_stats()
    return _ok("Statistiche fatture", stats=stats)


# ── B5 Prodotti / content / template / sequence ─────────────────────────────

async def _list_products(args: dict, user_id: str) -> dict:
    cursor = db["products"].find({"deletedAt": None}).sort("name", 1).limit(30)
    rows = []
    async for d in cursor:
        rows.append({"id": d["_id"], "name": d.get("name"), "price": d.get("price"), "description": d.get("description")})
    return _ok(f"{len(rows)} prodotti", products=rows)


async def _search_content(args: dict, user_id: str) -> dict:
    import re as _re
    query: dict = {"deletedAt": None}
    if args.get("type"):
        query["type"] = args["type"]
    if args.get("tag"):
        query["tags"] = args["tag"]
    if args.get("q"):
        rx = {"$regex": _re.escape(args["q"]), "$options": "i"}
        query["$or"] = [{"title": rx}, {"body": rx}, {"description": rx}]
    cursor = db["content_library"].find(query).sort("updatedAt", -1).limit(10)
    rows = []
    async for d in cursor:
        rows.append({
            "id": d["_id"],
            "title": d.get("title"),
            "type": d.get("type"),
            "preview": (d.get("body") or "")[:120],
        })
    return _ok(f"{len(rows)} contenuti", contents=rows)


async def _list_email_templates(args: dict, user_id: str) -> dict:
    cursor = db["email_templates"].find({"deletedAt": None}).limit(20)
    rows = []
    async for d in cursor:
        rows.append({"id": d["_id"], "name": d.get("name"), "subject": d.get("subject"), "category": d.get("category")})
    return _ok(f"{len(rows)} template", templates=rows)


async def _enroll_sequence(args: dict, user_id: str) -> dict:
    from app.services import email_sequence_service as ess
    if not args.get("sequenceId") and args.get("sequenceName"):
        doc = await db["email_sequences"].find_one({
            "name": {"$regex": args["sequenceName"], "$options": "i"},
            "deletedAt": None,
        })
        if not doc:
            return _err("Sequenza non trovata")
        seq_id = doc["_id"]
    else:
        seq_id = args.get("sequenceId")
    if not seq_id:
        return _err("sequenceId o sequenceName obbligatorio")
    lead = await _find_lead_doc(args.get("leadEmail"), args.get("leadQuery"))
    if not lead:
        return _err("Lead non trovato")
    enr = await ess.enroll_lead(seq_id, lead["_id"])
    if not enr:
        return _err("Iscrizione fallita (sequenza o lead assente)")
    return _ok(f"Lead {lead.get('email')} iscritto alla sequenza", enrollment=enr)


# ── B6 Comunicazioni / calendar ──────────────────────────────────────────────

async def _list_whatsapp(args: dict, user_id: str) -> dict:
    query: dict = {"deletedAt": None}
    if args.get("status"):
        query["status"] = args["status"]
    cursor = db["whatsapp_conversations"].find(query).sort("updatedAt", -1).limit(10)
    rows = []
    async for d in cursor:
        rows.append({
            "id": d["_id"],
            "phone": d.get("phone"),
            "leadName": d.get("leadName"),
            "status": d.get("status"),
        })
    return _ok(f"{len(rows)} conversazioni", conversations=rows)


async def _send_whatsapp(args: dict, user_id: str) -> dict:
    from app.services import whatsapp_service as ws
    conv_id = args.get("conversationId")
    body = (args.get("body") or "").strip()
    if not conv_id or not body:
        return _err("conversationId e body obbligatori")
    if not args.get("confirm"):
        return _err("Invio messaggio esterno: ripeti con confirm=true dopo conferma")
    msg = await ws.send_message(conv_id, body)
    if not msg:
        return _err("Conversazione non trovata")
    return _ok("Messaggio inviato", messageId=msg.get("id"))


async def _list_calendar(args: dict, user_id: str) -> dict:
    from app.services import calendar_service as cs
    year = int(args.get("year") or utcnow().year)
    month = int(args.get("month") or utcnow().month)
    events = await cs.get_calendar_events(year, month)
    return _ok(f"{len(events)} eventi {month}/{year}", events=events[:30], count=len(events))


# ── B7 Ops: export, reports, kpi, competitors ────────────────────────────────

async def _export_csv(args: dict, user_id: str) -> dict:
    from app.services import export_service as es
    kind = args.get("kind") or "leads"
    if kind == "deals":
        csv_text = await es.export_deals_csv()
    elif kind == "contacts":
        csv_text = await es.export_contacts_csv()
    else:
        csv_text = await es.export_leads_csv()
    # non restituire tutto il CSV: salva e ritorna id
    export_id = new_id()
    await db["agent_exports"].insert_one({
        "_id": export_id,
        "userId": user_id,
        "kind": kind,
        "csv": csv_text[:500_000],
        "rowCount": csv_text.count("\n") - 1,
        "createdAt": utcnow(),
        "deletedAt": None,
    })
    return _ok(
        f"Export {kind} pronto ({csv_text.count(chr(10)) - 1} righe)",
        exportId=export_id,
        downloadUrl=f"/api/v1/agent/exports/{export_id}",
    )


async def _list_reports(args: dict, user_id: str) -> dict:
    cursor = db["reports"].find({"deletedAt": None}).sort("createdAt", -1).limit(10)
    rows = []
    async for d in cursor:
        rows.append({
            "id": d["_id"],
            "title": d.get("title"),
            "timeRange": d.get("timeRange"),
            "createdAt": str(d.get("createdAt") or ""),
        })
    return _ok(f"{len(rows)} report", reports=rows)


async def _crm_kpi(args: dict, user_id: str) -> dict:
    from datetime import timedelta
    from app.services import analytics_service
    days = int(args.get("days") or 30)
    since = utcnow() - timedelta(days=days)
    kpis = await analytics_service.get_kpi_summary(since=since)
    return _ok(f"KPI ultimi {days} giorni", kpis=kpis)


async def _competitor_status(args: dict, user_id: str) -> dict:
    total = await db["competitors"].count_documents({"deletedAt": None})
    active = await db["competitors"].count_documents({"deletedAt": None, "status": "active"})
    changes = await db["competitor_changes"].count_documents({"deletedAt": None})
    return _ok(
        f"{total} competitor ({active} attivi, {changes} cambi)",
        total=total, active=active, changes=changes,
    )


# ── Registry ─────────────────────────────────────────────────────────────────

PHASE_B_TOOL_DEFS: list[dict] = [
    {"type": "function", "function": {
        "name": "list_tasks",
        "description": "Elenca task (filtro status, lead, assegnatario)",
        "parameters": {"type": "object", "properties": {
            "status": {"type": "string", "enum": ["open", "completed"]},
            "leadEmail": {"type": "string"},
            "leadQuery": {"type": "string"},
            "assignedTo": {"type": "string", "description": "me = utente corrente"},
            "limit": {"type": "integer"},
        }},
    }},
    {"type": "function", "function": {
        "name": "complete_task",
        "description": "Segna un task come completato (o riapri)",
        "parameters": {"type": "object", "properties": {
            "taskId": {"type": "string"},
            "status": {"type": "string", "enum": ["completed", "open"]},
        }, "required": ["taskId"]},
    }},
    {"type": "function", "function": {
        "name": "delete_task",
        "description": "Elimina un task (soft delete)",
        "parameters": {"type": "object", "properties": {"taskId": {"type": "string"}}, "required": ["taskId"]},
    }},
    {"type": "function", "function": {
        "name": "add_activity",
        "description": "Aggiungi una nota/attività a un lead",
        "parameters": {"type": "object", "properties": {
            "leadEmail": {"type": "string"},
            "leadQuery": {"type": "string"},
            "body": {"type": "string"},
            "type": {"type": "string", "enum": ["note", "call", "meeting", "email"]},
        }, "required": ["body"]},
    }},
    {"type": "function", "function": {
        "name": "search_leads",
        "description": "Cerca lead con filtri (status, industry, score, testo)",
        "parameters": {"type": "object", "properties": {
            "q": {"type": "string"},
            "status": {"type": "string"},
            "industry": {"type": "string"},
            "source": {"type": "string"},
            "minScore": {"type": "integer"},
            "assignedTo": {"type": "string"},
            "limit": {"type": "integer"},
        }},
    }},
    {"type": "function", "function": {
        "name": "delete_lead",
        "description": "Elimina un lead (soft delete). Richiede confirm=true",
        "parameters": {"type": "object", "properties": {
            "email": {"type": "string"},
            "query": {"type": "string"},
            "confirm": {"type": "boolean"},
        }, "required": ["confirm"]},
    }},
    {"type": "function", "function": {
        "name": "delete_deal",
        "description": "Elimina un deal (soft delete). Richiede confirm=true",
        "parameters": {"type": "object", "properties": {
            "dealId": {"type": "string"},
            "confirm": {"type": "boolean"},
        }, "required": ["dealId", "confirm"]},
    }},
    {"type": "function", "function": {
        "name": "move_deal_stage",
        "description": "Sposta un deal in un altro stage",
        "parameters": {"type": "object", "properties": {
            "dealId": {"type": "string"},
            "title": {"type": "string"},
            "stage": {"type": "string", "enum": ["new", "qualified", "proposal", "negotiation", "won", "lost"]},
        }, "required": ["stage"]},
    }},
    {"type": "function", "function": {
        "name": "deal_pipeline",
        "description": "Riepilogo pipeline: deal e valore per stage",
        "parameters": {"type": "object", "properties": {}},
    }},
    {"type": "function", "function": {
        "name": "list_proposals",
        "description": "Elenca proposte commerciali",
        "parameters": {"type": "object", "properties": {
            "status": {"type": "string", "enum": ["draft", "sent", "accepted", "rejected"]},
        }},
    }},
    {"type": "function", "function": {
        "name": "create_proposal",
        "description": "Crea una proposta con righe (items)",
        "parameters": {"type": "object", "properties": {
            "title": {"type": "string"},
            "clientName": {"type": "string"},
            "clientEmail": {"type": "string"},
            "taxRate": {"type": "number"},
            "notes": {"type": "string"},
            "items": {"type": "array", "items": {"type": "object"}},
        }, "required": ["title", "clientName", "items"]},
    }},
    {"type": "function", "function": {
        "name": "mark_proposal",
        "description": "Cambia stato proposta (sent/accepted/rejected)",
        "parameters": {"type": "object", "properties": {
            "proposalId": {"type": "string"},
            "action": {"type": "string", "enum": ["sent", "accepted", "rejected"]},
        }, "required": ["proposalId", "action"]},
    }},
    {"type": "function", "function": {
        "name": "list_invoices",
        "description": "Elenca fatture",
        "parameters": {"type": "object", "properties": {
            "status": {"type": "string", "enum": ["draft", "sent", "paid", "cancelled", "overdue"]},
        }},
    }},
    {"type": "function", "function": {
        "name": "create_invoice",
        "description": "Crea fattura (da proposta o da zero)",
        "parameters": {"type": "object", "properties": {
            "fromProposalId": {"type": "string"},
            "title": {"type": "string"},
            "clientName": {"type": "string"},
            "clientEmail": {"type": "string"},
            "taxRate": {"type": "number"},
            "dueDate": {"type": "string"},
            "notes": {"type": "string"},
            "items": {"type": "array", "items": {"type": "object"}},
        }},
    }},
    {"type": "function", "function": {
        "name": "mark_invoice",
        "description": "Aggiorna stato fattura (sent/paid/cancelled)",
        "parameters": {"type": "object", "properties": {
            "invoiceId": {"type": "string"},
            "action": {"type": "string", "enum": ["sent", "paid", "cancelled"]},
        }, "required": ["invoiceId", "action"]},
    }},
    {"type": "function", "function": {
        "name": "invoice_stats",
        "description": "Statistiche fatture (totali, per stato)",
        "parameters": {"type": "object", "properties": {}},
    }},
    {"type": "function", "function": {
        "name": "list_products",
        "description": "Elenca prodotti e prezzi",
        "parameters": {"type": "object", "properties": {}},
    }},
    {"type": "function", "function": {
        "name": "search_content",
        "description": "Cerca nella content library",
        "parameters": {"type": "object", "properties": {
            "q": {"type": "string"},
            "type": {"type": "string"},
            "tag": {"type": "string"},
        }},
    }},
    {"type": "function", "function": {
        "name": "list_email_templates",
        "description": "Elenca template email",
        "parameters": {"type": "object", "properties": {}},
    }},
    {"type": "function", "function": {
        "name": "enroll_sequence",
        "description": "Iscrivi un lead a una email sequence",
        "parameters": {"type": "object", "properties": {
            "sequenceId": {"type": "string"},
            "sequenceName": {"type": "string"},
            "leadEmail": {"type": "string"},
            "leadQuery": {"type": "string"},
        }},
    }},
    {"type": "function", "function": {
        "name": "list_whatsapp_conversations",
        "description": "Elenca conversazioni WhatsApp",
        "parameters": {"type": "object", "properties": {
            "status": {"type": "string", "enum": ["open", "closed"]},
        }},
    }},
    {"type": "function", "function": {
        "name": "send_whatsapp",
        "description": "Invia messaggio WhatsApp. Richiede confirm=true",
        "parameters": {"type": "object", "properties": {
            "conversationId": {"type": "string"},
            "body": {"type": "string"},
            "confirm": {"type": "boolean"},
        }, "required": ["conversationId", "body", "confirm"]},
    }},
    {"type": "function", "function": {
        "name": "list_calendar_events",
        "description": "Eventi calendario (task, booking, deal) per mese",
        "parameters": {"type": "object", "properties": {
            "year": {"type": "integer"},
            "month": {"type": "integer"},
        }},
    }},
    {"type": "function", "function": {
        "name": "export_csv",
        "description": "Genera export CSV (leads/deals/contacts) e ritorna downloadUrl",
        "parameters": {"type": "object", "properties": {
            "kind": {"type": "string", "enum": ["leads", "deals", "contacts"]},
        }},
    }},
    {"type": "function", "function": {
        "name": "list_reports",
        "description": "Elenca report generati",
        "parameters": {"type": "object", "properties": {}},
    }},
    {"type": "function", "function": {
        "name": "crm_kpi",
        "description": "KPI CRM (lead, deal, ricavi) per periodo",
        "parameters": {"type": "object", "properties": {
            "days": {"type": "integer", "description": "finestra in giorni (default 30)"},
        }},
    }},
    {"type": "function", "function": {
        "name": "competitor_status",
        "description": "Stato competitor monitoring",
        "parameters": {"type": "object", "properties": {}},
    }},
]

PHASE_B_HANDLERS: dict[str, Any] = {
    "list_tasks": _list_tasks,
    "complete_task": _complete_task,
    "delete_task": _delete_task,
    "add_activity": _add_activity,
    "search_leads": _search_leads,
    "delete_lead": _delete_lead,
    "delete_deal": _delete_deal,
    "move_deal_stage": _move_deal_stage,
    "deal_pipeline": _deal_pipeline,
    "list_proposals": _list_proposals,
    "create_proposal": _create_proposal,
    "mark_proposal": _mark_proposal,
    "list_invoices": _list_invoices,
    "create_invoice": _create_invoice,
    "mark_invoice": _mark_invoice,
    "invoice_stats": _invoice_stats,
    "list_products": _list_products,
    "search_content": _search_content,
    "list_email_templates": _list_email_templates,
    "enroll_sequence": _enroll_sequence,
    "list_whatsapp_conversations": _list_whatsapp,
    "send_whatsapp": _send_whatsapp,
    "list_calendar_events": _list_calendar,
    "export_csv": _export_csv,
    "list_reports": _list_reports,
    "crm_kpi": _crm_kpi,
    "competitor_status": _competitor_status,
}


# ── Phase D — workflow + team ────────────────────────────────────────────────

async def _workflow_inbound_lead(args: dict, user_id: str) -> dict:
    from app.services import agent_workflows as w

    lead = await _find_lead_doc(args.get("leadEmail"), args.get("leadQuery"))
    if not lead:
        return _err("Lead non trovato")
    result = await w.run_inbound_lead_workflow(
        lead["_id"],
        user_id,
        send_welcome=bool(args.get("sendWelcome")),
        create_followup_task=bool(args.get("createFollowupTask", True)),
    )
    return {
        "ok": result.get("ok", False),
        "message": result.get("summary") or "Workflow completato",
        **{k: v for k, v in result.items() if k not in ("ok",)},
    }


async def _marketing_content(args: dict, user_id: str) -> dict:
    from app.services import agent_workflows as w

    res = await w.marketing_assist(
        user_id,
        args.get("topic") or "",
        content_type=args.get("contentType") or "email",
        topic=args.get("topic") or "",
    )
    if not res.get("ok"):
        return _err(res.get("error") or "Marketing agent non disponibile")
    return _ok(res.get("message") or "Contenuto generato", team="marketing", content=res.get("content"))


async def _marketing_insights(args: dict, user_id: str) -> dict:
    from app.services import agent_workflows as w

    res = await w.marketing_assist(user_id, "insights", topic="insight marketing")
    if not res.get("ok"):
        return _err(res.get("error") or "Insight non disponibili")
    return _ok("Insight marketing", insights=res.get("insights"))


PHASE_D_TOOL_DEFS: list[dict] = [
    {"type": "function", "function": {
        "name": "workflow_inbound_lead",
        "description": "Workflow multi-step su un lead inbound: score, task follow-up, welcome email (opzionale), suggerimento deal",
        "parameters": {"type": "object", "properties": {
            "leadEmail": {"type": "string"},
            "leadQuery": {"type": "string"},
            "sendWelcome": {"type": "boolean"},
            "createFollowupTask": {"type": "boolean"},
        }},
    }},
    {"type": "function", "function": {
        "name": "marketing_content",
        "description": "Team marketing: genera contenuto (email, post, landing) su un tema",
        "parameters": {"type": "object", "properties": {
            "topic": {"type": "string"},
            "contentType": {"type": "string", "enum": ["email", "post", "landing", "ads"]},
        }, "required": ["topic"]},
    }},
    {"type": "function", "function": {
        "name": "marketing_insights",
        "description": "Team marketing: insight e suggerimenti dal CRM",
        "parameters": {"type": "object", "properties": {}},
    }},
]

PHASE_D_HANDLERS = {
    "workflow_inbound_lead": _workflow_inbound_lead,
    "marketing_content": _marketing_content,
    "marketing_insights": _marketing_insights,
}


# ── Phase F — knowledge + follow-up ──────────────────────────────────────────

async def _search_knowledge(args: dict, user_id: str) -> dict:
    from app.services import agent_knowledge as k

    kinds = args.get("kinds")
    if isinstance(kinds, str):
        kinds = [kinds]
    res = await k.search_knowledge(
        args.get("query") or args.get("q") or "",
        kinds=kinds,
        limit=min(int(args.get("limit") or 8), 20),
    )
    if not res.get("ok"):
        return _err(res.get("error") or "Ricerca knowledge fallita")
    return _ok(res["message"], results=res["results"], count=res["count"])


async def _schedule_followup(args: dict, user_id: str) -> dict:
    """Crea automaticamente un task di follow-up (anche da workflow/agent)."""
    lead = await _find_lead_doc(args.get("leadEmail"), args.get("leadQuery"))
    if not lead:
        return _err("Lead non trovato")
    title = args.get("title") or f"Follow-up {lead.get('email')}"
    now = utcnow()
    task_id = new_id()
    await db["tasks"].insert_one({
        "_id": task_id,
        "leadId": lead["_id"],
        "title": title,
        "description": args.get("description") or "Follow-up automatico generato dall'agent",
        "dueDate": now,
        "priority": args.get("priority") or "normal",
        "type": "todo",
        "status": "open",
        "assignedTo": user_id,
        "createdBy": user_id,
        "createdAt": now,
        "updatedAt": now,
        "deletedAt": None,
    })
    await db["leads"].update_one({"_id": lead["_id"]}, {"$inc": {"taskCount": 1}})
    return _ok(f"Follow-up creato su {lead.get('email')}", taskId=task_id, leadId=lead["_id"])


PHASE_F_TOOL_DEFS: list[dict] = [
    {"type": "function", "function": {
        "name": "search_knowledge",
        "description": "Cerca nella knowledge CRM (content library, template, prodotti, lead, deal)",
        "parameters": {"type": "object", "properties": {
            "query": {"type": "string"},
            "kinds": {"type": "array", "items": {"type": "string", "enum": ["content", "template", "product", "lead", "deal"]}},
            "limit": {"type": "integer"},
        }, "required": ["query"]},
    }},
    {"type": "function", "function": {
        "name": "schedule_followup",
        "description": "Crea un task di follow-up automatico su un lead",
        "parameters": {"type": "object", "properties": {
            "leadEmail": {"type": "string"},
            "leadQuery": {"type": "string"},
            "title": {"type": "string"},
            "description": {"type": "string"},
            "priority": {"type": "string", "enum": ["low", "normal", "high"]},
        }},
    }},
]

PHASE_F_HANDLERS = {
    "search_knowledge": _search_knowledge,
    "schedule_followup": _schedule_followup,
}
