import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.activity_service import append_activity, list_activities

@pytest.mark.asyncio
async def test_append_activity():
    with patch("app.services.activity_service.db") as mock_db:
        mock_doc_ref = MagicMock()
        mock_doc_ref.set = AsyncMock()
        
        # mock update per contatori
        mock_lead_ref = MagicMock()
        mock_lead_ref.update = AsyncMock()
        mock_lead_ref.collection.return_value.document.return_value = mock_doc_ref
        
        mock_db.collection.return_value.document.return_value = mock_lead_ref
        
        with patch("app.services.activity_service._increment"):
            lead_id = "lead_123"
            data = {"type": "note", "title": "Test note"}
            
            result = await append_activity(lead_id, data)
            
            assert "id" in result
            assert result["type"] == "note"
            assert "createdAt" in result
            mock_doc_ref.set.assert_called_once()

@pytest.mark.asyncio
async def test_list_activities():
    with patch("app.services.activity_service.db") as mock_db:
        mock_snap = MagicMock()
        mock_snap.id = "act_1"
        mock_snap.to_dict.return_value = {"type": "note"}
        
        async def mock_async_gen():
            yield mock_snap
            
        mock_db.collection.return_value.document.return_value.collection.return_value.order_by.return_value.limit.return_value.stream = mock_async_gen
        
        results = await list_activities("lead_123", limit=10)
        
        assert len(results) == 1
        assert results[0]["id"] == "act_1"
        assert results[0]["type"] == "note"
