"""
Test workflows router + condition matching.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from app.main import app
from app.deps import require_sales, UserRecord

client = TestClient(app)
_SALES_USER = UserRecord(uid="user_sales", role="sales", email="sales@test.com")

_WORKFLOW = {
    "id": "wf-1",
    "name": "Legal lead follow-up",
    "description": "Auto task when legal lead arrives",
    "trigger": "lead_created",
    "conditions": [{"field": "industry", "op": "eq", "value": "Legal"}],
    "actions": [{"type": "create_task", "title": "Chiama il lead"}],
    "isActive": True,
    "runCount": 3,
}


@pytest.fixture(autouse=True)
def override_auth():
    app.dependency_overrides[require_sales] = lambda: _SALES_USER
    yield
    app.dependency_overrides.pop(require_sales, None)


def test_evaluate_condition_ops():
    from app.services.workflow_service import evaluate_condition, matches_conditions

    entity = {"status": "new", "score": 80, "tags": ["vip"], "industry": "Legal"}
    assert evaluate_condition(entity, {"field": "status", "op": "eq", "value": "new"}) is True
    assert evaluate_condition(entity, {"field": "status", "op": "ne", "value": "new"}) is False
    assert evaluate_condition(entity, {"field": "industry", "op": "contains", "value": "leg"}) is True
    assert evaluate_condition(entity, {"field": "score", "op": "gte", "value": 70}) is True
    assert evaluate_condition(entity, {"field": "score", "op": "lte", "value": 70}) is False
    assert evaluate_condition(entity, {"field": "tags", "op": "contains", "value": "vip"}) is True
    assert evaluate_condition(entity, {"field": "status", "op": "in", "value": ["new", "contacted"]}) is True
    assert matches_conditions(entity, [{"field": "industry", "op": "eq", "value": "Legal"}]) is True
    assert matches_conditions(entity, [{"field": "industry", "op": "eq", "value": "FinTech"}]) is False
    assert matches_conditions(entity, []) is True


def test_list_workflows():
    with patch(
        "app.routers.workflows.workflow_service.list_workflows",
        new_callable=AsyncMock,
        return_value=[_WORKFLOW],
    ):
        resp = client.get("/api/v1/workflows/")
    assert resp.status_code == 200
    assert resp.json()[0]["name"] == "Legal lead follow-up"


def test_create_workflow():
    with patch(
        "app.routers.workflows.workflow_service.create_workflow",
        new_callable=AsyncMock,
        return_value=_WORKFLOW,
    ):
        resp = client.post(
            "/api/v1/workflows/",
            json={
                "name": "Legal lead follow-up",
                "trigger": "lead_created",
                "conditions": [{"field": "industry", "op": "eq", "value": "Legal"}],
                "actions": [{"type": "create_task", "title": "Chiama il lead"}],
            },
        )
    assert resp.status_code == 200
    assert resp.json()["trigger"] == "lead_created"


def test_create_workflow_invalid_trigger():
    resp = client.post("/api/v1/workflows/", json={"name": "X", "trigger": "nope"})
    assert resp.status_code == 400


def test_create_workflow_invalid_action():
    resp = client.post(
        "/api/v1/workflows/",
        json={"name": "X", "trigger": "manual", "actions": [{"type": "drop_database"}]},
    )
    assert resp.status_code == 400


def test_toggle_workflow():
    toggled = {**_WORKFLOW, "isActive": False}
    with patch(
        "app.routers.workflows.workflow_service.toggle_workflow",
        new_callable=AsyncMock,
        return_value=toggled,
    ):
        resp = client.post("/api/v1/workflows/wf-1/toggle")
    assert resp.status_code == 200
    assert resp.json()["isActive"] is False


def test_delete_workflow():
    with patch(
        "app.routers.workflows.workflow_service.delete_workflow",
        new_callable=AsyncMock,
        return_value=True,
    ):
        resp = client.delete("/api/v1/workflows/wf-1")
    assert resp.status_code == 200
    assert resp.json()["ok"] is True


def test_fire_trigger():
    results = [{"workflowId": "wf-1", "name": "Legal lead follow-up", "actions": [{"type": "create_task", "ok": True}]}]
    with patch(
        "app.routers.workflows.workflow_service.run_workflows",
        new_callable=AsyncMock,
        return_value=results,
    ):
        resp = client.post(
            "/api/v1/workflows/trigger",
            json={"trigger": "lead_created", "entity": {"id": "l1", "industry": "Legal"}},
        )
    assert resp.status_code == 200
    assert resp.json()["fired"] == 1
    assert resp.json()["results"][0]["workflowId"] == "wf-1"


def test_workflow_stats():
    stats = {"total": 4, "active": 2, "topRuns": [{"id": "wf-1", "name": "A", "runCount": 9}]}
    with patch(
        "app.routers.workflows.workflow_service.workflow_stats",
        new_callable=AsyncMock,
        return_value=stats,
    ):
        resp = client.get("/api/v1/workflows/stats")
    assert resp.status_code == 200
    assert resp.json()["active"] == 2
