import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.gdpr_service import log_consent, gdpr_erase


@pytest.mark.asyncio
async def test_log_consent():
    with patch("app.services.gdpr_service.db") as mock_db:
        mock_col = AsyncMock()
        mock_db.__getitem__ = MagicMock(return_value=mock_col)
        mock_col.insert_one = AsyncMock()

        lead_id = "lead_123"
        action = "granted"
        purpose = "marketing"
        consent_text = "Accetto marketing"
        ip = "127.0.0.1"

        consent_id = await log_consent(lead_id, action, purpose, consent_text, ip)

        assert consent_id is not None
        mock_col.insert_one.assert_called_once()
        insert_payload = mock_col.insert_one.call_args[0][0]
        assert insert_payload["leadId"] == lead_id
        assert insert_payload["dataHash"] is not None


@pytest.mark.asyncio
async def test_gdpr_erase():
    with (
        patch("app.services.gdpr_service.db") as mock_db,
        patch("app.services.gdpr_service.log_consent", new_callable=AsyncMock) as mock_log,
    ):
        mock_col = AsyncMock()
        mock_db.__getitem__ = MagicMock(return_value=mock_col)
        mock_col.update_one = AsyncMock()

        lead_id = "lead_123"
        erased_by_uid = "admin_1"

        await gdpr_erase(lead_id, erased_by_uid)

        mock_col.update_one.assert_called_once()
        call_args = mock_col.update_one.call_args[0]
        update_payload = call_args[1]["$set"]
        assert update_payload["firstName"] == "CANCELLATO"
        assert "deleted.invalid" in update_payload["email"]
        mock_log.assert_called_once()