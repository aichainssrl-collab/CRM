"""
Test proposals router.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
from app.main import app
from app.deps import require_sales, UserRecord

client = TestClient(app)
_SALES_USER = UserRecord(uid="user_sales", role="sales", email="sales@test.com")

_PROPOSAL = {
    "id": "prop-1",
    "number": "PROP-2026-0001",
    "title": "Offerta ZenTratto",
    "clientName": "Studio Rossi",
    "clientEmail": "info@studiorossi.it",
    "status": "draft",
    "items": [
        {"productId": "p1", "name": "ZenTratto", "quantity": 1, "unitPrice": 15000, "total": 15000}
    ],
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


def test_compute_totals_unit():
    from app.services.proposal_service import compute_totals

    result = compute_totals(
        [{"name": "A", "quantity": 2, "unitPrice": 100}, {"name": "B", "quantity": 1, "unitPrice": 50}],
        tax_rate=22,
    )
    assert result["subtotal"] == 250
    assert result["taxAmount"] == 55
    assert result["total"] == 305
    assert result["items"][0]["total"] == 200


def test_list_proposals():
    with patch(
        "app.routers.proposals.proposal_service.list_proposals",
        new_callable=AsyncMock,
        return_value=[_PROPOSAL],
    ):
        resp = client.get("/api/v1/proposals/")
    assert resp.status_code == 200
    assert resp.json()[0]["number"] == "PROP-2026-0001"


def test_create_proposal():
    with patch(
        "app.routers.proposals.proposal_service.create_proposal",
        new_callable=AsyncMock,
        return_value=_PROPOSAL,
    ):
        resp = client.post(
            "/api/v1/proposals/",
            json={
                "title": "Offerta ZenTratto",
                "clientName": "Studio Rossi",
                "items": [{"name": "ZenTratto", "quantity": 1, "unitPrice": 15000}],
                "taxRate": 22,
            },
        )
    assert resp.status_code == 200
    assert resp.json()["status"] == "draft"
    assert resp.json()["total"] == 18300


def test_get_proposal_not_found():
    with patch(
        "app.routers.proposals.proposal_service.get_proposal",
        new_callable=AsyncMock,
        return_value=None,
    ):
        resp = client.get("/api/v1/proposals/missing")
    assert resp.status_code == 404


def test_send_proposal():
    sent = {**_PROPOSAL, "status": "sent"}
    with patch(
        "app.routers.proposals.proposal_service.mark_sent",
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
        resp = client.post("/api/v1/proposals/prop-1/send")
    assert resp.status_code == 200
    assert resp.json()["status"] == "sent"


def test_accept_proposal():
    accepted = {**_PROPOSAL, "status": "accepted"}
    with patch(
        "app.routers.proposals.proposal_service.mark_accepted",
        new_callable=AsyncMock,
        return_value=accepted,
    ):
        resp = client.post("/api/v1/proposals/prop-1/accept")
    assert resp.status_code == 200
    assert resp.json()["status"] == "accepted"


def test_reject_proposal():
    rejected = {**_PROPOSAL, "status": "rejected"}
    with patch(
        "app.routers.proposals.proposal_service.mark_rejected",
        new_callable=AsyncMock,
        return_value=rejected,
    ):
        resp = client.post("/api/v1/proposals/prop-1/reject")
    assert resp.status_code == 200
    assert resp.json()["status"] == "rejected"


def test_delete_proposal():
    with patch(
        "app.routers.proposals.proposal_service.delete_proposal",
        new_callable=AsyncMock,
        return_value=True,
    ):
        resp = client.delete("/api/v1/proposals/prop-1")
    assert resp.status_code == 200
    assert resp.json()["ok"] is True


def test_proposal_stats():
    stats = {"totalCount": 3, "totalValue": 50000, "byStatus": {"draft": {"count": 2, "totalValue": 30000}}}
    with patch(
        "app.routers.proposals.proposal_service.proposal_stats",
        new_callable=AsyncMock,
        return_value=stats,
    ):
        resp = client.get("/api/v1/proposals/stats")
    assert resp.status_code == 200
    assert resp.json()["totalCount"] == 3
