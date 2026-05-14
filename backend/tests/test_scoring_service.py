import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.scoring_service import calculate_lead_score

@pytest.mark.asyncio
async def test_calculate_lead_score():
    with patch("app.services.scoring_service.db") as mock_db:
        mock_doc_ref = MagicMock()
        mock_doc_ref.update = AsyncMock()
        
        mock_snap = MagicMock()
        mock_snap.exists = True
        mock_snap.to_dict.return_value = {"roleSeniority": "manager", "budgetRange": "10k-50k", "timeline": "1_month"}
        
        mock_doc_ref.get = AsyncMock(return_value=mock_snap)
        mock_db.collection.return_value.document.return_value = mock_doc_ref
        
        score = await calculate_lead_score("lead_123")
        
        assert score > 0
        mock_doc_ref.update.assert_called_once()
