"""
Agent goals — obiettivi tracciabili con stato e progresso.

Quando un'azione CRM completa un goal, lo stato si aggiorna da solo
(opzionale anche update manuale da UI/API).
Collezione: agent_goals
"""
from __future__ import annotations

import logging
from typing import Any, Optional

from app.services.db_service import db, new_id, utcnow

logger = logging.getLogger(__name__)

# Tool → contributi di progresso ai goal (metric name)
# Ogni azione riuscita fa avanzare anche i goal generali.
TOOL_GOAL_IMPACT: dict[str, dict[str, int]] = {
    "create_lead": {"leads_captured": 1, "actions_ok": 1, "tool_calls": 1},
    "update_lead": {"leads_maintained": 1, "actions_ok": 1, "tool_calls": 1},
    "create_task": {"tasks_created": 1, "actions_ok": 1, "tool_calls": 1},
    "complete_task": {"tasks_completed": 1, "actions_ok": 1, "tool_calls": 1},
    "schedule_followup": {"tasks_created": 1, "actions_ok": 1, "tool_calls": 1},
    "create_deal": {"deals_created": 1, "actions_ok": 1, "tool_calls": 1},
    "move_deal_stage": {"deals_advanced": 1, "actions_ok": 1, "tool_calls": 1},
    "send_email": {"emails_sent": 1, "actions_ok": 1, "tool_calls": 1},
    "draft_email": {"emails_drafted": 1, "actions_ok": 1, "tool_calls": 1},
    "send_proposal": {"proposals_sent": 1, "deals_advanced": 1, "actions_ok": 1, "tool_calls": 1},
    "mark_proposal": {"proposals_advanced": 1, "deals_advanced": 1, "actions_ok": 1, "tool_calls": 1},
    "create_invoice": {"invoices_created": 1, "actions_ok": 1, "tool_calls": 1},
    "mark_invoice": {"invoices_updated": 1, "actions_ok": 1, "tool_calls": 1},
    "book_demo": {"demos_booked": 1, "deals_advanced": 1, "actions_ok": 1, "tool_calls": 1},
    "workflow_inbound_lead": {"leads_captured": 1, "tasks_created": 1, "actions_ok": 1, "tool_calls": 1},
    "generate_report": {"reports_generated": 1, "actions_ok": 1, "tool_calls": 1},
    "export_csv": {"exports_created": 1, "actions_ok": 1, "tool_calls": 1},
    "crm_summary": {"reviews_done": 1, "tool_calls": 1},
    "crm_kpi": {"reviews_done": 1, "tool_calls": 1},
    "search_knowledge": {"tool_calls": 1},
    "find_lead": {"tool_calls": 1},
    "list_leads": {"tool_calls": 1},
    "list_tasks": {"tool_calls": 1},
    "list_deals": {"tool_calls": 1},
}

DEFAULT_GOALS: list[dict[str, Any]] = [
    {
        "key": "respond_fast",
        "title": "Rispondere in modo rapido e preciso",
        "description": "Domande CRM chiare, senza inventare dati.",
        "metric": "responses_ok",
        "target": 50,
        "status": "in_progress",
    },
    {
        "key": "execute_actions",
        "title": "Eseguire azioni operative sul CRM",
        "description": "Lead, task, deal, fatture, email eseguite correttamente.",
        "metric": "actions_ok",
        "target": 30,
        "status": "in_progress",
    },
    {
        "key": "no_fake_data",
        "title": "Non inventare dati",
        "description": "Usare sempre i tool; zero dati fabricati.",
        "metric": "tool_calls",
        "target": 100,
        "status": "in_progress",
    },
    {
        "key": "drive_followups",
        "title": "Guidare follow-up e chiusura opportunità",
        "description": "Task, demo, deal avanzati verso chiusura.",
        "metric": "deals_advanced",
        "target": 10,
        "status": "in_progress",
    },
]


def _to_dict(doc: dict | None) -> dict | None:
    if not doc:
        return None
    d = dict(doc)
    d["id"] = d.pop("_id", None)
    return d


async def ensure_default_goals() -> None:
    col = db["agent_goals"]
    for g in DEFAULT_GOALS:
        existing = await col.find_one({"key": g["key"], "deletedAt": None})
        if not existing:
            now = utcnow()
            await col.insert_one({
                "_id": new_id(),
                **g,
                "progress": 0,
                "isDefault": True,
                "createdAt": now,
                "updatedAt": now,
                "deletedAt": None,
            })


