"""
Calendar service — aggregate tasks, bookings, deals by date.
"""
from datetime import datetime, timezone, timedelta
from app.services.db_service import db
import logging

logger = logging.getLogger(__name__)


async def get_calendar_events(year: int, month: int) -> list[dict]:
    """Get all events (tasks, bookings, deal deadlines) for a given month."""
    start = datetime(year, month, 1, tzinfo=timezone.utc)
    if month == 12:
        end = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
    else:
        end = datetime(year, month + 1, 1, tzinfo=timezone.utc)

    events = []

    # Tasks with due dates
    task_cursor = db["tasks"].find({
        "deletedAt": None,
        "dueDate": {"$gte": start, "$lt": end},
    }).sort("dueDate", 1)
    async for task in task_cursor:
        events.append({
            "id": task["_id"],
            "type": "task",
            "title": task.get("title", ""),
            "date": task.get("dueDate").isoformat() if task.get("dueDate") else None,
            "status": task.get("status", "open"),
            "assignedTo": task.get("assignedTo"),
        })

    # Bookings
    booking_cursor = db["bookings"].find({
        "deletedAt": None,
        "preferredDate": {"$gte": start, "$lt": end},
    }).sort("preferredDate", 1)
    async for booking in booking_cursor:
        events.append({
            "id": booking["_id"],
            "type": "booking",
            "title": f"Demo — {booking.get('firstName', '')} {booking.get('lastName', '')}".strip(),
            "date": booking.get("preferredDate").isoformat() if booking.get("preferredDate") else None,
            "status": booking.get("status", "pending"),
            "timeSlot": booking.get("timeSlot"),
        })

    # Deal expected close dates
    deal_cursor = db["deals"].find({
        "deletedAt": None,
        "expectedClose": {"$gte": start, "$lt": end},
        "stage": {"$nin": ["won", "lost"]},
    }).sort("expectedClose", 1)
    async for deal in deal_cursor:
        events.append({
            "id": deal["_id"],
            "type": "deal",
            "title": f"Deal: {deal.get('title', '')}",
            "date": deal.get("expectedClose").isoformat() if deal.get("expectedClose") else None,
            "status": deal.get("stage", "new"),
            "value": deal.get("value"),
        })

    return events


async def get_upcoming_events(days: int = 7) -> list[dict]:
    """Get upcoming events for the next N days."""
    now = datetime.now(timezone.utc)
    end = now + timedelta(days=days)

    events = []

    # Tasks
    task_cursor = db["tasks"].find({
        "deletedAt": None,
        "status": "open",
        "dueDate": {"$gte": now, "$lte": end},
    }).sort("dueDate", 1)
    async for task in task_cursor:
        events.append({
            "id": task["_id"],
            "type": "task",
            "title": task.get("title", ""),
            "date": task.get("dueDate").isoformat() if task.get("dueDate") else None,
        })

    # Bookings
    booking_cursor = db["bookings"].find({
        "deletedAt": None,
        "preferredDate": {"$gte": now, "$lte": end},
        "status": {"$ne": "cancelled"},
    }).sort("preferredDate", 1)
    async for booking in booking_cursor:
        events.append({
            "id": booking["_id"],
            "type": "booking",
            "title": f"Demo — {booking.get('firstName', '')} {booking.get('lastName', '')}".strip(),
            "date": booking.get("preferredDate").isoformat() if booking.get("preferredDate") else None,
        })

    # Sort by date
    events.sort(key=lambda e: e.get("date") or "")
    return events