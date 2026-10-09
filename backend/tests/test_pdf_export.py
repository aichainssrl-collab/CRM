"""
Phase 15 — PDF export for proposals/invoices (IT/EN, IVA 22%, document versioning).
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
    "notes": "Pagamento in unica soluzione",
}

_INVOICE = {
    "id": "inv-1",
    "number": "INV-2026-0001",
    "title": "Fattura ZenTratto",
    "clientName": "Studio Rossi",
    "clientEmail": "info@studiorossi.it",
    "status": "draft",
    "items": [{"name": "ZenTratto", "quantity": 1, "unitPrice": 15000, "total": 15000}],
    "subtotal": 15000,
    "taxRate": 22,
    "taxAmount": 3300,
    "total": 18300,
    "currency": "EUR",
    "issueDate": "2026-01-15",
    "dueDate": "2026-02-15",
}


@pytest.fixture(autouse=True)
def override_auth():
    app.dependency_overrides[require_sales] = lambda: _SALES_USER
    yield
    app.dependency_overrides.pop(require_sales, None)


def _reg(version=1, checksum="abc"):
    return {
        "id": "doc-1",
        "version": version,
        "checksum": checksum,
        "filename": "x.pdf",
    }


# --- unit: labels / totals / pdf bytes ---

def test_labels_it_en():
    from app.services.pdf_service import labels

    it = labels("it")
    en = labels("en")
    assert it["proposal"] == "PREVENTIVO"
    assert it["invoice"] == "FATTURA"
    assert it["vat"] == "IVA"
    assert en["proposal"] == "QUOTE"
    assert en["invoice"] == "INVOICE"
    assert en["vat"] == "VAT"
    assert labels("xx") is it  # fallback


def test_default_tax_rate_22():
    from app.services.proposal_service import compute_totals, DEFAULT_TAX_RATE

    assert DEFAULT_TAX_RATE == 22.0
    result = compute_totals([{"name": "A", "quantity": 1, "unitPrice": 100}])
    assert result["taxRate"] == 22
    assert result["taxAmount"] == 22
    assert result["total"] == 122


def test_explicit_zero_tax_still_allowed():
    from app.services.proposal_service import compute_totals

    result = compute_totals([{"name": "A", "quantity": 1, "unitPrice": 100}], tax_rate=0)
    assert result["taxRate"] == 0
    assert result["taxAmount"] == 0
    assert result["total"] == 100


def test_proposal_pdf_magic_and_labels():
    from app.services.pdf_service import proposal_pdf

    for lang, needle in (("it", b"PREVENTIVO"), ("en", b"QUOTE")):
        data = proposal_pdf(_PROPOSAL, lang=lang)
        assert data.startswith(b"%PDF")
        assert needle in data
        assert b"Iva" in data or b"IVA" in data or b"VAT" in data


def test_invoice_pdf_magic_and_labels():
    from app.services.pdf_service import invoice_pdf

    data_it = invoice_pdf(_INVOICE, lang="it")
    data_en = invoice_pdf(_INVOICE, lang="en")
    assert data_it.startswith(b"%PDF")
    assert data_en.startswith(b"%PDF")
    assert b"FATTURA" in data_it
    assert b"INVOICE" in data_en


def test_money_format_it_en():
    from app.services.pdf_service import _money

    assert _money(1234.5, "it") == "1.234,50 EUR"
    assert _money(1234.5, "en") == "1,234.50 EUR"


# --- API: PDF endpoints ---

def test_proposal_pdf_endpoint_it():
    with patch(
        "app.routers.proposals.proposal_service.get_proposal",
        new_callable=AsyncMock,
        return_value=_PROPOSAL,
    ), patch(
        "app.services.document_service.record_pdf",
        new_callable=AsyncMock,
        return_value=_reg(),
    ):
        resp = client.get("/api/v1/proposals/prop-1/pdf?lang=it")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/pdf"
    assert resp.content.startswith(b"%PDF")
    assert "PROP-2026-0001_it.pdf" in resp.headers["content-disposition"]
    assert resp.headers["x-document-version"] == "1"
    assert resp.headers["x-document-checksum"] == "abc"


def test_proposal_pdf_endpoint_en():
    with patch(
        "app.routers.proposals.proposal_service.get_proposal",
        new_callable=AsyncMock,
        return_value=_PROPOSAL,
    ), patch(
        "app.services.document_service.record_pdf",
        new_callable=AsyncMock,
        return_value=_reg(),
    ):
        resp = client.get("/api/v1/proposals/prop-1/pdf?lang=en")
    assert resp.status_code == 200
    assert b"QUOTE" in resp.content
    assert "PROP-2026-0001_en.pdf" in resp.headers["content-disposition"]


def test_proposal_pdf_soft_deleted_404():
    with patch(
        "app.routers.proposals.proposal_service.get_proposal",
        new_callable=AsyncMock,
        return_value=None,
    ):
        resp = client.get("/api/v1/proposals/gone/pdf")
    assert resp.status_code == 404


def test_invoice_pdf_endpoint():
    with patch(
        "app.routers.invoices.invoice_service.get_invoice",
        new_callable=AsyncMock,
        return_value=_INVOICE,
    ), patch(
        "app.services.document_service.record_pdf",
        new_callable=AsyncMock,
        return_value=_reg(),
    ):
        resp = client.get("/api/v1/invoices/inv-1/pdf?lang=it")
    assert resp.status_code == 200
    assert resp.content.startswith(b"%PDF")
    assert b"FATTURA" in resp.content
    assert "INV-2026-0001_it.pdf" in resp.headers["content-disposition"]


def test_invoice_pdf_not_found():
    with patch(
        "app.routers.invoices.invoice_service.get_invoice",
        new_callable=AsyncMock,
        return_value=None,
    ):
        resp = client.get("/api/v1/invoices/missing/pdf")
    assert resp.status_code == 404


def test_send_proposal_attaches_pdf():
    sent = {**_PROPOSAL, "status": "sent", "clientEmail": "info@studiorossi.it"}
    with patch(
        "app.routers.proposals.proposal_service.mark_sent",
        new_callable=AsyncMock,
        return_value=sent,
    ), patch(
        "app.services.document_service.record_pdf",
        new_callable=AsyncMock,
        return_value=_reg(),
    ) as rec, patch(
        "app.services.email_service.send_email",
        new_callable=AsyncMock,
        return_value="mock-id",
    ) as mail:
        resp = client.post("/api/v1/proposals/prop-1/send", json={"lang": "it", "sendEmail": True})
    assert resp.status_code == 200
    assert resp.json()["status"] == "sent"
    rec.assert_awaited_once()
    mail.assert_awaited_once()
    kwargs = mail.call_args.kwargs
    assert kwargs["to"] == "info@studiorossi.it"
    assert kwargs["attachments"][0]["filename"] == "PROP-2026-0001_it.pdf"


def test_send_invoice_no_email_when_missing():
    sent = {**_INVOICE, "status": "sent", "clientEmail": ""}
    with patch(
        "app.routers.invoices.invoice_service.mark_sent",
        new_callable=AsyncMock,
        return_value=sent,
    ), patch(
        "app.services.document_service.record_pdf",
        new_callable=AsyncMock,
        return_value=_reg(),
    ), patch(
        "app.services.email_service.send_email",
        new_callable=AsyncMock,
        return_value="mock-id",
    ) as mail:
        resp = client.post("/api/v1/invoices/inv-1/send", json={"lang": "it"})
    assert resp.status_code == 200
    mail.assert_not_called()


# --- document_service versioning ---

@pytest.mark.asyncio
async def test_document_version_increments_on_content_change():
    from app.services import document_service

    mock_col = MagicMock()
    mock_col.find_one = AsyncMock(
        side_effect=[
            None,  # no identical checksum
            {"_id": "prev", "version": 2},  # previous version
        ]
    )
    mock_col.insert_one = AsyncMock()
    mock_db = MagicMock()
    mock_db.__getitem__ = MagicMock(return_value=mock_col)

    with patch("app.services.document_service.db", mock_db):
        doc = await document_service.record_pdf(
            parent_type="proposal",
            parent_id="prop-1",
            data=b"%PDF-new",
            locale="it",
            generated_by="user_sales",
            filename="x.pdf",
        )
    assert doc["version"] == 3
    mock_col.insert_one.assert_awaited_once()


@pytest.mark.asyncio
async def test_document_reuses_version_on_same_checksum():
    from app.services import document_service

    existing = {
        "_id": "doc-1",
        "version": 1,
        "checksum": document_service.checksum(b"%PDF-same"),
        "parentType": "proposal",
        "parentId": "prop-1",
    }
    mock_col = MagicMock()
    mock_col.find_one = AsyncMock(return_value=existing)
    mock_col.insert_one = AsyncMock()
    mock_db = MagicMock()
    mock_db.__getitem__ = MagicMock(return_value=mock_col)

    with patch("app.services.document_service.db", mock_db):
        doc = await document_service.record_pdf(
            parent_type="proposal",
            parent_id="prop-1",
            data=b"%PDF-same",
            locale="it",
            generated_by="user_sales",
            filename="x.pdf",
        )
    assert doc["version"] == 1
    mock_col.insert_one.assert_not_called()
