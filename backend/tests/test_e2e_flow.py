import pytest
from contextlib import ExitStack
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch
from app.main import app


@pytest.fixture(autouse=True)
def clear_overrides():
    """Ensure dependency_overrides never leak between tests."""
    yield
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_e2e_public_form_to_lead_flow():
    """
    Flusso pubblico form → lead → task → GDPR export.
    Tutti i layer di servizio sono mockati (nessuna dipendenza Firestore).
    """
    with ExitStack() as stack:
        mock_create = stack.enter_context(
            patch("app.routers.forms.LeadService.create_or_update_from_form", new_callable=AsyncMock)
        )
        mock_create.return_value = {"id": "lead_e2e", "email": "elon.musk.e2e@tesla.com"}
        mock_log_consent = stack.enter_context(
            patch("app.routers.forms.log_consent", new_callable=AsyncMock)
        )
        stack.enter_context(patch("app.routers.forms.send_sales_notification", new_callable=AsyncMock))
        mock_enqueue = stack.enter_context(
            patch("app.routers.forms.enqueue_task", new_callable=AsyncMock)
        )

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # ── 1. Form pubblico (nessuna auth) ─────────────────────────────
            response = await client.post("/api/v1/forms/playbook", json={
                "firstName": "Elon",
                "lastName": "Musk",
                "companyName": "Tesla",
                "email": "elon.musk.e2e@tesla.com",
                "consent_given": True,
                "consent_text": "Accetto le policy e scarico il playbook",
            })
            assert response.status_code == 201
            data = response.json()
            assert data["success"] is True
            assert "download_url" in data
            mock_create.assert_called_once()
            mock_log_consent.assert_called_once()
            assert mock_enqueue.call_count == 2

            # ── 2. Bypass auth per operazioni CRM ───────────────────────────
            from app.deps import require_sales, UserRecord
            app.dependency_overrides[require_sales] = lambda: UserRecord(
                uid="user_e2e", role="sales", email="sales@aichain.it"
            )
            lead_id = "lead_e2e"

            # ── 3. Creazione task sul lead ───────────────────────────────────
            with patch("app.routers.tasks.get_document", new_callable=AsyncMock) as mock_lead_doc:
                mock_lead_doc.return_value = {"id": lead_id}
                with patch("app.routers.tasks.create_task", new_callable=AsyncMock) as mock_task:
                    mock_task.return_value = {"id": "task_1", "title": "Chiamare Elon"}
                    task_response = await client.post(f"/api/v1/leads/{lead_id}/tasks", json={
                        "title": "Chiamare Elon per followup",
                        "type": "call",
                        "priority": "high",
                        "assignedTo": "user_e2e",
                        "dueDate": "2026-12-31T10:00:00Z",
                    })
                    assert task_response.status_code == 201

            # ── 4. GDPR export (Art.20) ─────────────────────────────────────
            with patch("app.routers.gdpr.get_document", new_callable=AsyncMock) as mock_gdpr_doc:
                mock_gdpr_doc.return_value = {"id": lead_id, "email": "elon.musk.e2e@tesla.com"}
                with patch("app.routers.gdpr.gdpr_export", new_callable=AsyncMock) as mock_export:
                    mock_export.return_value = {
                        "lead": {"email": "elon.musk.e2e@tesla.com"},
                        "consents": [{"action": "granted"}],
                        "activities": [],
                        "tasks": [],
                        "exported_at": "2026-01-01T00:00:00Z",
                    }
                    gdpr_response = await client.get(f"/api/v1/gdpr/{lead_id}/export")
                    assert gdpr_response.status_code == 200
                    gdpr_data = gdpr_response.json()
                    assert gdpr_data["lead"]["email"] == "elon.musk.e2e@tesla.com"
                    assert gdpr_data["consents"][0]["action"] == "granted"
