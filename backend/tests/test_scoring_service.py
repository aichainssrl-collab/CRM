import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.scoring_service import calculate_lead_score


@pytest.mark.asyncio
async def test_calculate_lead_score():
    with patch("app.services.scoring_service.db") as mock_db:
        mock_col = MagicMock()
        mock_db.__getitem__ = MagicMock(return_value=mock_col)

        mock_col.find_one = AsyncMock(return_value={
            "_id": "lead_123",
            "roleSeniority": "manager",
            "budgetRange": "10k-50k",
            "timeline": "1_month",
        })
        mock_col.update_one = AsyncMock()

        # activities cursor — motor cursor chains .sort().limit() then async iteration
        mock_cursor = MagicMock()
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.limit.return_value = mock_cursor

        class AsyncDocIterator:
            def __init__(self, docs):
                self._docs = iter(docs)
            def __aiter__(self):
                return self
            async def __anext__(self):
                try:
                    return next(self._docs)
                except StopIteration:
                    raise StopAsyncIteration

        mock_cursor.__aiter__ = MagicMock(return_value=AsyncDocIterator([]))
        mock_col.find.return_value = mock_cursor

        score = await calculate_lead_score("lead_123")

        assert score > 0
        mock_col.update_one.assert_called_once()