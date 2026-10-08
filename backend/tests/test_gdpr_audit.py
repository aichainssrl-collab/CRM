"""
GDPR audit: export Art.20, erase Art.17, consent trail append-only.
"""
import pytest
import hashlib
import json
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.gdpr_service import log_consent, gdpr_export, gdpr_erase


# ── Consent Log ───────────────────────────────────────────────

class TestConsentLog:
    @pytest.mark.asyncio
    async def test_consent_logged_with_hash(self):
        with patch("app.services.gdpr_service.db") as mock_db:
            mock_col = AsyncMock()
            mock_db.__getitem__ = MagicMock(return_value=mock_col)
            mock_col.insert_one = AsyncMock()

            consent_id = await log_consent(
                lead_id="lead-001",
                action="granted",
                purpose="marketing",
                consent_text="Acconsento.",
                ip="1.2.3.4",
            )

        assert consent_id is not None
        insert_call = mock_col.insert_one.call_args[0][0]
        payload = {k: v for k, v in insert_call.items() if k != "_id"}

        # Hash SHA-256 presente e corretto
        assert "dataHash" in payload
        payload_without_hash = {k: v for k, v in payload.items() if k != "dataHash"}
        expected_hash = hashlib.sha256(
            json.dumps(payload_without_hash, default=str, sort_keys=True).encode()
        ).hexdigest()
        assert payload["dataHash"] == expected_hash

    @pytest.mark.asyncio
    async def test_consent_fields_complete(self):
        with patch("app.services.gdpr_service.db") as mock_db:
            mock_col = AsyncMock()
            mock_db.__getitem__ = MagicMock(return_value=mock_col)
            mock_col.insert_one = AsyncMock()

            await log_consent("lead-001", "granted", "marketing", "Acconsento.", "1.2.3.4")

        insert_call = mock_col.insert_one.call_args[0][0]
        required_fields = {"leadId", "action", "purpose", "consentText",
                           "policyVersion", "ipAddress", "createdAt", "dataHash"}
        assert required_fields.issubset(insert_call.keys())

    @pytest.mark.asyncio
    async def test_consent_append_only_no_update(self):
        """Il servizio gdpr deve solo INSERT, mai UPDATE o DELETE."""
        with patch("app.services.gdpr_service.db") as mock_db:
            mock_col = AsyncMock()
            mock_db.__getitem__ = MagicMock(return_value=mock_col)
            mock_col.insert_one = AsyncMock()

            await log_consent("lead-001", "revoked", "marketing", "Revoco.", "1.2.3.4")

        mock_col.insert_one.assert_called_once()
        mock_col.update_one.assert_not_called()


# ── GDPR Export (Art.20) ──────────────────────────────────────

class _AsyncDocIterator:
    """Reusable async iterator for mocking motor cursors in `async for`."""
    def __init__(self, docs):
        self._docs = iter(docs)
    def __aiter__(self):
        return self
    async def __anext__(self):
        try:
            return next(self._docs)
        except StopIteration:
            raise StopAsyncIteration


