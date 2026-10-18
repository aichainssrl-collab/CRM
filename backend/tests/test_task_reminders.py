"""Promemoria email per task in scadenza."""
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services import task_reminder_service as rem


def test_classify_due_buckets():
    now = datetime(2026, 10, 18, 12, 0, tzinfo=timezone.utc)
    assert rem.classify_due(now - timedelta(hours=1), now) == "overdue"
    assert rem.classify_due(now.replace(hour=15), now) == "due_today"
    assert rem.classify_due(now + timedelta(days=3), now) == "due_soon"
    assert rem.classify_due(now + timedelta(days=30), now) is None
    assert rem.classify_due(None, now) is None


def test_classify_due_naive_datetime():
    now = datetime(2026, 10, 18, 12, 0, tzinfo=timezone.utc)
    naive = datetime(2026, 10, 18, 11, 0)
    assert rem.classify_due(naive, now) == "overdue"


@pytest.mark.asyncio
async def test_send_reminders_skips_already_sent():
    task = {
        "_id": "t1",
        "title": "Call",
        "dueDate": datetime.now(timezone.utc) - timedelta(hours=2),
        "assignedTo": "u1",
        "priority": "high",
        "status": "open",
        "deletedAt": None,
    }

    class _Iter:
        def __init__(self, items):
            self._items = list(items)

        def __aiter__(self):
            return self

        async def __anext__(self):
            if not self._items:
                raise StopAsyncIteration
            return self._items.pop(0)

    with patch("app.services.task_reminder_service.db") as mock_db, \
         patch("app.services.email_service.send_email_ex", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = {"ok": True, "id": "e1", "mock": True, "error": None}
        mock_col = MagicMock()
        mock_col.find.return_value.sort.return_value.limit.return_value = _Iter([task])
        mock_col.find_one = AsyncMock(return_value={"_id": "r1"})  # già inviato
        mock_col.insert_one = AsyncMock()
        mock_db.__getitem__.return_value = mock_col

        res = await rem.send_due_task_reminders()

    assert res["skipped"] == 1
    assert res["sent"] == 0
    mock_send.assert_not_awaited()


@pytest.mark.asyncio
async def test_send_reminders_sends_and_marks():
    task = {
        "_id": "t2",
        "title": "Follow-up",
        "dueDate": datetime.now(timezone.utc) - timedelta(days=1),
        "assignedTo": "u1",
        "priority": "normal",
        "status": "open",
        "deletedAt": None,
    }

    class _Iter:
        def __init__(self, items):
            self._items = list(items)

        def __aiter__(self):
            return self

        async def __anext__(self):
            if not self._items:
                raise StopAsyncIteration
            return self._items.pop(0)

    with patch("app.services.task_reminder_service.db") as mock_db, \
         patch("app.services.email_service.send_email_ex", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = {"ok": True, "id": "e2", "mock": True, "error": None}
        mock_col = MagicMock()
        mock_col.find.return_value.sort.return_value.limit.return_value = _Iter([task])
        mock_col.find_one = AsyncMock(return_value=None)
        mock_col.insert_one = AsyncMock()
        # users lookup
        def get_col(name):
            return mock_col
        mock_db.__getitem__ = MagicMock(side_effect=get_col)

        res = await rem.send_due_task_reminders()

    assert res["sent"] == 1
    mock_send.assert_awaited_once()
    assert "scaduta" in mock_send.await_args.kwargs["subject"].lower() or "scaduta" in mock_send.await_args.args[1].lower()
