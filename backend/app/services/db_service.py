"""
Helper CRUD generico per MongoDB async (Motor).
Gestisce: paginazione cursor-based, soft delete, timestamp automatici.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING, DESCENDING
from app.config import settings

client = AsyncIOMotorClient(settings.MONGODB_URI)
db = client[settings.MONGODB_DB_NAME]


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def new_id() -> str:
    return str(uuid.uuid4())


def _to_dict(doc: dict) -> dict:
    """Normalizza _id → id."""
    if doc is None:
        return None
    doc = dict(doc)
    if "_id" in doc:
        doc["id"] = doc.pop("_id")
    return doc


async def create_document(
    collection: str,
    data: dict,
    doc_id: str = None,
) -> dict:
    doc_id = doc_id or new_id()
    now = utcnow()
    payload = {
        "_id": doc_id,
        **data,
        "createdAt": now,
        "updatedAt": now,
        "deletedAt": None,
    }
    await db[collection].insert_one(payload)
    return _to_dict(payload)


async def get_document(collection: str, doc_id: str) -> Optional[Dict[str, Any]]:
    doc = await db[collection].find_one({"_id": doc_id, "deletedAt": None})
    return _to_dict(doc) if doc else None


async def update_document(
    collection: str,
    doc_id: str,
    data: dict,
) -> Optional[dict]:
    now = utcnow()
    update_payload = {**data, "updatedAt": now}
    doc = await db[collection].find_one_and_update(
        {"_id": doc_id, "deletedAt": None},
        {"$set": update_payload},
        return_document=True,
    )
    return _to_dict(doc) if doc else None


async def soft_delete(collection: str, doc_id: str) -> None:
    now = utcnow()
    await db[collection].update_one(
        {"_id": doc_id},
        {"$set": {"deletedAt": now, "updatedAt": now}},
    )


async def list_collection(
    collection: str,
    filters: list = None,
    order_by: str = "createdAt",
    descending: bool = True,
    limit: int = 20,
    last_doc_id: str = None,
    include_deleted: bool = False,
) -> list[dict]:
    query: Dict[str, Any] = {}

    if not include_deleted:
        query["deletedAt"] = None

    if filters:
        for campo, op, valore in filters:
            if op == "==":
                query[campo] = valore
            elif op == ">=":
                query.setdefault(campo, {})["$gte"] = valore
            elif op == "<=":
                query.setdefault(campo, {})["$lte"] = valore
            elif op == "in":
                query[campo] = {"$in": valore}
            elif op == "!=":
                query[campo] = {"$ne": valore}

    direction = DESCENDING if descending else ASCENDING
    cursor = db[collection].find(query).sort(order_by, direction)

    if last_doc_id:
        last = await db[collection].find_one({"_id": last_doc_id})
        if last:
            pivot = last.get(order_by)
            if pivot is not None:
                op = "$lt" if descending else "$gt"
                cursor = db[collection].find(
                    {**query, order_by: {op: pivot}}
                ).sort(order_by, direction)

    cursor = cursor.limit(limit)
    docs = await cursor.to_list(length=limit)
    return [_to_dict(d) for d in docs]


async def increment_field(collection: str, doc_id: str, field: str, amount: int = 1) -> None:
    await db[collection].update_one(
        {"_id": doc_id},
        {"$inc": {field: amount}, "$set": {"updatedAt": utcnow()}},
    )


# ── Subcollection helpers (MongoDB: collezioni separate con leadId) ──────────

async def append_to_subcollection(
    parent_collection: str,
    parent_id: str,
    sub_collection: str,
    data: dict,
    doc_id: str = None,
) -> dict:
    doc_id = doc_id or new_id()
    now = utcnow()
    payload = {
        "_id": doc_id,
        f"{parent_collection[:-1]}Id": parent_id,  # e.g. leads → leadId
        **data,
        "createdAt": now,
    }
    await db[sub_collection].insert_one(payload)
    return _to_dict(payload)


async def list_subcollection(
    parent_collection: str,
    parent_id: str,
    sub_collection: str,
    order_by: str = "createdAt",
    descending: bool = True,
    limit: int = 100,
) -> list[dict]:
    parent_id_field = f"{parent_collection[:-1]}Id"  # leads → leadId
    direction = DESCENDING if descending else ASCENDING
    cursor = (
        db[sub_collection]
        .find({parent_id_field: parent_id, "deletedAt": None})
        .sort(order_by, direction)
        .limit(limit)
    )
    docs = await cursor.to_list(length=limit)
    return [_to_dict(d) for d in docs]