async def list_goals() -> list[dict]:
    await ensure_default_goals()
    cursor = db["agent_goals"].find({"deletedAt": None}).sort("createdAt", 1)
    out = []
    async for d in cursor:
        item = _to_dict(d)
        target = max(int(item.get("target") or 1), 1)
        progress = int(item.get("progress") or 0)
        item["percent"] = min(100, round(progress / target * 100))
        if item.get("status") == "completed" or progress >= target:
            item["status"] = "completed"
            item["percent"] = 100
        out.append(item)
    return out


async def get_goal(goal_id: str) -> Optional[dict]:
    doc = await db["agent_goals"].find_one({"_id": goal_id, "deletedAt": None})
    return _to_dict(doc)


async def create_goal(data: dict, created_by: str) -> dict:
    now = utcnow()
    doc = {
        "_id": new_id(),
        "key": data.get("key") or f"goal-{new_id()[:8]}",
        "title": data.get("title") or "Nuovo goal",
        "description": data.get("description") or "",
        "metric": data.get("metric") or "actions_ok",
        "target": int(data.get("target") or 10),
        "progress": int(data.get("progress") or 0),
        "status": data.get("status") or "pending",
        "isDefault": False,
        "createdBy": created_by,
        "createdAt": now,
        "updatedAt": now,
        "deletedAt": None,
    }
    await db["agent_goals"].insert_one(doc)
    return _to_dict(doc)


async def update_goal(goal_id: str, data: dict) -> Optional[dict]:
    allowed = {"title", "description", "metric", "target", "progress", "status", "key"}
    updates = {k: v for k, v in data.items() if k in allowed}
    if "target" in updates:
        updates["target"] = max(int(updates["target"] or 1), 1)
    if "progress" in updates:
        updates["progress"] = max(int(updates["progress"] or 0), 0)
    if "status" in updates and updates["status"] not in (
        "pending", "in_progress", "completed", "cancelled"
    ):
        updates.pop("status")
    if not updates:
        return await get_goal(goal_id)
    updates["updatedAt"] = utcnow()
    doc = await db["agent_goals"].find_one_and_update(
        {"_id": goal_id, "deletedAt": None},
        {"$set": updates},
    )
    return _to_dict(doc) if doc else None


async def complete_goal(goal_id: str, note: str = "") -> Optional[dict]:
    goal = await get_goal(goal_id)
    if not goal:
        return None
    return await update_goal(goal_id, {
        "status": "completed",
        "progress": goal.get("target") or 1,
        "description": (goal.get("description") or "") + (f"\n[completato] {note}" if note else ""),
    })


async def reset_goal(goal_id: str) -> Optional[dict]:
    return await update_goal(goal_id, {"status": "in_progress", "progress": 0})


async def delete_goal(goal_id: str) -> bool:
    res = await db["agent_goals"].update_one(
        {"_id": goal_id, "deletedAt": None},
        {"$set": {"deletedAt": utcnow(), "updatedAt": utcnow()}},
    )
    return res.modified_count > 0


async def record_tool_success(tool_name: str, user_id: str) -> list[dict]:
    """
    Aggiorna i goal in base a un tool riuscito.
    Ritorna la lista dei goal toccati (per eventuale messaggio in chat).
    """
    impact = TOOL_GOAL_IMPACT.get(tool_name)
    if not impact:
        return []
    await ensure_default_goals()
    touched = []
    for metric, delta in impact.items():
        goals = await db["agent_goals"].find({
            "metric": metric,
            "deletedAt": None,
            "status": {"$in": ["pending", "in_progress"]},
        }).to_list(length=20)
        for g in goals:
            progress = int(g.get("progress") or 0) + delta
            target = max(int(g.get("target") or 1), 1)
            status = "completed" if progress >= target else "in_progress"
            await db["agent_goals"].update_one(
                {"_id": g["_id"]},
                {"$set": {"progress": progress, "status": status, "updatedAt": utcnow()}},
            )
            item = _to_dict(g)
            item["progress"] = progress
            item["status"] = status
            item["percent"] = min(100, round(progress / target * 100))
            touched.append(item)
    return touched


async def goals_prompt_block() -> str:
    goals = await list_goals()
    if not goals:
        return ""
    lines = ["# Goal attivi (aggiorna quando completi)"]
    for g in goals:
        mark = "✓" if g.get("status") == "completed" else "…"
        lines.append(
            f"{mark} {g.get('title')} — {g.get('progress', 0)}/{g.get('target', 1)} "
            f"({g.get('percent', 0)}%) [{g.get('status')}]"
        )
    lines.append(
        "Se un'azione completa un goal, dillo in modo breve (es. «Goal aggiornato: …»)."
    )
    return "\n".join(lines)
