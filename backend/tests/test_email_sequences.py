"""
Test email sequences router.
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

_SEQ_DOC = {
    "id": "seq-123",
    "name": "Welcome Series",
    "description": "Test sequence",
    "steps": [
        {"subject": "Welcome", "bodyHtml": "<p>Hi</p>", "delayDays": 0},
        {"subject": "Follow up", "bodyHtml": "<p>Follow</p>", "delayDays": 3},
    ],
    "isActive": False,
    "enrollments": [],
    "createdBy": "user_sales",
    "deletedAt": None,
}


@pytest.fixture(autouse=True)
def override_auth():
    app.dependency_overrides[require_sales] = lambda: _SALES_USER
    app.dependency_overrides[require_admin] = lambda: _ADMIN_USER
    yield
    app.dependency_overrides.pop(require_sales, None)
    app.dependency_overrides.pop(require_admin, None)


def test_create_sequence():
    """POST /api/v1/email-sequences/ creates a sequence."""
    with patch("app.routers.email_sequences.svc.create_sequence", new_callable=AsyncMock, return_value=_SEQ_DOC) as mock_create:
        resp = client.post(
            "/api/v1/email-sequences/",
            json={"name": "Welcome Series", "description": "Test", "steps": [
                {"subject": "Welcome", "bodyHtml": "<p>Hi</p>", "delayDays": 0},
            ]},
        )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Welcome Series"
    mock_create.assert_called_once()


def test_list_sequences():
    """GET /api/v1/email-sequences/ returns list."""
    with patch("app.routers.email_sequences.svc.list_sequences", new_callable=AsyncMock, return_value=[_SEQ_DOC]), \
         patch("app.routers.email_sequences.svc.get_sequence_stats", new_callable=AsyncMock, return_value={"total": 0}):
        resp = client.get("/api/v1/email-sequences/")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_get_sequence():
    """GET /api/v1/email-sequences/{id} returns sequence."""
    with patch("app.routers.email_sequences.svc.get_sequence", new_callable=AsyncMock, return_value=_SEQ_DOC), \
         patch("app.routers.email_sequences.svc.get_sequence_stats", new_callable=AsyncMock, return_value={"total": 0}):
        resp = client.get("/api/v1/email-sequences/seq-123")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Welcome Series"


def test_get_sequence_not_found():
    """GET /api/v1/email-sequences/{id} returns 404 when missing."""
    with patch("app.routers.email_sequences.svc.get_sequence", new_callable=AsyncMock, return_value=None):
        resp = client.get("/api/v1/email-sequences/nonexistent")
    assert resp.status_code == 404


def test_update_sequence():
    """PATCH /api/v1/email-sequences/{id} updates."""
    updated = {**_SEQ_DOC, "name": "Updated Name"}
    with patch("app.routers.email_sequences.svc.update_sequence", new_callable=AsyncMock, return_value=updated):
        resp = client.patch("/api/v1/email-sequences/seq-123", json={"name": "Updated Name"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "Updated Name"


def test_delete_sequence():
    """DELETE /api/v1/email-sequences/{id} soft deletes."""
    with patch("app.routers.email_sequences.svc.delete_sequence", new_callable=AsyncMock, return_value=True):
        resp = client.delete("/api/v1/email-sequences/seq-123")
    assert resp.status_code == 200
    assert resp.json()["ok"] is True


def test_activate_sequence():
    """POST /api/v1/email-sequences/{id}/activate."""
    active_doc = {**_SEQ_DOC, "isActive": True}
    with patch("app.routers.email_sequences.svc.set_active", new_callable=AsyncMock, return_value=active_doc):
        resp = client.post("/api/v1/email-sequences/seq-123/activate")
    assert resp.status_code == 200
    assert resp.json()["isActive"] is True


def test_deactivate_sequence():
    """POST /api/v1/email-sequences/{id}/deactivate."""
    with patch("app.routers.email_sequences.svc.set_active", new_callable=AsyncMock, return_value=_SEQ_DOC):
        resp = client.post("/api/v1/email-sequences/seq-123/deactivate")
    assert resp.status_code == 200
    assert resp.json()["isActive"] is False


def test_enroll_lead():
    """POST /api/v1/email-sequences/{id}/enroll."""
    enrollment = {"id": "enroll-1", "leadId": "lead-1", "status": "active"}
    with patch("app.routers.email_sequences.svc.enroll_lead", new_callable=AsyncMock, return_value=enrollment):
        resp = client.post("/api/v1/email-sequences/seq-123/enroll", json={"leadId": "lead-1"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "active"


def test_enroll_lead_not_found():
    """POST enroll returns 404 when lead/sequence missing."""
    with patch("app.routers.email_sequences.svc.enroll_lead", new_callable=AsyncMock, return_value=None):
        resp = client.post("/api/v1/email-sequences/seq-123/enroll", json={"leadId": "bad"})
    assert resp.status_code == 404


def test_advance_enrollment():
    """POST advance enrollment."""
    enrollment = {"id": "enroll-1", "status": "completed", "currentStep": 2}
    with patch("app.routers.email_sequences.svc.advance_enrollment", new_callable=AsyncMock, return_value=enrollment):
        resp = client.post("/api/v1/email-sequences/seq-123/enrollments/enroll-1/advance")
    assert resp.status_code == 200
    assert resp.json()["status"] == "completed"


def test_pause_enrollment():
    """POST pause enrollment."""
    enrollment = {"id": "enroll-1", "status": "paused"}
    with patch("app.routers.email_sequences.svc.pause_enrollment", new_callable=AsyncMock, return_value=enrollment):
        resp = client.post("/api/v1/email-sequences/seq-123/enrollments/enroll-1/pause")
    assert resp.status_code == 200
    assert resp.json()["status"] == "paused"


def test_resume_enrollment():
    """POST resume enrollment."""
    enrollment = {"id": "enroll-1", "status": "active"}
    with patch("app.routers.email_sequences.svc.resume_enrollment", new_callable=AsyncMock, return_value=enrollment):
        resp = client.post("/api/v1/email-sequences/seq-123/enrollments/enroll-1/resume")
    assert resp.status_code == 200
    assert resp.json()["status"] == "active"


def test_unsubscribe_enrollment():
    """POST unsubscribe enrollment."""
    enrollment = {"id": "enroll-1", "status": "unsubscribed"}
    with patch("app.routers.email_sequences.svc.unsubscribe_enrollment", new_callable=AsyncMock, return_value=enrollment):
        resp = client.post("/api/v1/email-sequences/seq-123/enrollments/enroll-1/unsubscribe")
    assert resp.status_code == 200
    assert resp.json()["status"] == "unsubscribed"


def test_get_stats():
    """GET /api/v1/email-sequences/{id}/stats."""
    stats = {"total": 5, "active": 3, "completed": 2, "completionRate": 40.0}
    with patch("app.routers.email_sequences.svc.get_sequence_stats", new_callable=AsyncMock, return_value=stats):
        resp = client.get("/api/v1/email-sequences/seq-123/stats")
    assert resp.status_code == 200
    assert resp.json()["total"] == 5


def test_health_check():
    """GET /api/health returns status with checks."""
    with patch("app.main.mongo_db") as mock_db:
        mock_db.command = AsyncMock(return_value={"ok": 1})
        resp = client.get("/api/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["checks"]["mongodb"] == "ok"
    assert "timestamp" in body
    assert "version" in body


def test_security_headers():
    """All responses include security headers."""
    with patch("app.routers.email_sequences.svc.list_sequences", new_callable=AsyncMock, return_value=[]):
        resp = client.get("/api/v1/email-sequences/")
    assert resp.headers.get("X-Content-Type-Options") == "nosniff"
    assert resp.headers.get("X-Frame-Options") == "DENY"
    assert resp.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"