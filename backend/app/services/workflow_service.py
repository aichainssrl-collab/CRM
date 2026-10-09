"""
Workflow automation — rules that fire actions when a trigger matches a condition.
"""
from typing import Any, Optional
from app.services.db_service import db, new_id, utcnow, _to_dict
import logging

logger = logging.getLogger(__name__)

TRIGGERS = ("lead_created", "deal_stage_changed", "proposal_accepted", "task_completed", "manual")

ACTION_TYPES = ("create_task", "add_tag", "update_lead_status", "send_notification", "send_email")

OPS = ("eq", "ne", "contains", "gte", "lte", "in")


def evaluate_condition(entity: dict, cond: dict) -> bool:
    field = cond.get("field", "")
    op = cond.get("op", "eq")
    expected = cond.get("value")
    actual = entity.get(field) if entity else None

    if op == "eq":
        return actual == expected
    if op == "ne":
        return actual != expected
    if op == "contains":
        if isinstance(actual, list):
            return expected in actual
        return expected is not None and str(expected).lower() in str(actual or "").lower()
    if op == "gte":
        try:
            return float(actual) >= float(expected)
        except (TypeError, ValueError):
            return False
    if op == "lte":
        try:
            return float(actual) <= float(expected)
        except (TypeError, ValueError):
            return False
    if op == "in":
        if not isinstance(expected, (list, tuple)):
            return False
        return actual in expected
    return False


def matches_conditions(entity: dict, conditions: list[dict]) -> bool:
    if not conditions:
        return True
    return all(evaluate_condition(entity, c) for c in conditions)


def _extract_entity_fields(trigger: str, entity: dict) -> dict:
    """Normalize incoming entity into a flat dict for condition evaluation."""
    if not entity:
        return {}
    return {
        "id": entity.get("id") or entity.get("_id"),
        "status": entity.get("status"),
        "stage": entity.get("stage"),
        "source": entity.get("source"),
        "industry": entity.get("industry"),
        "score": entity.get("score"),
        "tags": entity.get("tags") or [],
        "email": entity.get("email") or entity.get("clientEmail"),
        "company": entity.get("company") or entity.get("clientName"),
        "assignedTo": entity.get("assignedTo"),
        "title": entity.get("title") or entity.get("name"),
        "trigger": trigger,
    }


async def execute_action(action: dict, entity: dict, run_by: str) -> dict:
    """Execute a single workflow action. Returns result summary."""
    action_type = action.get("type")
    target_id = entity.get("id") or entity.get("_id")
    now = utcnow()

    if action_type == "create_task":
        doc = {
            "_id": new_id(),
            "leadId": target_id,
            "title": action.get("title") or f"Workflow task: {entity.get('title') or entity.get('name') or target_id}",
            "description": action.get("description", ""),
            "dueDate": action.get("dueDate"),
            "priority": action.get("priority", "medium"),
            "status": "pending",
            "assignedTo": action.get("assignedTo") or entity.get("assignedTo") or run_by,
            "createdBy": run_by,
            "createdAt": now,
            "updatedAt": now,
            "completedAt": None,
            "deletedAt": None,
        }
        await db["tasks"].insert_one(doc)
        return {"type": action_type, "ok": True, "taskId": doc["_id"]}

    if action_type == "add_tag":
        tag = action.get("tag", "")
        if not tag or not target_id:
            return {"type": action_type, "ok": False, "error": "missing tag/target"}
        # leads and deals both support tags
        coll = "leads" if entity.get("trigger") == "lead_created" or "status" in entity else "deals"
        if entity.get("stage") is not None:
            coll = "deals"
        await db[coll].update_one(
            {"_id": target_id},
            {"$addToSet": {"tags": tag}, "$set": {"updatedAt": now}},
        )
        return {"type": action_type, "ok": True, "tag": tag, "collection": coll}

    if action_type == "update_lead_status":
        new_status = action.get("status", "")
        if not new_status or not target_id:
            return {"type": action_type, "ok": False, "error": "missing status/target"}
        await db["leads"].update_one(
            {"_id": target_id},
            {"$set": {"status": new_status, "updatedAt": now}},
        )
        return {"type": action_type, "ok": True, "status": new_status}

    if action_type == "send_notification":
        doc = {
            "_id": new_id(),
            "userId": action.get("userId") or entity.get("assignedTo") or run_by,
            "title": action.get("title") or "Workflow",
            "body": action.get("body") or f"Triggered by {entity.get('title') or target_id}",
            "type": "workflow",
            "read": False,
            "createdAt": now,
        }
        await db["notifications"].insert_one(doc)
        return {"type": action_type, "ok": True, "notificationId": doc["_id"]}

    if action_type == "send_email":
        # Placeholder: log only — wire to Resend when template is configured
        logger.info(
            f"[WORKFLOW EMAIL] to={action.get('to') or entity.get('email')} subject={action.get('subject')}"
        )
        return {"type": action_type, "ok": True, "mock": True}

    return {"type": action_type, "ok": False, "error": "unknown action"}


