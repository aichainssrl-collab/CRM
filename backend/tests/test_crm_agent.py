"""
CRM Agent — parser + tool tests (offline, no LLM).
"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.deps import require_sales, UserRecord
from app.services import crm_agent_service

client = TestClient(app)
_USER = UserRecord(uid="agent-user", role="admin", email="agent@test.com")


@pytest.fixture(autouse=True)
def override_auth():
    app.dependency_overrides[require_sales] = lambda: _USER
    yield
    app.dependency_overrides.pop(require_sales, None)


# ── parser ───────────────────────────────────────────────────────────────────

def test_parse_create_lead():
    parsed = crm_agent_service.parse_command(
        "Crea lead Mario Rossi email mario@studio.it"
    )
    assert parsed is not None
    name, args = parsed
    assert name == "create_lead"
    assert args["email"] == "mario@studio.it"
    assert args["firstName"] == "Mario"
    assert args["lastName"] == "Rossi"


def test_parse_create_task_with_due_date():
    parsed = crm_agent_service.parse_command(
        "Crea task Chiama Mario entro 2026-02-01 email mario@studio.it urgente"
    )
    assert parsed is not None
    name, args = parsed
    assert name == "create_task"
    assert "Chiama" in args["title"]
    assert args["dueDate"] == "2026-02-01"
    assert args["priority"] == "high"


def test_parse_draft_email():
    parsed = crm_agent_service.parse_command(
        "Bozza email a mario@studio.it oggetto Demo testo Ciao come stai"
    )
    assert parsed is not None
    name, args = parsed
    assert name == "draft_email"
    assert args["toEmail"] == "mario@studio.it"
    assert args["subject"] == "Demo"
    assert "Ciao" in args["body"]


def test_parse_list_leads():
    parsed = crm_agent_service.parse_command("Mostra i lead")
    assert parsed == ("list_leads", {"limit": 10})


def test_parse_unknown():
    assert crm_agent_service.parse_command("ciao come va?") is None


# ── tools via API ────────────────────────────────────────────────────────────

def test_tools_list():
    resp = client.get("/api/v1/agent/tools")
    assert resp.status_code == 200
    names = {t["function"]["name"] for t in resp.json()["tools"]}
    assert {"create_lead", "create_task", "draft_email", "send_email", "list_leads"} <= names


def test_run_create_lead_via_agent():
    mock_col = MagicMock()
    mock_col.find_one = AsyncMock(return_value=None)
    mock_col.insert_one = AsyncMock()

    with patch("app.services.crm_agent_service.db") as mock_db:
        mock_db.__getitem__ = MagicMock(return_value=mock_col)
        resp = client.post(
            "/api/v1/agent/run",
            json={"message": "Crea lead Anna Neri email anna@neri.it"},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["mode"] == "parser"
    assert data["ok"] is True
    assert mock_col.insert_one.await_count == 1
    assert "anna@neri.it" in data["reply"]


def test_run_create_task_via_agent():
    mock_tasks = MagicMock()
    mock_tasks.insert_one = AsyncMock()
    mock_leads = MagicMock()
    mock_leads.find_one = AsyncMock(return_value={"_id": "L1", "email": "a@b.com"})

    def get_col(name):
        return {"tasks": mock_tasks, "leads": mock_leads}[name]

    with patch("app.services.crm_agent_service.db") as mock_db:
        mock_db.__getitem__ = MagicMock(side_effect=get_col)
        resp = client.post(
            "/api/v1/agent/run",
            json={"message": "crea task Follow-up call email a@b.com"},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert mock_tasks.insert_one.await_count == 1


def test_direct_tool_endpoint():
    mock_col = MagicMock()
    mock_col.find_one = AsyncMock(return_value=None)
    mock_col.insert_one = AsyncMock()

    with patch("app.services.crm_agent_service.db") as mock_db:
        mock_db.__getitem__ = MagicMock(return_value=mock_col)
        resp = client.post(
            "/api/v1/agent/tools/create_lead",
            json={"args": {"email": "tool@test.com", "firstName": "Tool"}},
        )

    assert resp.status_code == 200
    assert resp.json()["ok"] is True


def test_duplicate_lead_rejected():
    mock_col = MagicMock()
    mock_col.find_one = AsyncMock(return_value={"_id": "existing", "email": "dup@test.com"})
    mock_col.insert_one = AsyncMock()

    with patch("app.services.crm_agent_service.db") as mock_db:
        mock_db.__getitem__ = MagicMock(return_value=mock_col)
        resp = client.post(
            "/api/v1/agent/run",
            json={"message": "crea lead email dup@test.com"},
        )

    data = resp.json()
    assert data["ok"] is False
    assert "già presente" in data["reply"]
    assert mock_col.insert_one.await_count == 0
