"""
Test notifications & search router.
Mocks Firebase Auth and MongoDB.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
from app.main import app
from app.deps import require_sales, UserRecord

client = TestClient(app)

_SALES_USER = UserRecord(uid="user_sales", role="sales", email="sales@test.com")

_NOTIF = {
    "id": "notif-1",
    "userId": "user_sales",
    "title": "Nuovo lead",
    "body": "Mario Rossi è stato aggiunto",
    "kind": "info",
    "link": "/crm/leads/lead-1",
    "readAt": None,
    "createdAt": "2026-01-22T10:00:00Z",
}

_ACTIVITY = {
    "id": "act-1",
    "userId": "user_sales",
    "userName": "Sales User",
    "action": "lead.created",
    "entityType": "lead",
    "entityId": "lead-1",
    "description": "Lead Mario Rossi creato",
    "metadata": {},
    "createdAt": "2026-01-22T10:00:00Z",
}

_SEARCH = {
    "leads": [{"id": "l1", "title": "Mario Rossi", "subtitle": "Studio Rossi", "status": "qualified"}],
    "deals": [{"id": "d1", "title": "Deal ERP", "subtitle": "€15.000", "status": "proposal"}],
    "tasks": [{"id": "t1", "title": "Chiamare Mario", "subtitle": "", "status": "open"}],
}


@pytest.fixture(autouse=True)
def override_auth():
    app.dependency_overrides[require_sales] = lambda: _SALES_USER
    yield
    app.dependency_overrides.pop(require_sales, None)


def test_list_notifications():
    """GET /api/v1/notifications/ returns notifications."""
    with patch("app.routers.notifications.svc.list_notifications", new_callable=AsyncMock, return_value=[_NOTIF]):
        resp = client.get("/api/v1/notifications/")
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["title"] == "Nuovo lead"


def test_unread_count():
    """GET /api/v1/notifications/unread-count returns count."""
    with patch("app.routers.notifications.svc.get_unread_count", new_callable=AsyncMock, return_value=5):
        resp = client.get("/api/v1/notifications/unread-count")
    assert resp.status_code == 200
    assert resp.json()["count"] == 5


def test_mark_read():
    """POST /api/v1/notifications/mark-read marks a notification."""
    with patch("app.routers.notifications.svc.mark_read", new_callable=AsyncMock, return_value=_NOTIF):
        resp = client.post("/api/v1/notifications/mark-read", json={"notificationId": "notif-1"})
    assert resp.status_code == 200
    assert resp.json()["ok"] is True


def test_mark_all_read():
    """POST /api/v1/notifications/mark-all-read marks all."""
    with patch("app.routers.notifications.svc.mark_all_read", new_callable=AsyncMock, return_value=3):
        resp = client.post("/api/v1/notifications/mark-all-read")
    assert resp.status_code == 200
    assert resp.json()["marked"] == 3


def test_activity_feed():
    """GET /api/v1/notifications/activity-feed returns activities."""
    with patch("app.routers.notifications.svc.get_activity_feed", new_callable=AsyncMock, return_value=[_ACTIVITY]):
        resp = client.get("/api/v1/notifications/activity-feed")
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["action"] == "lead.created"


def test_global_search():
    """GET /api/v1/notifications/search returns results."""
    with patch("app.routers.notifications.svc.global_search", new_callable=AsyncMock, return_value=_SEARCH):
        resp = client.get("/api/v1/notifications/search?q=Mario")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["leads"]) == 1
    assert len(body["deals"]) == 1
    assert len(body["tasks"]) == 1


def test_search_requires_query():
    """GET /api/v1/notifications/search returns 422 without query."""
    resp = client.get("/api/v1/notifications/search")
    assert resp.status_code == 422


def test_search_min_length():
    """GET /api/v1/notifications/search requires at least 1 char."""
    resp = client.get("/api/v1/notifications/search?q=")
    assert resp.status_code == 422