"""
Test content library router.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from app.main import app
from app.deps import require_sales, UserRecord

client = TestClient(app)
_SALES_USER = UserRecord(uid="user_sales", role="sales", email="sales@test.com")

_CONTENT = {
    "id": "c1",
    "title": "Email welcome ZenTratto",
    "type": "email",
    "body": "Ciao {{firstName}}...",
    "tags": ["welcome", "zentratto"],
    "language": "it",
    "source": "marketing_agent",
}


@pytest.fixture(autouse=True)
def override_auth():
    app.dependency_overrides[require_sales] = lambda: _SALES_USER
    yield
    app.dependency_overrides.pop(require_sales, None)


def test_list_content():
    with patch(
        "app.routers.content.content_service.list_content",
        new_callable=AsyncMock,
        return_value=[_CONTENT],
    ):
        resp = client.get("/api/v1/content/")
    assert resp.status_code == 200
    assert resp.json()[0]["title"] == "Email welcome ZenTratto"


def test_create_content():
    with patch(
        "app.routers.content.content_service.create_content",
        new_callable=AsyncMock,
        return_value=_CONTENT,
    ):
        resp = client.post(
            "/api/v1/content/",
            json={"title": "Email welcome ZenTratto", "type": "email", "body": "Ciao"},
        )
    assert resp.status_code == 200
    assert resp.json()["type"] == "email"


def test_create_content_invalid_type():
    resp = client.post("/api/v1/content/", json={"title": "X", "type": "spam"})
    assert resp.status_code == 400


def test_update_content():
    updated = {**_CONTENT, "title": "Updated"}
    with patch(
        "app.routers.content.content_service.update_content",
        new_callable=AsyncMock,
        return_value=updated,
    ):
        resp = client.patch("/api/v1/content/c1", json={"title": "Updated"})
    assert resp.status_code == 200
    assert resp.json()["title"] == "Updated"


def test_delete_content():
    with patch(
        "app.routers.content.content_service.delete_content",
        new_callable=AsyncMock,
        return_value=True,
    ):
        resp = client.delete("/api/v1/content/c1")
    assert resp.status_code == 200
    assert resp.json()["ok"] is True


def test_content_stats():
    stats = {"totalCount": 5, "byType": {"email": 3, "social": 2}}
    with patch(
        "app.routers.content.content_service.content_stats",
        new_callable=AsyncMock,
        return_value=stats,
    ):
        resp = client.get("/api/v1/content/stats")
    assert resp.status_code == 200
    assert resp.json()["totalCount"] == 5


def test_content_tags():
    with patch(
        "app.routers.content.content_service.list_tags",
        new_callable=AsyncMock,
        return_value=["welcome", "zentratto"],
    ):
        resp = client.get("/api/v1/content/tags")
    assert resp.status_code == 200
    assert resp.json() == ["welcome", "zentratto"]
