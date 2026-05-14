from typing import Optional
from app.schemas.task import TaskCreate, TaskUpdate
from app.services.db_service import (
    create_document, update_document, get_document,
    list_subcollection, soft_delete, utcnow, new_id,
)
from app.services.activity_service import append_activity
from app.firebase_admin import db


async def create_task(lead_id: str, data: TaskCreate, created_by: str) -> dict:
    task_id = new_id()
    payload = {
        **data.model_dump(),
        "leadId": lead_id,
        "status": "open",
        "createdBy": created_by,
    }
    ref = db.collection("leads").document(lead_id).collection("tasks").document(task_id)
    from app.services.db_service import utcnow
    now = utcnow()
    full_payload = {**payload, "createdAt": now, "updatedAt": now, "deletedAt": None}
    await ref.set(full_payload)

    await db.collection("leads").document(lead_id).update({
        "taskCount": _increment(1),
    })

    return {"id": task_id, **full_payload}


async def list_tasks(lead_id: str, status: str = None) -> list[dict]:
    query = (
        db.collection("leads")
        .document(lead_id)
        .collection("tasks")
        .order_by("createdAt", direction="DESCENDING")
    )
    results = []
    async for snap in query.stream():
        doc = {"id": snap.id, **snap.to_dict()}
        if doc.get("deletedAt"):
            continue
        if status and doc.get("status") != status:
            continue
        results.append(doc)
    return results


async def get_task(lead_id: str, task_id: str) -> Optional[dict]:
    snap = await (
        db.collection("leads")
        .document(lead_id)
        .collection("tasks")
        .document(task_id)
        .get()
    )
    if not snap.exists:
        return None
    doc = {"id": snap.id, **snap.to_dict()}
    return None if doc.get("deletedAt") else doc


async def update_task(lead_id: str, task_id: str, data: TaskUpdate, updated_by: str) -> Optional[dict]:
    update_data = data.model_dump(exclude_unset=True)
    update_data["updatedAt"] = utcnow()
    ref = db.collection("leads").document(lead_id).collection("tasks").document(task_id)
    await ref.update(update_data)
    snap = await ref.get()
    return {"id": snap.id, **snap.to_dict()} if snap.exists else None


async def complete_task(lead_id: str, task_id: str, completed_by: str) -> Optional[dict]:
    now = utcnow()
    ref = db.collection("leads").document(lead_id).collection("tasks").document(task_id)
    await ref.update({"status": "completed", "completedAt": now, "updatedAt": now})
    await append_activity(lead_id, {
        "type": "task_completed",
        "title": "Task completato",
        "userId": completed_by,
        "metadata": {"taskId": task_id},
    })
    snap = await ref.get()
    return {"id": snap.id, **snap.to_dict()} if snap.exists else None


async def delete_task(lead_id: str, task_id: str) -> None:
    now = utcnow()
    await (
        db.collection("leads")
        .document(lead_id)
        .collection("tasks")
        .document(task_id)
        .update({"deletedAt": now, "updatedAt": now})
    )


def _increment(amount: int):
    from google.cloud.firestore_v1 import Increment
    return Increment(amount)
