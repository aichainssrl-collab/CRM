"""
Proposals / quotes service — commercial offers with product line items.
"""
from typing import Optional
from app.services.db_service import db, new_id, utcnow, _to_dict
import logging

logger = logging.getLogger(__name__)

STATUSES = ("draft", "sent", "accepted", "rejected", "expired")


DEFAULT_TAX_RATE = 22.0


def compute_totals(items: list[dict], tax_rate: float = DEFAULT_TAX_RATE) -> dict:
    """Normalize line items and compute subtotal/tax/total."""
    normalized = []
    subtotal = 0.0
    for raw in items or []:
        qty = float(raw.get("quantity", 1) or 1)
        unit = float(raw.get("unitPrice", 0) or 0)
        line_total = round(qty * unit, 2)
        subtotal += line_total
        normalized.append(
            {
                "productId": raw.get("productId"),
                "name": raw.get("name", ""),
                "description": raw.get("description", ""),
                "quantity": qty,
                "unitPrice": unit,
                "total": line_total,
            }
        )
    subtotal = round(subtotal, 2)
    if tax_rate is None or tax_rate == "":
        tax_rate = DEFAULT_TAX_RATE
    tax_rate = float(tax_rate)
    tax_amount = round(subtotal * tax_rate / 100.0, 2)
    total = round(subtotal + tax_amount, 2)
    return {
        "items": normalized,
        "subtotal": subtotal,
        "taxRate": tax_rate,
        "taxAmount": tax_amount,
        "total": total,
    }


async def _next_number() -> str:
    year = utcnow().year
    count = await db["proposals"].count_documents({"deletedAt": None})
    return f"PROP-{year}-{count + 1:04d}"


async def create_proposal(data: dict, created_by: str) -> dict:
    now = utcnow()
    totals = compute_totals(data.get("items", []), data.get("taxRate", DEFAULT_TAX_RATE))
    doc = {
        "_id": new_id(),
        "number": await _next_number(),
        "title": data["title"],
        "clientName": data.get("clientName", ""),
        "clientEmail": data.get("clientEmail", ""),
        "leadId": data.get("leadId"),
        "dealId": data.get("dealId"),
        "status": "draft",
        **totals,
        "currency": data.get("currency", "EUR"),
        "validUntil": data.get("validUntil"),
        "notes": data.get("notes", ""),
        "sentAt": None,
        "acceptedAt": None,
        "rejectedAt": None,
        "createdBy": created_by,
        "createdAt": now,
        "updatedAt": now,
        "deletedAt": None,
    }
    await db["proposals"].insert_one(doc)
    return _to_dict(doc)


async def list_proposals(status: Optional[str] = None) -> list[dict]:
    query: dict = {"deletedAt": None}
    if status:
        query["status"] = status
    cursor = db["proposals"].find(query).sort("createdAt", -1)
    docs = await cursor.to_list(length=200)
    return [_to_dict(d) for d in docs]


async def get_proposal(proposal_id: str) -> Optional[dict]:
    doc = await db["proposals"].find_one({"_id": proposal_id, "deletedAt": None})
    return _to_dict(doc) if doc else None


async def update_proposal(proposal_id: str, data: dict) -> Optional[dict]:
    # Recompute totals when items or taxRate change
    if "items" in data or "taxRate" in data:
        current = await get_proposal(proposal_id)
        if not current:
            return None
        items = data.get("items", current.get("items", []))
        tax_rate = data.get("taxRate", current.get("taxRate", DEFAULT_TAX_RATE))
        data.update(compute_totals(items, tax_rate))
    data["updatedAt"] = utcnow()
    doc = await db["proposals"].find_one_and_update(
        {"_id": proposal_id, "deletedAt": None},
        {"$set": data},
        return_document=True,
    )
    return _to_dict(doc) if doc else None


async def delete_proposal(proposal_id: str) -> bool:
    now = utcnow()
    result = await db["proposals"].update_one(
        {"_id": proposal_id, "deletedAt": None},
        {"$set": {"deletedAt": now, "updatedAt": now}},
    )
    return result.modified_count > 0


async def mark_sent(proposal_id: str) -> Optional[dict]:
    now = utcnow()
    doc = await db["proposals"].find_one_and_update(
        {"_id": proposal_id, "deletedAt": None, "status": "draft"},
        {"$set": {"status": "sent", "sentAt": now, "updatedAt": now}},
        return_document=True,
    )
    return _to_dict(doc) if doc else None


async def mark_accepted(proposal_id: str) -> Optional[dict]:
    now = utcnow()
    doc = await db["proposals"].find_one_and_update(
        {"_id": proposal_id, "deletedAt": None, "status": {"$in": ["draft", "sent"]}},
        {"$set": {"status": "accepted", "acceptedAt": now, "updatedAt": now}},
        return_document=True,
    )
    return _to_dict(doc) if doc else None


async def mark_rejected(proposal_id: str) -> Optional[dict]:
    now = utcnow()
    doc = await db["proposals"].find_one_and_update(
        {"_id": proposal_id, "deletedAt": None, "status": {"$in": ["draft", "sent"]}},
        {"$set": {"status": "rejected", "rejectedAt": now, "updatedAt": now}},
        return_document=True,
    )
    return _to_dict(doc) if doc else None


async def proposal_stats() -> dict:
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
    rows = await db["proposals"].aggregate(pipeline).to_list(length=20)
    by_status = {r["_id"]: {"count": r["count"], "totalValue": r["totalValue"]} for r in rows}
    total_count = sum(v["count"] for v in by_status.values())
    total_value = sum(v["totalValue"] for v in by_status.values())
    return {
        "totalCount": total_count,
        "totalValue": round(total_value, 2),
        "byStatus": by_status,
    }
