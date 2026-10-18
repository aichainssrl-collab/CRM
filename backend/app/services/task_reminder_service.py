"""
Task email reminders — promemoria per task scadute / in scadenza.

Anti-duplicato: un reminder per task+bucket (overdue | due_today | due_soon)
viene inviato una volta sola finché lo stato del task non cambia.
Collezione: task_reminders
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from app.services.db_service import db, new_id, utcnow

logger = logging.getLogger(__name__)


def _aware(dt: Any) -> Optional[datetime]:
    if isinstance(dt, datetime):
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    return None


def classify_due(due: Any, now: datetime) -> Optional[str]:
    """overdue | due_today | due_soon | None"""
    d = _aware(due)
    if not d:
        return None
    if d < now:
        return "overdue"
    start_today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_today = start_today + timedelta(days=1)
    if start_today <= d < end_today:
        return "due_today"
    if d < now + timedelta(days=7):
        return "due_soon"
    return None


async def _user_email(uid: str) -> Optional[str]:
    if not uid:
        return None
    doc = await db["users"].find_one({"_id": uid})
    return (doc or {}).get("email")


async def _already_reminded(task_id: str, bucket: str) -> bool:
    doc = await db["task_reminders"].find_one({
        "taskId": task_id,
        "bucket": bucket,
        "deletedAt": None,
    })
    return bool(doc)


async def _mark_reminded(task_id: str, bucket: str, to: str, email_id: Optional[str]) -> None:
    await db["task_reminders"].insert_one({
        "_id": new_id(),
        "taskId": task_id,
        "bucket": bucket,
        "to": to,
        "emailId": email_id,
        "createdAt": utcnow(),
        "deletedAt": None,
    })


def _reminder_html(title: str, due: Optional[datetime], bucket: str, priority: str) -> str:
    when = due.strftime("%d/%m/%Y %H:%M") if due else "—"
    if bucket == "overdue":
        headline = f"⚠️ Task scaduta: {title}"
        intro = "Questa attività è scaduta e richiede attenzione."
    elif bucket == "due_today":
        headline = f"🔔 Task in scadenza oggi: {title}"
        intro = "Questa attività scade oggi."
    else:
        headline = f"📅 Promemoria task: {title}"
        intro = "Questa attività è in scadenza nei prossimi giorni."
    return f"""
    <div style="font-family:Arial,sans-serif;max-width:560px">
      <h2 style="margin:0 0 12px">{headline}</h2>
      <p>{intro}</p>
      <ul>
        <li><strong>Scadenza:</strong> {when}</li>
        <li><strong>Priorità:</strong> {priority or "normal"}</li>
      </ul>
      <p style="color:#666;font-size:12px">Promemoria automatico AiChain CRM</p>
    </div>
    """


async def send_due_task_reminders(
    *,
    hours_ahead: int = 24,
    include_overdue: bool = True,
    only_uid: Optional[str] = None,
    force: bool = False,
) -> dict:
    """
    Invia promemoria email per task scadute o in scadenza.
    Ritorna {sent, skipped, errors, items[]}.
    """
    from app.services.email_service import send_email_ex

    now = datetime.now(timezone.utc)
    limit_dt = now + timedelta(hours=max(hours_ahead, 1))
    week_dt = now + timedelta(days=7)

    query: dict[str, Any] = {
        "deletedAt": None,
        "status": "open",
        "dueDate": {"$ne": None, "$lt": week_dt},
    }
    if only_uid:
        query["assignedTo"] = only_uid

    cursor = db["tasks"].find(query).sort("dueDate", 1).limit(100)
    sent = skipped = errors = 0
    items: list[dict] = []

    async for task in cursor:
        due = _aware(task.get("dueDate"))
        bucket = classify_due(due, now)
        if not bucket:
            continue
        if bucket == "due_soon" and due and due > limit_dt and hours_ahead <= 24:
            # per bucket due_soon invia solo se entro la finestra
            pass  # week list already filtered; keep due_soon for 7d digests when hours_ahead large
        if bucket == "overdue" and not include_overdue:
            continue

        task_id = task["_id"]
        if not force and await _already_reminded(task_id, bucket):
            skipped += 1
            items.append({"taskId": task_id, "title": task.get("title"), "bucket": bucket, "status": "skipped"})
            continue

        to = await _user_email(task.get("assignedTo"))
        if not to:
            # fallback: admin/sales con email? oppure EMAIL_FROM
            from app.config import settings

            to = settings.EMAIL_FROM
        if not to:
            errors += 1
            items.append({"taskId": task_id, "title": task.get("title"), "bucket": bucket, "status": "no_email"})
            continue

        subject = {
            "overdue": f"[CRM] Task scaduta: {task.get('title')}",
            "due_today": f"[CRM] Task in scadenza oggi: {task.get('title')}",
            "due_soon": f"[CRM] Promemoria task: {task.get('title')}",
        }.get(bucket, f"[CRM] Promemoria: {task.get('title')}")

        try:
            result = await send_email_ex(
                to=to,
                subject=subject,
                html=_reminder_html(task.get("title") or "Task", due, bucket, task.get("priority") or "normal"),
            )
            if result.get("ok"):
                sent += 1
                await _mark_reminded(task_id, bucket, to, result.get("id"))
                items.append({
                    "taskId": task_id,
                    "title": task.get("title"),
                    "bucket": bucket,
                    "status": "sent",
                    "to": to,
                    "mock": result.get("mock"),
                })
            else:
                errors += 1
                items.append({
                    "taskId": task_id,
                    "title": task.get("title"),
                    "bucket": bucket,
                    "status": "error",
                    "error": result.get("error"),
                })
        except Exception as exc:
            logger.exception("task reminder failed")
            errors += 1
            items.append({
                "taskId": task_id,
                "title": task.get("title"),
                "bucket": bucket,
                "status": "error",
                "error": str(exc),
            })

    return {
        "sent": sent,
        "skipped": skipped,
        "errors": errors,
        "items": items,
        "timestamp": now.isoformat(),
    }


async def list_recent_reminders(limit: int = 50) -> list[dict]:
    cursor = db["task_reminders"].find({"deletedAt": None}).sort("createdAt", -1).limit(min(limit, 200))
    out = []
    async for d in cursor:
        out.append({
            "id": d["_id"],
            "taskId": d.get("taskId"),
            "bucket": d.get("bucket"),
            "to": d.get("to"),
            "emailId": d.get("emailId"),
            "createdAt": d.get("createdAt").isoformat() if hasattr(d.get("createdAt"), "isoformat") else str(d.get("createdAt")),
        })
    return out
