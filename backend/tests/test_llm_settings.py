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
    col.insert_one = AsyncMock()
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
    doc = col.insert_one.await_args.args[0]
    assert doc["model"] == "qwen3:4b"
    assert doc["baseUrl"] == "http://localhost:11434/v1"
    assert doc["apiKey"] == "sk-new-key"


def test_update_llm_settings_existing_doc_uses_update_one():
    col = _mock_settings_col({"_id": "llm", "model": "old"})
    with patch("app.services.llm_settings_service.db") as mock_db:
        mock_db.__getitem__ = MagicMock(return_value=col)
        resp = client.put(
            "/api/v1/admin/llm-settings",
            json={"model": "gpt-4o-mini", "baseUrl": "https://api.openai.com/v1"},
        )
    assert resp.status_code == 200
    set_payload = col.update_one.await_args.args[1]["$set"]
    assert set_payload["model"] == "gpt-4o-mini"


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


def test_llm_connection_test_button_uses_form_values():
    """POST /llm-settings/test probes draft config without saving."""
    col = _mock_settings_col(None)

    class FakeResp:
        def __getitem__(self, k):
            return {"model": "gpt-4o-mini"}[k]

        def get(self, k, default=None):
            return {"model": "gpt-4o-mini"}.get(k, default)

    async def fake_completion(**kwargs):
        # custom provider is prefixed for litellm
        assert kwargs.get("model") in ("gpt-4o-mini", "openai/gpt-4o-mini")
        assert kwargs.get("api_base") == "http://localhost:11434/v1"
        return FakeResp()

    with (
        patch("app.services.llm_settings_service.db") as mock_db,
        patch("litellm.acompletion", side_effect=fake_completion),
    ):
        mock_db.__getitem__ = MagicMock(return_value=col)
        resp = client.post(
            "/api/v1/admin/llm-settings/test",
            json={
                "provider": "custom",
                "model": "gpt-4o-mini",
                "baseUrl": "http://localhost:11434/v1",
                "apiKey": "sk-draft",
            },
        )
    data = resp.json()
    assert resp.status_code == 200
    assert data["ok"] is True
    assert data["model"] in ("gpt-4o-mini", "openai/gpt-4o-mini")


def test_custom_model_id_with_slash_gets_openai_prefix():
    """Bionic-style ids (nvidia/nemotron-3-nano-4b) must not be treated as litellm providers."""
    from app.services.llm_settings_service import get_llm_runtime_config, _as_openai_compatible_model

    assert _as_openai_compatible_model("nvidia/nemotron-3-nano-4b") == "openai/nvidia/nemotron-3-nano-4b"
    assert _as_openai_compatible_model("openai/gpt-4o") == "openai/gpt-4o"
    assert _as_openai_compatible_model("qwen3:4b") == "openai/qwen3:4b"

    col = _mock_settings_col({
        "_id": "llm",
        "provider": "custom",
        "model": "nvidia/nemotron-3-nano-4b",
        "baseUrl": "http://localhost:1235/v1",
        "apiKey": "no-key",
    })
    with patch("app.services.llm_settings_service.db") as mock_db:
        mock_db.__getitem__ = MagicMock(return_value=col)

        async def _run():
            return await get_llm_runtime_config()

        import asyncio
        cfg = asyncio.run(_run())

    assert cfg["model"] == "openai/nvidia/nemotron-3-nano-4b"
    assert cfg["api_base"] == "http://localhost:1235/v1"
