"""
Test export router.
Mocks Firebase Auth and MongoDB.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from app.main import app
from app.deps import require_sales, UserRecord

client = TestClient(app)

_SALES_USER = UserRecord(uid="user_sales", role="sales", email="sales@test.com")

_LEADS_CSV = "ID,Nome,Cognome,Email\nlead-1,Mario,Rossi,mario@test.com\n"
_DEALS_CSV = "ID,Titolo,Valore\ndeal-1,Proposta ERP,5000\n"
_CONTACTS_CSV = "Email,Nome,Cognome\nmario@test.com,Mario,Rossi\n"


@pytest.fixture(autouse=True)
def override_auth():
    app.dependency_overrides[require_sales] = lambda: _SALES_USER
    yield
    app.dependency_overrides.pop(require_sales, None)


def test_export_leads_csv():
    """GET /api/v1/export/leads returns CSV."""
    with patch("app.routers.export.export_service.export_leads_csv", new_callable=AsyncMock, return_value=_LEADS_CSV):
        resp = client.get("/api/v1/export/leads")
    assert resp.status_code == 200
    assert "text/csv" in resp.headers["content-type"]
    assert "leads_export.csv" in resp.headers["content-disposition"]
    assert "Mario" in resp.text


def test_export_deals_csv():
    """GET /api/v1/export/deals returns CSV."""
    with patch("app.routers.export.export_service.export_deals_csv", new_callable=AsyncMock, return_value=_DEALS_CSV):
        resp = client.get("/api/v1/export/deals")
    assert resp.status_code == 200
    assert "deals_export.csv" in resp.headers["content-disposition"]


def test_export_contacts_csv():
    """GET /api/v1/export/contacts returns CSV."""
    with patch("app.routers.export.export_service.export_contacts_csv", new_callable=AsyncMock, return_value=_CONTACTS_CSV):
        resp = client.get("/api/v1/export/contacts")
    assert resp.status_code == 200
    assert "contacts_export.csv" in resp.headers["content-disposition"]


def test_export_with_filters():
    """GET /api/v1/export/leads?status=new passes filter."""
    with patch("app.routers.export.export_service.export_leads_csv", new_callable=AsyncMock, return_value=_LEADS_CSV) as mock_csv:
        client.get("/api/v1/export/leads?status=new&source=playbook")
    mock_csv.assert_called_once()
    filters = mock_csv.call_args[0][0]
    assert filters.get("status") == "new"
    assert filters.get("source") == "playbook"