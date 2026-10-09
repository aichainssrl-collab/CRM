"""
Invoices service — billing documents, optionally generated from accepted proposals.
"""
from typing import Optional
from app.services.db_service import db, new_id, utcnow, _to_dict
from app.services.proposal_service import compute_totals
import logging

logger = logging.getLogger(__name__)

STATUSES = ("draft", "sent", "paid", "overdue", "cancelled")


async def _next_number() -> str:
    year = utcnow().year
    count = await db["invoices"].count_documents({"deletedAt": None})
    return f"INV-{year}-{count + 1:04d}"


def _doc_from_items(data: dict) -> dict:
    totals = compute_totals(data.get("items", []), data.get("taxRate", 0))
    return {
        "title": data.get("title", ""),
        "clientName": data.get("clientName", ""),
        "clientEmail": data.get("clientEmail", ""),
        "leadId": data.get("leadId"),
        "dealId": data.get("dealId"),
        "proposalId": data.get("proposalId"),
        **totals,
        "currency": data.get("currency", "EUR"),
        "issueDate": data.get("issueDate") or utcnow().isoformat(),
        "dueDate": data.get("dueDate"),
        "notes": data.get("notes", ""),
    }


async def create_invoice(data: dict, created_by: str) -> dict:
    now = utcnow()
    doc = {
        "_id": new_id(),
        "number": await _next_number(),
        "status": "draft",
        **_doc_from_items(data),
        "sentAt": None,
        "paidAt": None,
        "createdBy": created_by,
        "createdAt": now,
        "updatedAt": now,
        "deletedAt": None,
    }
    await db["invoices"].insert_one(doc)
    return _to_dict(doc)


async def create_from_proposal(proposal_id: str, created_by: str) -> Optional[dict]:
    """Create an invoice snapshot from an accepted proposal."""
    prop = await db["proposals"].find_one(
        {"_id": proposal_id, "deletedAt": None, "status": "accepted"}
    )
    if not prop:
        return None
    data = {
        "title": prop.get("title", ""),
        "clientName": prop.get("clientName", ""),
        "clientEmail": prop.get("clientEmail", ""),
        "leadId": prop.get("leadId"),
        "dealId": prop.get("dealId"),
        "proposalId": proposal_id,
        "items": prop.get("items") or [],
        "taxRate": prop.get("taxRate", 0),
        "currency": prop.get("currency", "EUR"),
        "notes": prop.get("notes", ""),
    }
    return await create_invoice(data, created_by)


async def list_invoices(status: Optional[str] = None) -> list[dict]:
    query: dict = {"deletedAt": None}
    if status:
        query["status"] = status
    cursor = db["invoices"].find(query).sort("createdAt", -1)
    docs = await cursor.to_list(length=200)
    return [_to_dict(d) for d in docs]


async def get_invoice(invoice_id: str) -> Optional[dict]:
    doc = await db["invoices"].find_one({"_id": invoice_id, "deletedAt": None})
    return _to_dict(doc) if doc else None


async def update_invoice(invoice_id: str, data: dict) -> Optional[dict]:
    if "items" in data or "taxRate" in data:
        current = await get_invoice(invoice_id)
        if not current:
            return None
        items = data.get("items", current.get("items", []))
        tax_rate = data.get("taxRate", current.get("taxRate", 0))
        data.update(compute_totals(items, tax_rate))
    data["updatedAt"] = utcnow()
    doc = await db["invoices"].find_one_and_update(
        {"_id": invoice_id, "deletedAt": None},
        {"$set": data},
        return_document=True,
    )
    return _to_dict(doc) if doc else None


async def delete_invoice(invoice_id: str) -> bool:
    now = utcnow()
    result = await db["invoices"].update_one(
        {"_id": invoice_id, "deletedAt": None},
        {"$set": {"deletedAt": now, "updatedAt": now}},
    )
    return result.modified_count > 0


async def mark_sent(invoice_id: str) -> Optional[dict]:
    now = utcnow()
    doc = await db["invoices"].find_one_and_update(
        {"_id": invoice_id, "deletedAt": None, "status": "draft"},
        {"$set": {"status": "sent", "sentAt": now, "updatedAt": now}},
        return_document=True,
    )
    return _to_dict(doc) if doc else None


async def mark_paid(invoice_id: str) -> Optional[dict]:
    now = utcnow()
    doc = await db["invoices"].find_one_and_update(
        {"_id": invoice_id, "deletedAt": None, "status": {"$in": ["draft", "sent", "overdue"]}},
        {"$set": {"status": "paid", "paidAt": now, "updatedAt": now}},
        return_document=True,
    )
    return _to_dict(doc) if doc else None


async def mark_cancelled(invoice_id: str) -> Optional[dict]:
    now = utcnow()
    doc = await db["invoices"].find_one_and_update(
        {"_id": invoice_id, "deletedAt": None, "status": {"$ne": "paid"}},
        {"$set": {"status": "cancelled", "updatedAt": now}},
        return_document=True,
    )
    return _to_dict(doc) if doc else None


async def invoice_stats() -> dict:
    pipeline = [
        {"$match": {"deletedAt": None}},
        {
            "$group": {
                "_id": "$status",
                "count": {"$sum": 1},
                "totalValue": {"$sum": "$total"},
            }
        },
    ]
    rows = await db["invoices"].aggregate(pipeline).to_list(length=20)
    by_status = {r["_id"]: {"count": r["count"], "totalValue": round(r["totalValue"], 2)} for r in rows}
    return {
        "totalCount": sum(v["count"] for v in by_status.values()),
        "totalValue": round(sum(v["totalValue"] for v in by_status.values()), 2),
        "paidValue": round(by_status.get("paid", {}).get("totalValue", 0), 2),
        "outstandingValue": round(
            sum(
                by_status.get(s, {}).get("totalValue", 0)
                for s in ("draft", "sent", "overdue")
            ),
            2,
        ),
        "byStatus": by_status,
    }
