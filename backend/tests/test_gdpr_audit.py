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
            ref = MagicMock()
            ref.set = AsyncMock()
            mock_db.collection.return_value.document.return_value = ref

            consent_id = await log_consent(
                lead_id="lead-001",
                action="granted",
                purpose="marketing",
                consent_text="Acconsento.",
                ip="1.2.3.4",
            )

        assert consent_id is not None
        payload = ref.set.call_args.args[0]

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
            ref = MagicMock()
            ref.set = AsyncMock()
            mock_db.collection.return_value.document.return_value = ref

            await log_consent("lead-001", "granted", "marketing", "Acconsento.", "1.2.3.4")

        payload = ref.set.call_args.args[0]
        required_fields = {"leadId", "action", "purpose", "consentText",
                           "policyVersion", "ipAddress", "createdAt", "dataHash"}
        assert required_fields.issubset(payload.keys())

    @pytest.mark.asyncio
    async def test_consent_append_only_no_update(self):
        """Il servizio gdpr deve solo SET (create), mai UPDATE o DELETE."""
        with patch("app.services.gdpr_service.db") as mock_db:
            ref = MagicMock()
            ref.set = AsyncMock()
            mock_db.collection.return_value.document.return_value = ref

            await log_consent("lead-001", "revoked", "marketing", "Revoco.", "1.2.3.4")

        ref.set.assert_called_once()
        ref.update.assert_not_called() if hasattr(ref, "update") else None


# ── GDPR Export (Art.20) ──────────────────────────────────────

class TestGdprExport:
    @pytest.mark.asyncio
    async def test_export_returns_all_data(self):
        mock_lead_snap = MagicMock()
        mock_lead_snap.exists = True
        mock_lead_snap.id = "lead-001"
        mock_lead_snap.to_dict.return_value = {
            "email": "user@test.com",
            "firstName": "Mario",
        }

        mock_activity = MagicMock()
        mock_activity.id = "act-001"
        mock_activity.to_dict.return_value = {"type": "form_submitted"}

        mock_consent = MagicMock()
        mock_consent.id = "con-001"
        mock_consent.to_dict.return_value = {"action": "granted", "purpose": "marketing"}

        async def mock_stream_activities():
            yield mock_activity

        async def mock_stream_consents():
            yield mock_consent

        async def mock_stream_tasks():
            return
            yield  # empty async generator

        with patch("app.services.gdpr_service.db") as mock_db:
            mock_db.collection.return_value.document.return_value.get = AsyncMock(
                return_value=mock_lead_snap
            )
            mock_db.collection.return_value.document.return_value\
                .collection.return_value.stream = mock_stream_activities

            # Setup consent query stream
            consent_query = MagicMock()
            consent_query.stream = mock_stream_consents
            mock_db.collection.return_value.where.return_value = consent_query

            result = await gdpr_export("lead-001")

        assert result["lead"]["email"] == "user@test.com"
        assert "exported_at" in result
        assert isinstance(result["activities"], list)
        assert isinstance(result["gdpr_consents"], list)

    @pytest.mark.asyncio
    async def test_export_structure_matches_gdpr_portability(self):
        """Art.20: l'export deve contenere tutti i dati dell'interessato."""
        mock_snap = MagicMock()
        mock_snap.exists = False

        async def empty_stream():
            return
            yield

        with patch("app.services.gdpr_service.db") as mock_db:
            mock_db.collection.return_value.document.return_value.get = AsyncMock(
                return_value=mock_snap
            )
            mock_db.collection.return_value.document.return_value\
                .collection.return_value.stream = empty_stream
            q = MagicMock()
            q.stream = empty_stream
            mock_db.collection.return_value.where.return_value = q

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
        with patch("app.services.gdpr_service.db") as mock_db:
            lead_ref = MagicMock()
            lead_ref.update = AsyncMock()
            consent_ref = MagicMock()
            consent_ref.set = AsyncMock()

            mock_db.collection.return_value.document.return_value = lead_ref
            # Per log_consent interno
            mock_db.collection.return_value.document.side_effect = None

            def collection_router(name):
                coll = MagicMock()
                if name == "leads":
                    coll.document.return_value = lead_ref
                else:
                    coll.document.return_value = consent_ref
                return coll

            mock_db.collection.side_effect = collection_router

            await gdpr_erase("lead-001", "admin-uid")

        anonymized = lead_ref.update.call_args.args[0]
        assert anonymized["firstName"] == "CANCELLATO"
        assert anonymized["lastName"] == "GDPR"
        assert "deleted.invalid" in anonymized["email"]
        assert anonymized["phone"] is None
        assert anonymized["linkedinUrl"] is None
        assert anonymized["notes"] is None

    @pytest.mark.asyncio
    async def test_erase_does_not_delete_document(self):
        """Art.17: il documento deve esistere ancora dopo l'erase (anonimizzato)."""
        with patch("app.services.gdpr_service.db") as mock_db:
            ref = MagicMock()
            ref.update = AsyncMock()
            ref.delete = MagicMock()
            consent_ref = MagicMock()
            consent_ref.set = AsyncMock()

            def collection_router(name):
                coll = MagicMock()
                coll.document.return_value = ref if name == "leads" else consent_ref
                return coll

            mock_db.collection.side_effect = collection_router

            await gdpr_erase("lead-001", "admin-uid")

        ref.delete.assert_not_called()
        ref.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_erase_logs_deletion_consent(self):
        """Ogni cancellazione deve generare un consent record GDPR."""
        with patch("app.services.gdpr_service.db") as mock_db:
            lead_ref = MagicMock()
            lead_ref.update = AsyncMock()
            consent_ref = MagicMock()
            consent_ref.set = AsyncMock()

            def collection_router(name):
                coll = MagicMock()
                coll.document.return_value = lead_ref if name == "leads" else consent_ref
                return coll

            mock_db.collection.side_effect = collection_router

            await gdpr_erase("lead-001", "admin-uid")

        consent_ref.set.assert_called_once()
        consent_payload = consent_ref.set.call_args.args[0]
        assert consent_payload["action"] == "deletion_completed"


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
