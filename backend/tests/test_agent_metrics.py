"""Fase G — metriche, health, esecuzione post-approvazione."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.deps import require_sales, UserRecord
from app.services import agent_metrics as m


client = TestClient(app)
_USER = UserRecord(uid="g-user", role="admin", email="g@test.com")


@pytest.fixture(autouse=True)
def override_auth():
    app.dependency_overrides[require_sales] = lambda: _USER
    yield
    app.dependency_overrides.pop(require_sales, None)


@pytest.mark.asyncio
async def test_agent_metrics_aggregates():
    runs = [
        {"ok": True, "mode": "parser", "durationMs": 100, "tools": ["find_lead"]},
        {"ok": False, "mode": "llm_error", "durationMs": 200, "tools": []},
        {"ok": True, "mode": "llm", "durationMs": 300, "tools": ["find_lead", "create_lead"]},
    ]

    class _Iter:
        def __init__(self, items):
            self._items = list(items)

        def __aiter__(self):
            return self

        async def __anext__(self):
            if not self._items:
                raise StopAsyncIteration
            return self._items.pop(0)

    with patch("app.services.agent_metrics.db") as mock_db:
        mock_db.__getitem__.return_value.find = MagicMock(return_value=_Iter(runs))
        metrics = await m.agent_metrics(days=7)

    assert metrics["totalRuns"] == 3
    assert metrics["successRate"] == 66.7
    assert metrics["byMode"]["parser"] == 1
    assert metrics["topTools"][0]["tool"] == "find_lead"


@pytest.mark.asyncio
async def test_agent_health_reports_llm_flag():
    with patch("app.services.agent_metrics.db") as mock_db, \
         patch("app.services.crm_agent_service._llm_available", new_callable=AsyncMock, return_value=True), \
         patch("app.services.llm_settings_service.get_llm_settings", new_callable=AsyncMock) as mock_cfg:
        mock_cfg.return_value = {
            "provider": "custom",
            "model": "test-model",
            "baseUrl": "",
            "apiKeySet": True,
        }
        mock_db.__getitem__.return_value.count_documents = AsyncMock(return_value=2)
        h = await m.agent_health()
    assert h["ok"] is True
    assert h["llmAvailable"] is True
    assert h["pendingApprovals"] == 2


def test_health_endpoint():
    with patch("app.services.agent_metrics.agent_health", new_callable=AsyncMock) as mock_h:
        mock_h.return_value = {"ok": True, "llmAvailable": False}
        resp = client.get("/api/v1/agent/health")
    assert resp.status_code == 200
    assert resp.json()["ok"] is True


def test_metrics_endpoint():
    with patch("app.services.agent_metrics.agent_metrics", new_callable=AsyncMock) as mock_m:
        mock_m.return_value = {"totalRuns": 1, "successRate": 100}
        resp = client.get("/api/v1/agent/metrics?days=7")
    assert resp.status_code == 200
    assert resp.json()["totalRuns"] == 1


def test_approval_decision_executes_tool():
    with patch("app.services.agent_governance.resolve_approval", new_callable=AsyncMock) as mock_res, \
         patch("app.services.crm_agent_service.run_tool", new_callable=AsyncMock) as mock_tool:
        mock_res.return_value = {
            "tool": "send_email",
            "args": {"toEmail": "a@b.it", "subject": "S", "body": "B"},
            "userId": "u1",
            "status": "approved",
        }
        mock_tool.return_value = {"ok": True, "message": "Email inviata"}
        resp = client.post(
            "/api/v1/agent/approvals/appr1/decision",
            json={"approve": True},
        )
    data = resp.json()
    assert data["ok"] is True
    assert data["status"] == "approved"
    # confirm forzato a true
    assert mock_tool.await_args.args[1]["confirm"] is True
    assert data["message"] == "Email inviata"
