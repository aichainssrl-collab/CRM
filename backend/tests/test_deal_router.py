"""
Test HTTP router deals — POST /api/v1/deals, GET, PATCH, DELETE.
Tutti i test mockano Firebase Auth e MongoDB.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from app.main import app
from app.deps import require_sales, UserRecord

client = TestClient(app)

_SALES_USER = UserRecord(uid="user_sales", role="sales", email="sales@test.com")
_LEAD_DOC = {
    "id": "lead_abc",
    "email": "cliente@test.com",
    "firstName": "Mario",
    "lastName": "Rossi",
    "deletedAt": None,
}
_DEAL_DOC = {
    "id": "deal_xyz",
    "leadId": "lead_abc",
    "title": "Proposta ERP",
    "value": 5000.0,
    "probability": 60,
    "stage": "proposal",
    "createdBy": "user_sales",
    "deletedAt": None,
}


@pytest.fixture(autouse=True)
def override_auth():
    """Bypassa Firebase Auth per tutti i test di questo modulo."""
    app.dependency_overrides[require_sales] = lambda: _SALES_USER
    yield
    app.dependency_overrides.pop(require_sales, None)


# ── POST /api/v1/deals ────────────────────────────────────────────────────────

def test_create_deal_success():
    """Happy path: lead esiste → deal creato → 201."""
    with patch("app.routers.deals.get_document", new_callable=AsyncMock, return_value=_LEAD_DOC):
        with patch("app.routers.deals.create_deal", new_callable=AsyncMock, return_value=_DEAL_DOC) as mock_svc:
            response = client.post(
                "/api/v1/deals?lead_id=lead_abc",
                json={"title": "Proposta ERP", "stage": "proposal", "value": 5000, "probability": 60},
            )

    assert response.status_code == 201
    body = response.json()
    assert body["id"] == "deal_xyz"
    assert body["leadId"] == "lead_abc"
    assert body["title"] == "Proposta ERP"
    mock_svc.assert_called_once()
    # verifica che lead_id e created_by siano passati correttamente
    _, kwargs = mock_svc.call_args
    assert kwargs.get("lead_id") == "lead_abc"
    assert kwargs.get("created_by") == _SALES_USER.uid


def test_create_deal_lead_not_found():
    """Se il lead non esiste → 404 Lead non trovato."""
    with patch("app.routers.deals.get_document", new_callable=AsyncMock, return_value=None):
        response = client.post(
            "/api/v1/deals?lead_id=nonexistent",
            json={"title": "Deal X", "stage": "new", "probability": 10},
        )

    assert response.status_code == 404
    assert "Lead non trovato" in response.json()["detail"]


def test_create_deal_missing_lead_id_query_param():
    """Senza ?lead_id=... → FastAPI risponde 422 Unprocessable Entity."""
    response = client.post(
        "/api/v1/deals",
        json={"title": "Deal X", "stage": "new", "probability": 10},
    )
    assert response.status_code == 422


def test_create_deal_missing_required_body_fields():
    """Body senza 'title' o 'stage' → 422."""
    with patch("app.routers.deals.get_document", new_callable=AsyncMock, return_value=_LEAD_DOC):
        response = client.post(
            "/api/v1/deals?lead_id=lead_abc",
            json={"value": 1000},  # title e stage mancanti
        )
    assert response.status_code == 422


def test_create_deal_minimal_body():
    """Solo title e stage (campi obbligatori) sono sufficienti."""
    minimal_deal = {**_DEAL_DOC, "value": None, "probability": 0}
    with patch("app.routers.deals.get_document", new_callable=AsyncMock, return_value=_LEAD_DOC):
        with patch("app.routers.deals.create_deal", new_callable=AsyncMock, return_value=minimal_deal):
            response = client.post(
                "/api/v1/deals?lead_id=lead_abc",
                json={"title": "Primo contatto", "stage": "new"},
            )
    assert response.status_code == 201


# ── GET /api/v1/deals ─────────────────────────────────────────────────────────

def test_list_deals():
    with patch("app.routers.deals.list_deals", new_callable=AsyncMock, return_value=[_DEAL_DOC]):
        response = client.get("/api/v1/deals")

    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert response.json()[0]["id"] == "deal_xyz"


def test_list_deals_filtered_by_lead():
    with patch("app.routers.deals.list_deals", new_callable=AsyncMock, return_value=[_DEAL_DOC]) as mock_list:
        response = client.get("/api/v1/deals?lead_id=lead_abc")

    assert response.status_code == 200
    _, kwargs = mock_list.call_args
    assert kwargs.get("lead_id") == "lead_abc"


def test_list_deals_empty():
    with patch("app.routers.deals.list_deals", new_callable=AsyncMock, return_value=[]):
        response = client.get("/api/v1/deals")
    assert response.status_code == 200
    assert response.json() == []


# ── GET /api/v1/deals/{id} ────────────────────────────────────────────────────

def test_get_deal_found():
    with patch("app.routers.deals.get_deal", new_callable=AsyncMock, return_value=_DEAL_DOC):
        response = client.get("/api/v1/deals/deal_xyz")

    assert response.status_code == 200
    assert response.json()["id"] == "deal_xyz"


def test_get_deal_not_found():
    with patch("app.routers.deals.get_deal", new_callable=AsyncMock, return_value=None):
        response = client.get("/api/v1/deals/does_not_exist")

    assert response.status_code == 404
    assert "Deal non trovato" in response.json()["detail"]


# ── PATCH /api/v1/deals/{id} ──────────────────────────────────────────────────

def test_update_deal_success():
    updated = {**_DEAL_DOC, "stage": "won"}
    with patch("app.routers.deals.get_deal", new_callable=AsyncMock, return_value=_DEAL_DOC):
        with patch("app.routers.deals.update_deal", new_callable=AsyncMock, return_value=updated):
            response = client.patch("/api/v1/deals/deal_xyz", json={"stage": "won"})

    assert response.status_code == 200
    assert response.json()["stage"] == "won"


def test_update_deal_not_found():
    with patch("app.routers.deals.get_deal", new_callable=AsyncMock, return_value=None):
        response = client.patch("/api/v1/deals/no_deal", json={"stage": "won"})
    assert response.status_code == 404


# ── DELETE /api/v1/deals/{id} ─────────────────────────────────────────────────

def test_delete_deal_success():
    with patch("app.routers.deals.get_deal", new_callable=AsyncMock, return_value=_DEAL_DOC):
        with patch("app.routers.deals.delete_deal", new_callable=AsyncMock) as mock_del:
            response = client.delete("/api/v1/deals/deal_xyz")

    assert response.status_code == 204
    mock_del.assert_called_once_with("deal_xyz")


def test_delete_deal_not_found():
    with patch("app.routers.deals.get_deal", new_callable=AsyncMock, return_value=None):
        response = client.delete("/api/v1/deals/no_deal")
    assert response.status_code == 404
