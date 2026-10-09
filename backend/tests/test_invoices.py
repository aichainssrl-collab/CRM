"""
Test invoices router.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from app.main import app
from app.deps import require_sales, UserRecord

client = TestClient(app)
_SALES_USER = UserRecord(uid="user_sales", role="sales", email="sales@test.com")

_INVOICE = {
    "id": "inv-1",
    "number": "INV-2026-0001",
    "title": "Fattura ZenTratto",
    "clientName": "Studio Rossi",
    "status": "draft",
    "items": [{"name": "ZenTratto", "quantity": 1, "unitPrice": 15000, "total": 15000}],
    "subtotal": 15000,
    "taxRate": 22,
    "taxAmount": 3300,
    "total": 18300,
    "currency": "EUR",
}


@pytest.fixture(autouse=True)
def override_auth():
    app.dependency_overrides[require_sales] = lambda: _SALES_USER
    yield
    app.dependency_overrides.pop(require_sales, None)


def test_list_invoices():
    with patch(
        "app.routers.invoices.invoice_service.list_invoices",
        new_callable=AsyncMock,
        return_value=[_INVOICE],
    ):
        resp = client.get("/api/v1/invoices/")
    assert resp.status_code == 200
    assert resp.json()[0]["number"] == "INV-2026-0001"


def test_create_invoice():
    with patch(
        "app.routers.invoices.invoice_service.create_invoice",
        new_callable=AsyncMock,
        return_value=_INVOICE,
    ):
        resp = client.post(
            "/api/v1/invoices/",
            json={"title": "Fattura ZenTratto", "items": [{"name": "ZenTratto", "quantity": 1, "unitPrice": 15000}]},
        )
    assert resp.status_code == 200
    assert resp.json()["status"] == "draft"


def test_invoice_from_proposal():
    with patch(
        "app.routers.invoices.invoice_service.create_from_proposal",
        new_callable=AsyncMock,
        return_value=_INVOICE,
    ):
        resp = client.post("/api/v1/invoices/from-proposal/prop-1")
    assert resp.status_code == 200
    assert resp.json()["number"].startswith("INV-")


def test_invoice_from_proposal_not_found():
    with patch(
        "app.routers.invoices.invoice_service.create_from_proposal",
        new_callable=AsyncMock,
        return_value=None,
    ):
        resp = client.post("/api/v1/invoices/from-proposal/missing")
    assert resp.status_code == 404


def test_mark_paid():
    paid = {**_INVOICE, "status": "paid"}
    with patch(
        "app.routers.invoices.invoice_service.mark_paid",
        new_callable=AsyncMock,
        return_value=paid,
    ):
        resp = client.post("/api/v1/invoices/inv-1/mark-paid")
    assert resp.status_code == 200
    assert resp.json()["status"] == "paid"


def test_send_invoice():
    sent = {**_INVOICE, "status": "sent"}
    with patch(
        "app.routers.invoices.invoice_service.mark_sent",
        new_callable=AsyncMock,
        return_value=sent,
    ), patch(
        "app.services.document_service.record_pdf",
        new_callable=AsyncMock,
        return_value={"id": "d1", "version": 1, "checksum": "x"},
    ), patch(
        "app.services.email_service.send_email",
        new_callable=AsyncMock,
        return_value="mock-id",
    ):
        resp = client.post("/api/v1/invoices/inv-1/send")
    assert resp.status_code == 200
    assert resp.json()["status"] == "sent"


def test_cancel_invoice():
    cancelled = {**_INVOICE, "status": "cancelled"}
    with patch(
        "app.routers.invoices.invoice_service.mark_cancelled",
        new_callable=AsyncMock,
        return_value=cancelled,
    ):
        resp = client.post("/api/v1/invoices/inv-1/cancel")
    assert resp.status_code == 200
    assert resp.json()["status"] == "cancelled"


def test_delete_invoice():
    with patch(
        "app.routers.invoices.invoice_service.delete_invoice",
        new_callable=AsyncMock,
        return_value=True,
    ):
        resp = client.delete("/api/v1/invoices/inv-1")
    assert resp.status_code == 200
    assert resp.json()["ok"] is True


def test_invoice_stats():
    stats = {
        "totalCount": 2,
        "totalValue": 36600,
        "paidValue": 18300,
        "outstandingValue": 18300,
        "byStatus": {"paid": {"count": 1, "totalValue": 18300}, "sent": {"count": 1, "totalValue": 18300}},
    }
    with patch(
        "app.routers.invoices.invoice_service.invoice_stats",
        new_callable=AsyncMock,
        return_value=stats,
    ):
        resp = client.get("/api/v1/invoices/stats")
    assert resp.status_code == 200
    assert resp.json()["paidValue"] == 18300
