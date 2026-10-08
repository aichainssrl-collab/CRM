from fastapi import APIRouter, Depends, Query
from typing import Optional
from datetime import datetime, timezone
from app.deps import require_sales, UserRecord
from app.services.db_service import db
from pymongo import ASCENDING

router = APIRouter()


@router.get("")
async def list_all_tasks(
    status: Optional[str] = Query(None, description="open | completed"),
    due_before: Optional[str] = Query(None, description="ISO date string (es. 2025-12-31)"),
    limit: int = Query(50, ge=1, le=200),
    user: UserRecord = Depends(require_sales),
):
    query = {"assignedTo": user.uid, "deletedAt": None}

    if status:
        query["status"] = status

    if due_before:
        due_dt = datetime.fromisoformat(due_before).replace(tzinfo=timezone.utc)
        query["dueDate"] = {"$lte": due_dt}

    cursor = db["tasks"].find(query).sort("dueDate", ASCENDING).limit(limit)
    results = []
    async for doc in cursor:
        doc = dict(doc)
        doc["id"] = doc.pop("_id")
        results.append(doc)
    return results
