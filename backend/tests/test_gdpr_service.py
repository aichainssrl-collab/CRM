import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.gdpr_service import log_consent, gdpr_erase

@pytest.mark.asyncio
async def test_log_consent():
    with patch("app.services.gdpr_service.db") as mock_db:
        mock_doc_ref = AsyncMock()
        mock_db.collection.return_value.document.return_value = mock_doc_ref
        
        lead_id = "lead_123"
        action = "granted"
        purpose = "marketing"
        consent_text = "Accetto marketing"
        ip = "127.0.0.1"

        consent_id = await log_consent(lead_id, action, purpose, consent_text, ip)
        
        assert consent_id is not None
        mock_doc_ref.set.assert_called_once()
        call_args = mock_doc_ref.set.call_args[0][0]
        assert call_args["leadId"] == lead_id
        assert call_args["dataHash"] is not None

@pytest.mark.asyncio
async def test_gdpr_erase():
    with patch("app.services.gdpr_service.db") as mock_db:
        mock_doc_ref = AsyncMock()
        mock_db.collection.return_value.document.return_value = mock_doc_ref
        
        with patch("app.services.gdpr_service.log_consent", new_callable=AsyncMock) as mock_log:
            lead_id = "lead_123"
            erased_by_uid = "admin_1"

            await gdpr_erase(lead_id, erased_by_uid)

            mock_doc_ref.update.assert_called_once()
            call_args = mock_doc_ref.update.call_args[0][0]
            assert call_args["firstName"] == "CANCELLATO"
            assert "deleted.invalid" in call_args["email"]
            mock_log.assert_called_once()