async def create_workflow(data: dict, created_by: str) -> dict:
    now = utcnow()
    doc = {
        "_id": new_id(),
        "name": data["name"],
        "description": data.get("description", ""),
        "trigger": data.get("trigger", "manual"),
        "conditions": data.get("conditions") or [],
        "actions": data.get("actions") or [],
        "isActive": data.get("isActive", False),
        "runCount": 0,
        "lastRunAt": None,
        "createdBy": created_by,
        "createdAt": now,
        "updatedAt": now,
        "deletedAt": None,
    }
    await db["workflows"].insert_one(doc)
    return _to_dict(doc)


async def list_workflows(only_active: bool = False) -> list[dict]:
    query: dict = {"deletedAt": None}
    if only_active:
        query["isActive"] = True
    cursor = db["workflows"].find(query).sort("createdAt", -1)
    docs = await cursor.to_list(length=100)
    return [_to_dict(d) for d in docs]


async def get_workflow(workflow_id: str) -> Optional[dict]:
    doc = await db["workflows"].find_one({"_id": workflow_id, "deletedAt": None})
    return _to_dict(doc) if doc else None


async def update_workflow(workflow_id: str, data: dict) -> Optional[dict]:
    data["updatedAt"] = utcnow()
    doc = await db["workflows"].find_one_and_update(
        {"_id": workflow_id, "deletedAt": None},
        {"$set": data},
        return_document=True,
    )
    return _to_dict(doc) if doc else None


async def delete_workflow(workflow_id: str) -> bool:
    now = utcnow()
    result = await db["workflows"].update_one(
        {"_id": workflow_id, "deletedAt": None},
        {"$set": {"deletedAt": now, "updatedAt": now}},
    )
    return result.modified_count > 0


async def toggle_workflow(workflow_id: str) -> Optional[dict]:
    wf = await get_workflow(workflow_id)
    if not wf:
        return None
    return await update_workflow(workflow_id, {"isActive": not wf.get("isActive", False)})


async def run_workflows(trigger: str, entity: dict, run_by: str = "system") -> list[dict]:
    """Run all active workflows matching this trigger. Returns run results."""
    if trigger not in TRIGGERS:
        return []
    fields = _extract_entity_fields(trigger, entity)
    cursor = db["workflows"].find({"deletedAt": None, "isActive": True, "trigger": trigger})
    workflows = await cursor.to_list(length=100)

    results = []
    for wf in workflows:
        if not matches_conditions(fields, wf.get("conditions") or []):
            continue
        action_results = []
        for action in wf.get("actions") or []:
            try:
                action_results.append(await execute_action(action, fields, run_by))
            except Exception as exc:
                logger.error(f"Workflow {wf['_id']} action failed: {exc}")
                action_results.append({"type": action.get("type"), "ok": False, "error": str(exc)})

        await db["workflows"].update_one(
            {"_id": wf["_id"]},
            {
                "$inc": {"runCount": 1},
                "$set": {"lastRunAt": utcnow(), "updatedAt": utcnow()},
            },
        )
        results.append(
            {
                "workflowId": wf["_id"],
                "name": wf.get("name"),
                "actions": action_results,
            }
        )
    return results


async def workflow_stats() -> dict:
    total = await db["workflows"].count_documents({"deletedAt": None})
    active = await db["workflows"].count_documents({"deletedAt": None, "isActive": True})
    cursor = db["workflows"].find({"deletedAt": None}).sort("runCount", -1)
    top = await cursor.to_list(length=5)
    return {
        "total": total,
        "active": active,
        "topRuns": [
            {"id": _to_dict(w).get("id"), "name": w.get("name"), "runCount": w.get("runCount", 0)}
            for w in top
        ],
    }
