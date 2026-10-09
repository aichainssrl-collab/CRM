"""
Test calendar & bulk operations router.
Mocks Firebase Auth and MongoDB.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
from app.main import app
from app.deps import require_sales, UserRecord

client = TestClient(app)

_SALES_USER = UserRecord(uid="user_sales", role="sales", email="sales@test.com")

_EVENTS = [
    {"id": "t1", "type": "task", "title": "Chiamare Mario", "date": "2026-01-15T00:00:00Z", "status": "open"},
    {"id": "b1", "type": "booking", "title": "Demo — Mario Rossi", "date": "2026-01-20T00:00:00Z", "status": "pending"},
    {"id": "d1", "type": "deal", "title": "Deal: ZenTratto", "date": "2026-01-25T00:00:00Z", "status": "proposal", "value": 15000},
]


@pytest.fixture(autouse=True)
def override_auth():
    app.dependency_overrides[require_sales] = lambda: _SALES_USER
    yield
    app.dependency_overrides.pop(require_sales, None)


def test_calendar_events():
    """GET /api/v1/calendar/events returns events for month."""
    with patch("app.routers.calendar.calendar_service.get_calendar_events", new_callable=AsyncMock, return_value=_EVENTS):
        resp = client.get("/api/v1/calendar/events?year=2026&month=1")
    assert resp.status_code == 200
    assert len(resp.json()) == 3


def test_upcoming_events():
    """GET /api/v1/calendar/upcoming returns events."""
    with patch("app.routers.calendar.calendar_service.get_upcoming_events", new_callable=AsyncMock, return_value=_EVENTS[:2]):
        resp = client.get("/api/v1/calendar/upcoming?days=7")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_bulk_assign():
    """POST /api/v1/calendar/bulk/assign updates leads."""
    with patch("app.routers.calendar.db") as mock_db:
        mock_col = MagicMock()
        mock_db.__getitem__ = MagicMock(return_value=mock_col)
        mock_result = MagicMock()
        mock_result.modified_count = 3
        mock_col.update_many = AsyncMock(return_value=mock_result)
        resp = client.post("/api/v1/calendar/bulk/assign", json={
            "leadIds": ["l1", "l2", "l3"], "assignedTo": "user_sales",
        })
    assert resp.status_code == 200
    assert resp.json()["updated"] == 3


def test_bulk_status():
    """POST /api/v1/calendar/bulk/status updates status."""
    with patch("app.routers.calendar.db") as mock_db:
        mock_col = MagicMock()
        mock_db.__getitem__ = MagicMock(return_value=mock_col)
        mock_result = MagicMock()
        mock_result.modified_count = 2
        mock_col.update_many = AsyncMock(return_value=mock_result)
        resp = client.post("/api/v1/calendar/bulk/status", json={
            "leadIds": ["l1", "l2"], "status": "contacted",
        })
    assert resp.status_code == 200
    assert resp.json()["updated"] == 2


def test_bulk_delete():
    """POST /api/v1/calendar/bulk/delete soft deletes leads."""
    with patch("app.routers.calendar.db") as mock_db:
        mock_col = MagicMock()
        mock_db.__getitem__ = MagicMock(return_value=mock_col)
        mock_result = MagicMock()
        mock_result.modified_count = 5
        mock_col.update_many = AsyncMock(return_value=mock_result)
        resp = client.post("/api/v1/calendar/bulk/delete", json={
            "leadIds": ["l1", "l2", "l3", "l4", "l5"], "assignedTo": "",
        })
    assert resp.status_code == 200
    assert resp.json()["deleted"] == 5


def test_leaderboard():
    """GET /api/v1/calendar/leaderboard returns ranking."""
    with patch("app.routers.calendar.db") as mock_db:
        mock_col = MagicMock()
        mock_db.__getitem__ = MagicMock(return_value=mock_col)

        class AsyncCursor:
            def __init__(self, data):
                self._data = data
            def __aiter__(self):
                self._iter = iter(self._data)
                return self
            async def __anext__(self):
                try:
                    return next(self._iter)
                except StopIteration:
                    raise StopAsyncIteration

        call_count = [0]
        def mock_aggregate(pipeline):
            call_count[0] += 1
            if call_count[0] == 1:
                return AsyncCursor([{"_id": "user1", "dealsWon": 5, "revenue": 50000.0}])
            elif call_count[0] == 2:
                return AsyncCursor([{"_id": "user1", "tasksCompleted": 10}])
            else:
                return AsyncCursor([{"_id": "user1", "leadsAssigned": 15}])

        mock_col.aggregate = mock_aggregate

        def mock_find(*args, **kwargs):
            return AsyncCursor([{"_id": "user1", "displayName": "Mario Rossi"}])
        mock_col.find = mock_find

        resp = client.get("/api/v1/calendar/leaderboard?days=30")

    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, list)
    assert len(body) >= 1


def test_calendar_endpoints_work():
    """Calendar endpoints work with auth override."""
    with patch("app.routers.calendar.calendar_service.get_calendar_events", new_callable=AsyncMock, return_value=[]):
        resp = client.get("/api/v1/calendar/events?year=2026&month=1")
    assert resp.status_code == 200