"""
Test admin router — audit log, system stats, saved filters.
Mocks Firebase Auth and MongoDB.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
from app.main import app
from app.deps import require_sales, require_admin, UserRecord

client = TestClient(app)

_SALES_USER = UserRecord(uid="user_sales", role="sales", email="sales@test.com")
_ADMIN_USER = UserRecord(uid="user_admin", role="admin", email="admin@test.com")

_AUDIT_ENTRY = {
    "id": "audit-1",
    "userId": "user_admin",
    "userName": "Admin User",
    "action": "create",
    "entityType": "lead",
    "entityId": "lead-1",
    "description": "Lead creato",
    "changes": {},
    "createdAt": "2026-01-22T10:00:00Z",
}

_SYSTEM_STATS = {
    "entities": {
        "leads": {"total": 391, "last7d": 12, "last30d": 45},
        "deals": {"total": 15, "won": 3, "active": 8},
        "tasks": {"total": 20, "open": 5},
        "users": {"total": 4, "active": 4},
        "bookings": {"total": 8},
        "emailSequences": {"total": 1, "active": 0},
        "reports": {"total": 2},
        "formSubmissions": {"total": 15},
        "gdprConsents": {"total": 200},
    },
    "emails": {"sent": 50, "last30d": 30},
    "database": {"collections": 12, "totalDocuments": 1500},
}

_SAVED_FILTER = {
    "id": "sf-1",
    "userId": "user_sales",
    "name": "Legal Leads",
    "entityType": "leads",
    "filters": {"industry": "Legal", "status": "qualified"},
    "isGlobal": False,
}


@pytest.fixture(autouse=True)
def override_auth():
    app.dependency_overrides[require_sales] = lambda: _SALES_USER
    app.dependency_overrides[require_admin] = lambda: _ADMIN_USER
    yield
    app.dependency_overrides.pop(require_sales, None)
    app.dependency_overrides.pop(require_admin, None)


# ── Audit Log ──────────────────────────────────────────────────
def test_list_audit_log():
    """GET /api/v1/admin/audit-log returns entries."""
    with patch("app.routers.admin.audit_service.list_audit_log", new_callable=AsyncMock, return_value=[_AUDIT_ENTRY]):
        resp = client.get("/api/v1/admin/audit-log")
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["action"] == "create"


def test_audit_log_stats():
    """GET /api/v1/admin/audit-log/stats returns stats."""
    stats = {"total": 42, "byAction": {"create": 20, "update": 15}, "byEntity": {"lead": 30}, "topUsers": []}
    with patch("app.routers.admin.audit_service.get_audit_stats", new_callable=AsyncMock, return_value=stats):
        resp = client.get("/api/v1/admin/audit-log/stats")
    assert resp.status_code == 200
    assert resp.json()["total"] == 42


# ── System Stats ──────────────────────────────────────────────
def test_system_stats():
    """GET /api/v1/admin/system-stats returns system data."""
    with patch("app.routers.admin.system_service.get_system_stats", new_callable=AsyncMock, return_value=_SYSTEM_STATS):
        resp = client.get("/api/v1/admin/system-stats")
    assert resp.status_code == 200
    body = resp.json()
    assert body["entities"]["leads"]["total"] == 391
    assert body["database"]["collections"] == 12


# ── Saved Filters ─────────────────────────────────────────────
def test_list_saved_filters():
    """GET /api/v1/admin/saved-filters returns filters."""
    with patch("app.routers.admin.saved_filter_service.list_saved_filters", new_callable=AsyncMock, return_value=[_SAVED_FILTER]):
        resp = client.get("/api/v1/admin/saved-filters")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_create_saved_filter():
    """POST /api/v1/admin/saved-filters creates filter."""
    with patch("app.routers.admin.saved_filter_service.create_saved_filter", new_callable=AsyncMock, return_value=_SAVED_FILTER):
        resp = client.post("/api/v1/admin/saved-filters", json={
            "name": "Legal Leads", "entityType": "leads", "filters": {"industry": "Legal"},
        })
    assert resp.status_code == 200
    assert resp.json()["name"] == "Legal Leads"


def test_delete_saved_filter():
    """DELETE /api/v1/admin/saved-filters/{id} deletes filter."""
    with patch("app.routers.admin.saved_filter_service.delete_saved_filter", new_callable=AsyncMock, return_value=True):
        resp = client.delete("/api/v1/admin/saved-filters/sf-1")
    assert resp.status_code == 200
    assert resp.json()["ok"] is True


def test_audit_log_requires_admin():
    """Audit log requires admin role."""
    app.dependency_overrides[require_admin] = lambda: _SALES_USER  # sales user trying admin
    from app.deps import require_admin as real_admin
    # Simulate 403 by removing the override and using actual role check
    app.dependency_overrides.pop(require_admin, None)
    with patch("app.deps.get_current_user", new_callable=AsyncMock, return_value=_SALES_USER):
        resp = client.get("/api/v1/admin/audit-log")
    # This should be 403 because user is sales
    assert resp.status_code == 403