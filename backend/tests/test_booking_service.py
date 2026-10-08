import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.booking_service import create_booking, get_booking, cancel_booking, list_available_slots
from app.schemas.booking import BookingCreate


@pytest.mark.asyncio
async def test_list_available_slots():
    with patch("app.services.booking_service.db") as mock_db:
        mock_col = MagicMock()
        mock_db.__getitem__ = MagicMock(return_value=mock_col)

        mock_cursor = MagicMock()
        mock_cursor.sort.return_value = mock_cursor

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

        mock_cursor.__aiter__ = MagicMock(return_value=AsyncDocIterator([
            {"_id": "slot_1", "startTime": "2024-01-01T10:00:00Z", "isAvailable": True},
        ]))
        mock_col.find.return_value = mock_cursor

        results = await list_available_slots()

        assert len(results) == 1
        assert results[0]["id"] == "slot_1"


@pytest.mark.asyncio
async def test_create_booking():
    with patch("app.services.booking_service.db") as mock_db:
        mock_col = AsyncMock()
        mock_db.__getitem__ = MagicMock(return_value=mock_col)
        mock_col.find_one = AsyncMock(return_value={
            "_id": "slot_1", "isAvailable": True, "startTime": "2024-01-01T10:00:00Z",
        })
        mock_col.insert_one = AsyncMock()
        mock_col.update_one = AsyncMock()

        data = BookingCreate(
            slotId="slot_1",
            firstName="Test",
            lastName="User",
            email="test@test.com",
            companyName="Test Inc",
            consent_given=True,
            consent_text="Yes",
        )

        result = await create_booking(data, "lead_1")
        assert "id" in result
        assert result["status"] == "confirmed"


@pytest.mark.asyncio
async def test_cancel_booking():
    with (
        patch("app.services.booking_service.get_document", new_callable=AsyncMock) as mock_get,
        patch("app.services.booking_service.db") as mock_db,
    ):
        mock_get.side_effect = [
            {"id": "book_1", "slotId": "slot_1"},  # first call in cancel_booking
            {"id": "book_1", "status": "cancelled"},  # second call at end
        ]

        mock_col = AsyncMock()
        mock_db.__getitem__ = MagicMock(return_value=mock_col)
        mock_col.update_one = AsyncMock()

        result = await cancel_booking("book_1")

        assert result is not None
        # update_one called twice: once for booking, once for slot
        assert mock_col.update_one.call_count == 2