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


def test_parse_list_deals_by_stage():
    parsed = crm_agent_service.parse_command("Mostra deal in trattativa")
    assert parsed is not None
    name, args = parsed
    assert name == "list_deals"
    assert args.get("stage") == "negotiation"


def test_parse_update_deal_stage():
    parsed = crm_agent_service.parse_command("Sposta deal ZenTratto in proposta")
    assert parsed is not None
    name, args = parsed
    assert name == "update_deal"
    assert args.get("stage") == "proposal"
    assert "ZenTratto" in args.get("title", "")


def test_parse_deadlines():
    parsed = crm_agent_service.parse_command("Scadenze dei prossimi 30 giorni")
    assert parsed is not None
    name, args = parsed
    assert name == "list_deadlines"
    assert args.get("days") == 30


def test_parse_reschedule_task():
    parsed = crm_agent_service.parse_command("Proroga task Call follow-up a 2026-03-01")
    assert parsed is not None
    name, args = parsed
    assert name == "reschedule_task"
    assert args.get("dueDate") == "2026-03-01"
    assert "Call" in args.get("title", "")


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


# ── deals + deadlines tools ──────────────────────────────────────────────────

def test_list_deals_tool():
    mock_col = MagicMock()
    mock_col.find = MagicMock()
    mock_col.find.return_value.sort.return_value.limit.return_value.to_list = AsyncMock(
        return_value=[
            {
                "_id": "d1",
                "title": "ZenTratto — Studio",
                "stage": "proposal",
                "value": 15000,
                "expectedClose": None,
                "leadId": "L1",
            }
        ]
    )
    with patch("app.services.crm_agent_service.db") as mock_db:
        mock_db.__getitem__ = MagicMock(return_value=mock_col)
        resp = client.post(
            "/api/v1/agent/run",
            json={"message": "Mostra i deal"},
        )
    data = resp.json()
    assert data["ok"] is True
    assert data["mode"] == "parser"
    assert "1 deal" in data["reply"] or "deal trovati" in data["reply"]


def test_update_deal_tool():
    deal = {"_id": "d1", "title": "ZenTratto — Studio", "stage": "new", "value": 0}
    mock_col = MagicMock()
    mock_col.find_one = AsyncMock(return_value=deal)
    mock_col.update_one = AsyncMock()

    with patch("app.services.crm_agent_service.db") as mock_db:
        mock_db.__getitem__ = MagicMock(return_value=mock_col)
        resp = client.post(
            "/api/v1/agent/run",
            json={"message": "Sposta deal ZenTratto in proposta"},
        )
    data = resp.json()
    assert data["ok"] is True
    assert mock_col.update_one.await_count == 1
    set_payload = mock_col.update_one.await_args.args[1]["$set"]
    assert set_payload["stage"] == "proposal"


def test_list_deadlines_tool():
    tasks_col = MagicMock()
    tasks_col.find = MagicMock()
    tasks_col.find.return_value.sort.return_value.limit.return_value.to_list = AsyncMock(
        return_value=[{"_id": "t1", "title": "Call follow-up", "dueDate": None, "priority": "high", "status": "open"}]
    )
    deals_col = MagicMock()
    deals_col.find = MagicMock()
    deals_col.find.return_value.sort.return_value.limit.return_value.to_list = AsyncMock(return_value=[])

    def get_col(name):
        return {"tasks": tasks_col, "deals": deals_col}[name]

    with patch("app.services.crm_agent_service.db") as mock_db:
        mock_db.__getitem__ = MagicMock(side_effect=get_col)
        resp = client.post(
            "/api/v1/agent/run",
            json={"message": "Scadenze dei prossimi 7 giorni"},
        )
    data = resp.json()
    assert data["ok"] is True
    assert "scadenze" in data["reply"].lower()


def test_reschedule_task_tool():
    from datetime import datetime, timezone

    task = {"_id": "t1", "title": "Call follow-up", "status": "open", "dueDate": datetime.now(timezone.utc)}
    mock_col = MagicMock()
    mock_col.find_one = AsyncMock(return_value=task)
    mock_col.update_one = AsyncMock()

    with patch("app.services.crm_agent_service.db") as mock_db:
        mock_db.__getitem__ = MagicMock(return_value=mock_col)
        resp = client.post(
            "/api/v1/agent/run",
            json={"message": "Proroga task Call follow-up a 2026-03-01"},
        )
    data = resp.json()
    assert data["ok"] is True
    assert mock_col.update_one.await_count == 1
    set_payload = mock_col.update_one.await_args.args[1]["$set"]
    assert set_payload["dueDate"].isoformat().startswith("2026-03-01")


# ── resilience / regression ──────────────────────────────────────────────────

