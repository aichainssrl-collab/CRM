"""
Helper CRUD generico per Firestore async.
Gestisce: paginazione cursor-based, soft delete, timestamp automatici.
"""
from datetime import datetime, timezone
from typing import Optional
import uuid
from google.cloud.firestore_v1 import FieldFilter
from app.firebase_admin import db


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def new_id() -> str:
    return str(uuid.uuid4())


def _snap_to_dict(snap) -> dict:
    return {"id": snap.id, **snap.to_dict()}


async def create_document(
    collection: str,
    data: dict,
    doc_id: str = None,
) -> dict:
    doc_id = doc_id or new_id()
    now = utcnow()
    payload = {
        **data,
        "createdAt": now,
        "updatedAt": now,
        "deletedAt": None,
    }
    await db.collection(collection).document(doc_id).set(payload)
    return {"id": doc_id, **payload}


async def update_document(
    collection: str,
    doc_id: str,
    data: dict,
) -> Optional[dict]:
    now = utcnow()
    update_payload = {**data, "updatedAt": now}
    ref = db.collection(collection).document(doc_id)
    await ref.update(update_payload)
    snap = await ref.get()
    return _snap_to_dict(snap) if snap.exists else None


async def soft_delete(collection: str, doc_id: str) -> None:
    now = utcnow()
    await db.collection(collection).document(doc_id).update({
        "deletedAt": now,
        "updatedAt": now,
    })


async def get_document(
    collection: str,
    doc_id: str,
    include_deleted: bool = False,
) -> Optional[dict]:
    snap = await db.collection(collection).document(doc_id).get()
    if not snap.exists:
        return None
    doc = _snap_to_dict(snap)
    if not include_deleted and doc.get("deletedAt"):
        return None
    return doc


async def append_to_subcollection(
    parent_collection: str,
    parent_id: str,
    sub_collection: str,
    data: dict,
    doc_id: str = None,
) -> dict:
    """Aggiunge documento a una subcollection — usato per activities (append-only)."""
    doc_id = doc_id or new_id()
    now = utcnow()
    payload = {**data, "createdAt": now}
    ref = (
        db.collection(parent_collection)
        .document(parent_id)
        .collection(sub_collection)
        .document(doc_id)
    )
    await ref.set(payload)
    return {"id": doc_id, **payload}


async def list_subcollection(
    parent_collection: str,
    parent_id: str,
    sub_collection: str,
    order_by: str = "createdAt",
    descending: bool = True,
    limit: int = 100,
) -> list[dict]:
    direction = "DESCENDING" if descending else "ASCENDING"
    query = (
        db.collection(parent_collection)
        .document(parent_id)
        .collection(sub_collection)
        .order_by(order_by, direction=direction)
        .limit(limit)
    )
    results = []
    async for snap in query.stream():
        results.append(_snap_to_dict(snap))
    return results


async def list_collection(
    collection: str,
    filters: list[tuple] = None,
    order_by: str = "createdAt",
    descending: bool = True,
    limit: int = 20,
    last_doc_id: str = None,
    include_deleted: bool = False,
) -> list[dict]:
    """
    Elenca documenti con paginazione cursor-based.
    filters: lista di tuple (campo, operatore, valore)
    """
    query = db.collection(collection)

    if not include_deleted:
        query = query.where(filter=FieldFilter("deletedAt", "==", None))

    if filters:
        for campo, op, valore in filters:
            query = query.where(filter=FieldFilter(campo, op, valore))

    direction = "DESCENDING" if descending else "ASCENDING"
    query = query.order_by(order_by, direction=direction)

    if last_doc_id:
        last_snap = await db.collection(collection).document(last_doc_id).get()
        if last_snap.exists:
            query = query.start_after(last_snap)

    query = query.limit(limit)

    results = []
    async for snap in query.stream():
        results.append(_snap_to_dict(snap))
    return results


async def increment_field(collection: str, doc_id: str, field: str, amount: int = 1) -> None:
    from google.cloud.firestore_v1 import Increment
    await db.collection(collection).document(doc_id).update({
        field: Increment(amount),
        "updatedAt": utcnow(),
    })