class TestGdprExport:
    @pytest.mark.asyncio
    async def test_export_returns_all_data(self):
        with (
            patch("app.services.gdpr_service.db") as mock_db,
            patch("app.services.gdpr_service.list_activities", new_callable=AsyncMock) as mock_activities,
        ):
            mock_col = MagicMock()
            mock_db.__getitem__ = MagicMock(return_value=mock_col)

            mock_col.find_one = AsyncMock(return_value={
                "_id": "lead-001", "email": "user@test.com", "firstName": "Mario",
            })

            # tasks cursor (empty async iterator)
            mock_tasks_cursor = MagicMock()
            mock_tasks_cursor.__aiter__ = MagicMock(return_value=_AsyncDocIterator([]))

            # consents cursor (one item)
            mock_consents_cursor = MagicMock()
            mock_consents_cursor.__aiter__ = MagicMock(return_value=_AsyncDocIterator([
                {"_id": "con-001", "action": "granted", "purpose": "marketing", "leadId": "lead-001"},
            ]))

            mock_col.find = MagicMock(side_effect=[mock_tasks_cursor, mock_consents_cursor])

            mock_activities.return_value = [
                {"id": "act-001", "type": "form_submitted", "leadId": "lead-001"},
            ]

            result = await gdpr_export("lead-001")

        assert result["lead"]["email"] == "user@test.com"
        assert result["lead"]["id"] == "lead-001"
        assert "exported_at" in result
        assert isinstance(result["activities"], list)
        assert isinstance(result["gdpr_consents"], list)

    @pytest.mark.asyncio
    async def test_export_structure_matches_gdpr_portability(self):
        """Art.20: l'export deve contenere tutti i dati dell'interessato."""
        with (
            patch("app.services.gdpr_service.db") as mock_db,
            patch("app.services.gdpr_service.list_activities", new_callable=AsyncMock) as mock_activities,
        ):
            mock_col = MagicMock()
            mock_db.__getitem__ = MagicMock(return_value=mock_col)
            mock_col.find_one = AsyncMock(return_value=None)

            mock_empty_cursor = MagicMock()
            mock_empty_cursor.__aiter__ = MagicMock(return_value=_AsyncDocIterator([]))
            mock_col.find = MagicMock(return_value=mock_empty_cursor)

            mock_activities.return_value = []

            result = await gdpr_export("lead-nonexistent")

        assert "lead" in result
        assert "activities" in result
        assert "tasks" in result
        assert "gdpr_consents" in result
        assert "exported_at" in result


# ── GDPR Erase (Art.17) ───────────────────────────────────────

class TestGdprErase:
    @pytest.mark.asyncio
    async def test_erase_anonymizes_pii(self):
        with (
            patch("app.services.gdpr_service.db") as mock_db,
            patch("app.services.gdpr_service.log_consent", new_callable=AsyncMock) as mock_log,
        ):
            mock_col = AsyncMock()
            mock_db.__getitem__ = MagicMock(return_value=mock_col)
            mock_col.update_one = AsyncMock()

            await gdpr_erase("lead-001", "admin-uid")

        call_args = mock_col.update_one.call_args[0]
        update_payload = call_args[1]["$set"]
        assert update_payload["firstName"] == "CANCELLATO"
        assert update_payload["lastName"] == "GDPR"
        assert "deleted.invalid" in update_payload["email"]
        assert update_payload["phone"] is None
        assert update_payload["linkedinUrl"] is None
        assert update_payload["notes"] is None

    @pytest.mark.asyncio
    async def test_erase_does_not_delete_document(self):
        """Art.17: il documento deve esistere ancora dopo l'erase (anonimizzato)."""
        with (
            patch("app.services.gdpr_service.db") as mock_db,
            patch("app.services.gdpr_service.log_consent", new_callable=AsyncMock) as mock_log,
        ):
            mock_col = AsyncMock()
            mock_db.__getitem__ = MagicMock(return_value=mock_col)
            mock_col.update_one = AsyncMock()
            mock_col.delete_one = MagicMock()

            await gdpr_erase("lead-001", "admin-uid")

        mock_col.delete_one.assert_not_called()
        mock_col.update_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_erase_logs_deletion_consent(self):
        """Ogni cancellazione deve generare un consent record GDPR."""
        with (
            patch("app.services.gdpr_service.db") as mock_db,
            patch("app.services.gdpr_service.log_consent", new_callable=AsyncMock) as mock_log,
        ):
            mock_col = AsyncMock()
            mock_db.__getitem__ = MagicMock(return_value=mock_col)
            mock_col.update_one = AsyncMock()

            await gdpr_erase("lead-001", "admin-uid")

        mock_log.assert_called_once()
        call_kwargs = mock_log.call_args.kwargs
        assert call_kwargs["action"] == "deletion_completed"


# ── Endpoint GDPR protetti ────────────────────────────────────

class TestGdprEndpoints:
    def test_export_requires_auth(self):
        from fastapi.testclient import TestClient
        from app.main import app
        c = TestClient(app)
        response = c.get("/api/v1/gdpr/lead-001/export")
        assert response.status_code == 403

    def test_erase_requires_admin(self):
        from fastapi.testclient import TestClient
        from app.main import app
        c = TestClient(app)
        response = c.post(
            "/api/v1/gdpr/lead-001/erase",
            json={"confirm": True},
            headers={"Authorization": "Bearer fake"},
        )
        # Senza token valido → 401/403
        assert response.status_code in (401, 403)