"""
Product catalog service — manage products and services.
"""
from typing import Optional
from app.services.db_service import db, new_id, utcnow, _to_dict
import logging

logger = logging.getLogger(__name__)


async def create_product(data: dict, created_by: str) -> dict:
    now = utcnow()
    doc = {
        "_id": new_id(),
        "name": data["name"],
        "description": data.get("description", ""),
        "sku": data.get("sku", ""),
        "category": data.get("category", ""),  # software | service | consulting | other
        "price": float(data.get("price", 0)),
        "currency": data.get("currency", "EUR"),
        "billingModel": data.get("billingModel", "one-time"),  # one-time | monthly | yearly
        "isActive": data.get("isActive", True),
        "createdBy": created_by,
        "createdAt": now,
        "updatedAt": now,
        "deletedAt": None,
    }
    await db["products"].insert_one(doc)
    return _to_dict(doc)


async def list_products(active_only: bool = True) -> list[dict]:
    query = {"deletedAt": None}
    if active_only:
        query["isActive"] = True
    cursor = db["products"].find(query).sort("name", 1)
    docs = await cursor.to_list(length=100)
    return [_to_dict(d) for d in docs]


async def get_product(product_id: str) -> Optional[dict]:
    doc = await db["products"].find_one({"_id": product_id, "deletedAt": None})
    return _to_dict(doc) if doc else None


async def update_product(product_id: str, data: dict) -> Optional[dict]:
    data["updatedAt"] = utcnow()
    doc = await db["products"].find_one_and_update(
        {"_id": product_id, "deletedAt": None},
        {"$set": data},
        return_document=True,
    )
    return _to_dict(doc) if doc else None


async def delete_product(product_id: str) -> bool:
    now = utcnow()
    result = await db["products"].update_one(
        {"_id": product_id, "deletedAt": None},
        {"$set": {"deletedAt": now, "updatedAt": now}},
    )
    return result.modified_count > 0