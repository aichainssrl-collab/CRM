"""
LLM settings API tests (admin-only, Mongo-backed with mocks).
"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.deps import require_admin, require_sales, UserRecord

client = TestClient(app)
_ADMIN = UserRecord(uid="admin-1", role="admin", email="admin@test.com")


@pytest.fixture(autouse=True)
def override_auth():
    app.dependency_overrides[require_admin] = lambda: _ADMIN
    app.dependency_overrides[require_sales] = lambda: _ADMIN
    yield
    app.dependency_overrides.pop(require_admin, None)
    app.dependency_overrides.pop(require_sales, None)


def _mock_settings_col(doc=None):
    col = MagicMock()
    col.find_one = AsyncMock(return_value=doc)
    col.update_one = AsyncMock()
    return col


def test_get_llm_settings_never_returns_raw_key():
    col = _mock_settings_col({
        "_id": "llm",
        "provider": "openai",
        "model": "gpt-4o",
        "baseUrl": "https://api.openai.com/v1",
        "apiKey": "sk-secret-key-12345678",
    })
    with patch("app.services.llm_settings_service.db") as mock_db:
        mock_db.__getitem__ = MagicMock(return_value=col)
        resp = client.get("/api/v1/admin/llm-settings")
    data = resp.json()
    assert resp.status_code == 200
    assert data["apiKey"] is None
    assert data["apiKeySet"] is True
    assert "secret-key" not in str(data)
    assert data["apiKeyMasked"].startswith("sk-s")


def test_update_llm_settings_persists_model_and_url():
    col = _mock_settings_col(None)
    with patch("app.services.llm_settings_service.db") as mock_db:
        mock_db.__getitem__ = MagicMock(return_value=col)
        resp = client.put(
            "/api/v1/admin/llm-settings",
            json={
                "provider": "custom",
                "model": "qwen3:4b",
                "baseUrl": "http://localhost:11434/v1",
                "apiKey": "sk-new-key",
            },
        )
    assert resp.status_code == 200
    set_payload = col.update_one.await_args.args[1]["$set"]
    assert set_payload["model"] == "qwen3:4b"
    assert set_payload["baseUrl"] == "http://localhost:11434/v1"
    assert set_payload["apiKey"] == "sk-new-key"


def test_clear_api_key():
    col = _mock_settings_col({"_id": "llm", "apiKey": "sk-old"})
    with patch("app.services.llm_settings_service.db") as mock_db:
        mock_db.__getitem__ = MagicMock(return_value=col)
        resp = client.put(
            "/api/v1/admin/llm-settings",
            json={"clearApiKey": True},
        )
    assert resp.status_code == 200
    set_payload = col.update_one.await_args.args[1]["$set"]
    assert set_payload["apiKey"] is None
