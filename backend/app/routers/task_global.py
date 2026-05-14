from fastapi import APIRouter, Depends, Query
from typing import Optional
from datetime import datetime, timezone
from google.cloud.firestore_v1 import FieldFilter
from app.deps import require_sales, UserRecord
from app.firebase_admin import db

router = APIRouter()


@router.get("")
async def list_all_tasks(
    status: Optional[str] = Query(None, description="open | completed"),
    due_before: Optional[str] = Query(None, description="ISO date string (es. 2025-12-31)"),
    limit: int = Query(50, ge=1, le=200),
    user: UserRecord = Depends(require_sales),
):
    query = (
        db.collection_group("tasks")
        .where(filter=FieldFilter("assignedTo", "==", user.uid))
        .where(filter=FieldFilter("deletedAt", "==", None))
    )

    if status:
        query = query.where(filter=FieldFilter("status", "==", status))

    if due_before:
        due_dt = datetime.fromisoformat(due_before).replace(tzinfo=timezone.utc)
        query = query.where(filter=FieldFilter("dueDate", "<=", due_dt))

    query = query.order_by("dueDate", direction="ASCENDING").limit(limit)

    results = []
    async for snap in query.stream():
        results.append({"id": snap.id, **snap.to_dict()})

    return results
