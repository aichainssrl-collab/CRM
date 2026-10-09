"""
Generated document registry — versioned PDF snapshots for proposals/invoices.

Append-only history of what was rendered and sent. Content checksum detects
regeneration of identical bytes (no new version) vs real content change.
"""
import hashlib
from typing import Optional

from app.services.db_service import db, new_id, utcnow, _to_dict


def checksum(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


async def record_pdf(
    *,
    parent_type: str,
    parent_id: str,
    data: bytes,
    locale: str = "it",
    generated_by: str = "",
    filename: str = "",
) -> dict:
    """Insert a new version if content changed; else return the latest matching doc."""
    digest = checksum(data)
    latest = await db["documents"].find_one(
        {
            "parentType": parent_type,
            "parentId": parent_id,
            "kind": "pdf",
            "locale": locale,
            "checksum": digest,
        },
        sort=[("version", -1)],
    )
    if latest:
        return _to_dict(latest)

    prev = await db["documents"].find_one(
        {"parentType": parent_type, "parentId": parent_id, "kind": "pdf", "locale": locale},
        sort=[("version", -1)],
    )
    version = int(prev.get("version") or 0) + 1 if prev else 1
    now = utcnow()
    doc = {
        "_id": new_id(),
        "parentType": parent_type,
        "parentId": parent_id,
        "kind": "pdf",
        "locale": locale,
        "version": version,
        "checksum": digest,
        "filename": filename or f"{parent_id}.pdf",
        "size": len(data),
        "generatedBy": generated_by,
        "createdAt": now,
        "updatedAt": now,
        "deletedAt": None,
    }
    await db["documents"].insert_one(doc)
    return _to_dict(doc)


async def latest_for(
    parent_type: str,
    parent_id: str,
    locale: Optional[str] = None,
) -> Optional[dict]:
    query: dict = {
        "parentType": parent_type,
        "parentId": parent_id,
        "deletedAt": None,
    }
    if locale:
        query["locale"] = locale
    doc = await db["documents"].find_one(query, sort=[("version", -1)])
    return _to_dict(doc) if doc else None


async def list_for(parent_type: str, parent_id: str) -> list[dict]:
    cursor = (
        db["documents"]
        .find({"parentType": parent_type, "parentId": parent_id, "deletedAt": None})
        .sort("version", -1)
    )
    docs = await cursor.to_list(length=50)
    return [_to_dict(d) for d in docs]