def test_run_endpoint_never_500_on_internal_error():
    """Chat UI must get 200 + error payload even if the service explodes."""
    with patch(
        "app.routers.crm_agent.crm_agent_service.run_agent",
        side_effect=RuntimeError("boom"),
    ):
        resp = client.post(
            "/api/v1/agent/run",
            json={"message": "Crea lead Mario Rossi email mario@studio.it"},
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is False
    assert data["mode"] == "error"
    assert "boom" in data["reply"]


def test_create_lead_exact_user_message():
    """Regression: 'Crea lead Mario Rossi email mario@studio.it' must use parser."""
    mock_col = MagicMock()
    mock_col.find_one = AsyncMock(return_value=None)
    mock_col.insert_one = AsyncMock()

    with patch("app.services.crm_agent_service.db") as mock_db:
        mock_db.__getitem__ = MagicMock(return_value=mock_col)
        resp = client.post(
            "/api/v1/agent/run",
            json={"message": "Crea lead Mario Rossi email mario@studio.it"},
        )

    data = resp.json()
    assert resp.status_code == 200
    assert data["mode"] == "parser"
    assert data["ok"] is True
    assert data["steps"][0]["name"] == "create_lead"
    assert data["steps"][0]["args"]["email"] == "mario@studio.it"


# ── Resend email send ────────────────────────────────────────────────────────

def test_send_email_mock_resend_when_fake_key():
    from app.config import settings

    mock_leads = MagicMock()
    mock_leads.find_one = AsyncMock(
        return_value={"_id": "L1", "email": "a@b.com", "deletedAt": None}
    )
    mock_acts = MagicMock()
    mock_acts.insert_one = AsyncMock()

    def get_col(name):
        return {"leads": mock_leads, "activities": mock_acts}[name]

    with (
        patch("app.services.crm_agent_service.db") as mock_db,
        patch("app.services.email_service.settings") as es,
        patch("app.services.crm_agent_service.settings") as cs,
    ):
        mock_db.__getitem__ = MagicMock(side_effect=get_col)
        es.RESEND_API_KEY = "re_fake_key"
        es.EMAIL_FROM = "noreply@test.com"
        cs.RESEND_API_KEY = "re_fake_key"
        cs.EMAIL_FROM = "noreply@test.com"
        resp = client.post(
            "/api/v1/agent/run",
            json={
                "message": "invia email a a@b.com oggetto Ciao testo Come stai?",
            },
        )

    data = resp.json()
    assert resp.status_code == 200
    assert data["ok"] is True
    step = data["steps"][0]
    assert step["name"] == "send_email"
    assert step["result"]["sent"] is True
    assert step["result"]["mock"] is True
    assert step["result"]["provider"] == "mock"
    assert mock_acts.insert_one.await_count == 1


def test_send_email_real_resend_id_logged():
    """When Resend returns an id, agent reports sent + emailId and logs activity."""
    mock_leads = MagicMock()
    mock_leads.find_one = AsyncMock(
        return_value={"_id": "L1", "email": "c@d.com", "deletedAt": None}
    )
    mock_acts = MagicMock()
    mock_acts.insert_one = AsyncMock()

    def get_col(name):
        return {"leads": mock_leads, "activities": mock_acts}[name]

    with (
        patch("app.services.crm_agent_service.db") as mock_db,
        patch("app.services.email_service.send_email_ex") as mock_ex,
        patch("app.services.crm_agent_service.settings") as cs,
    ):
        mock_db.__getitem__ = MagicMock(side_effect=get_col)
        cs.RESEND_API_KEY = "re_real_key"
        cs.EMAIL_FROM = "noreply@test.com"
        mock_ex.return_value = {
            "ok": True,
            "id": "re_abc123xyz",
            "mock": False,
            "error": None,
            "from": "noreply@test.com",
        }
        resp = client.post(
            "/api/v1/agent/tools/send_email",
            json={
                "args": {
                    "toEmail": "c@d.com",
                    "subject": "Proposta",
                    "body": "Ciao,<br>eccola.",
                }
            },
        )

    data = resp.json()
    assert data["ok"] is True
    assert data["sent"] is True
    assert data["mock"] is False
    assert data["emailId"] == "re_abc123xyz"
    assert data["provider"] == "resend"
    assert mock_acts.insert_one.await_count == 1
    meta = mock_acts.insert_one.await_args.args[0]["metadata"]
    assert meta["emailId"] == "re_abc123xyz"
    assert meta["provider"] == "resend"


def test_send_email_failure_reports_error():
    with (
        patch("app.services.crm_agent_service.db") as mock_db,
        patch("app.services.email_service.send_email_ex") as mock_ex,
        patch("app.services.crm_agent_service.settings") as cs,
    ):
        mock_db.__getitem__ = MagicMock(return_value=MagicMock())
        mock_db["leads"].find_one = AsyncMock(return_value=None)
        cs.RESEND_API_KEY = "re_real_key"
        cs.EMAIL_FROM = "noreply@test.com"
        mock_ex.return_value = {
            "ok": False,
            "id": None,
            "mock": False,
            "error": "getaddrinfo failed",
            "from": "noreply@test.com",
        }
        resp = client.post(
            "/api/v1/agent/tools/send_email",
            json={"args": {"toEmail": "x@y.com", "subject": "S", "body": "B"}},
        )

    data = resp.json()
    assert data["ok"] is False
    assert data["sent"] is False
    assert "getaddrinfo" in (data.get("error") or "")
