import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.deal_service import create_deal, get_deal, update_deal, delete_deal, list_deals
from app.schemas.deal import DealCreate, DealUpdate

@pytest.mark.asyncio
async def test_create_deal():
    with patch("app.services.deal_service.create_document", new_callable=AsyncMock) as mock_create:
        mock_create.return_value = {"id": "deal_123", "leadId": "lead_1", "title": "Test Deal"}
        with patch("app.services.deal_service.append_activity", new_callable=AsyncMock) as mock_append:
            
            data = DealCreate(title="Test Deal", stage="new", probability=50)
            result = await create_deal(data, lead_id="lead_1", created_by="user_1")
            
            assert result["id"] == "deal_123"
            mock_create.assert_called_once()
            mock_append.assert_called_once()

@pytest.mark.asyncio
async def test_get_deal():
    with patch("app.services.deal_service.get_document", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = {"id": "deal_123"}
        
        result = await get_deal("deal_123")
        assert result["id"] == "deal_123"
        mock_get.assert_called_once_with("deals", "deal_123")

@pytest.mark.asyncio
async def test_update_deal():
    with patch("app.services.deal_service.update_document", new_callable=AsyncMock) as mock_update:
        mock_update.return_value = {"id": "deal_123", "leadId": "lead_1", "stage": "won"}
        with patch("app.services.deal_service.append_activity", new_callable=AsyncMock) as mock_append:
            
            data = DealUpdate(stage="won")
            result = await update_deal("deal_123", data, "user_1")
            
            assert result["stage"] == "won"
            mock_update.assert_called_once()
            mock_append.assert_called_once()

@pytest.mark.asyncio
async def test_delete_deal():
    with patch("app.services.deal_service.soft_delete", new_callable=AsyncMock) as mock_del:
        await delete_deal("deal_123")
        mock_del.assert_called_once_with("deals", "deal_123")

@pytest.mark.asyncio
async def test_list_deals():
    with patch("app.services.deal_service.list_collection", new_callable=AsyncMock) as mock_list:
        mock_list.return_value = [{"id": "deal_123"}]
        
        results = await list_deals(lead_id="lead_1")
        assert len(results) == 1
        mock_list.assert_called_once()
