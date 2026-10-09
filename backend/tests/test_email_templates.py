"""
Test email templates + process-due endpoint.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from app.main import app
from app.deps import require_sales, UserRecord

client = TestClient(app)
_SALES_USER = UserRecord(uid="user_sales", role="sales", email="sales@test.com")

_TEMPLATE = {
    "id": "tpl-1",
    "key": "welcome",
    "name": "Welcome / Playbook",
    "subject": "Ecco il tuo AiChain Playbook",
    "bodyHtml": "<p>Ciao</p>",
    "category": "nurture",
}


@pytest.fixture(autouse=True)
def override_auth():
    app.dependency_overrides[require_sales] = lambda: _SALES_USER
    yield
    app.dependency_overrides.pop(require_sales, None)


def test_list_templates_includes_defaults():
    with patch(
        "app.routers.email_templates.svc.list_templates",
        new_callable=AsyncMock,
        return_value=[_TEMPLATE],
    ):
        resp = client.get("/api/v1/email-templates/")
    assert resp.status_code == 200
    assert resp.json()[0]["key"] == "welcome"


def test_create_template():
    with patch(
        "app.routers.email_templates.svc.create_template",
        new_callable=AsyncMock,
        return_value=_TEMPLATE,
    ):
        resp = client.post(
            "/api/v1/email-templates/",
            json={"name": "Welcome / Playbook", "subject": "Hi", "bodyHtml": "<p>Ciao</p>"},
        )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Welcome / Playbook"


def test_update_template():
    updated = {**_TEMPLATE, "subject": "Nuovo subject"}
    with patch(
        "app.routers.email_templates.svc.update_template",
        new_callable=AsyncMock,
        return_value=updated,
    ):
        resp = client.patch("/api/v1/email-templates/tpl-1", json={"subject": "Nuovo subject"})
    assert resp.status_code == 200
    assert resp.json()["subject"] == "Nuovo subject"


def test_delete_template():
    with patch(
        "app.routers.email_templates.svc.delete_template",
        new_callable=AsyncMock,
        return_value=True,
    ):
        resp = client.delete("/api/v1/email-templates/tpl-1")
    assert resp.status_code == 200
    assert resp.json()["ok"] is True


def test_process_due_enrollments():
    with patch(
        "app.routers.email_sequences.svc.process_due_enrollments",
        new_callable=AsyncMock,
        return_value=3,
    ):
        resp = client.post("/api/v1/email-sequences/process-due")
    assert resp.status_code == 200
    assert resp.json()["processed"] == 3


def test_default_templates_content():
    from app.services.email_template_service import DEFAULT_TEMPLATES

    keys = {t["key"] for t in DEFAULT_TEMPLATES}
    assert keys == {"welcome", "case_study", "cost_of_inaction", "demo", "last_call"}
