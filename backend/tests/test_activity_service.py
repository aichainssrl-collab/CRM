import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.activity_service import append_activity, list_activities


@pytest.mark.asyncio
async def test_append_activity():
    with patch("app.services.activity_service.db") as mock_db:
        mock_col = AsyncMock()
        mock_db.__getitem__ = MagicMock(return_value=mock_col)
        mock_col.insert_one = AsyncMock()
        mock_col.update_one = AsyncMock()

        lead_id = "lead_123"
        data = {"type": "note", "title": "Test note"}

        result = await append_activity(lead_id, data)

        assert "id" in result
        assert result["type"] == "note"
        assert result["title"] == "Test note"
        assert result["leadId"] == lead_id
        assert "createdAt" in result
        mock_col.insert_one.assert_called_once()
        mock_col.update_one.assert_called_once()


@pytest.mark.asyncio
async def test_list_activities():
    with patch("app.services.activity_service.db") as mock_db:
        mock_col = MagicMock()
        mock_db.__getitem__ = MagicMock(return_value=mock_col)

        mock_cursor = MagicMock()
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.limit.return_value = mock_cursor
        mock_cursor.to_list = AsyncMock(return_value=[
            {"_id": "act_1", "type": "note", "leadId": "lead_123"},
        ])
        mock_col.find.return_value = mock_cursor

        results = await list_activities("lead_123", limit=10)

        assert len(results) == 1
        assert results[0]["id"] == "act_1"
        assert results[0]["type"] == "note"