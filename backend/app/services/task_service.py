from typing import Optional
from app.schemas.task import TaskCreate, TaskUpdate
from app.services.db_service import db, utcnow, new_id
from app.services.activity_service import append_activity
from pymongo import DESCENDING


async def create_task(lead_id: str, data: TaskCreate, created_by: str) -> dict:
    task_id = new_id()
    now = utcnow()
    payload = {
        "_id": task_id,
        "leadId": lead_id,
        **data.model_dump(),
        "status": "open",
        "createdBy": created_by,
        "createdAt": now,
        "updatedAt": now,
        "deletedAt": None,
    }
    await db["tasks"].insert_one(payload)
    await db["leads"].update_one(
        {"_id": lead_id},
        {"$inc": {"taskCount": 1}, "$set": {"updatedAt": now}},
    )
    doc = dict(payload)
    doc["id"] = doc.pop("_id")
    return doc


async def list_tasks(lead_id: str, status: str = None) -> list[dict]:
    query = {"leadId": lead_id, "deletedAt": None}
    if status:
        query["status"] = status
    cursor = db["tasks"].find(query).sort("createdAt", DESCENDING)
    docs = await cursor.to_list(length=200)
    return [{**{k: v for k, v in d.items() if k != "_id"}, "id": d["_id"]} for d in docs]


async def get_task(lead_id: str, task_id: str) -> Optional[dict]:
    doc = await db["tasks"].find_one({"_id": task_id, "leadId": lead_id, "deletedAt": None})
    if not doc:
        return None
    doc = dict(doc)
    doc["id"] = doc.pop("_id")
    return doc


async def update_task(lead_id: str, task_id: str, data: TaskUpdate, updated_by: str) -> Optional[dict]:
    update_data = {**data.model_dump(exclude_unset=True), "updatedAt": utcnow()}
    doc = await db["tasks"].find_one_and_update(
        {"_id": task_id, "leadId": lead_id, "deletedAt": None},
        {"$set": update_data},
        return_document=True,
    )
    if not doc:
        return None
    doc = dict(doc)
    doc["id"] = doc.pop("_id")
    return doc


async def complete_task(lead_id: str, task_id: str, completed_by: str) -> Optional[dict]:
    now = utcnow()
    doc = await db["tasks"].find_one_and_update(
        {"_id": task_id, "leadId": lead_id, "deletedAt": None},
        {"$set": {"status": "completed", "completedAt": now, "updatedAt": now}},
        return_document=True,
    )
    if not doc:
        return None
    await append_activity(lead_id, {
        "type": "task_completed",
        "title": "Task completato",
        "userId": completed_by,
        "metadata": {"taskId": task_id},
    })
    doc = dict(doc)
    doc["id"] = doc.pop("_id")
    return doc


async def delete_task(lead_id: str, task_id: str) -> None:
    now = utcnow()
    await db["tasks"].update_one(
        {"_id": task_id, "leadId": lead_id},
        {"$set": {"deletedAt": now, "updatedAt": now}},
    )
