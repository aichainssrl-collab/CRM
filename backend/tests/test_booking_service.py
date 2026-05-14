import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.booking_service import create_booking, get_booking, cancel_booking, list_available_slots, get_slot
from app.schemas.booking import BookingCreate
import datetime

@pytest.mark.asyncio
async def test_list_available_slots():
    with patch("app.services.booking_service.db") as mock_db:
        mock_snap = MagicMock()
        mock_snap.id = "slot_1"
        mock_snap.to_dict.return_value = {"startTime": "2024-01-01T10:00:00Z", "isAvailable": True}
        
        async def mock_async_gen():
            yield mock_snap
            
        mock_db.collection.return_value.where.return_value.order_by.return_value.stream = mock_async_gen
        
        results = await list_available_slots()
        
        assert len(results) == 1
        assert results[0]["id"] == "slot_1"

@pytest.mark.asyncio
async def test_create_booking():
    # Since create_booking uses a transaction, we mock the db.transaction decorator and behavior
    with patch("app.services.booking_service.db") as mock_db:
        # mock decorator
        def mock_transaction(func):
            async def wrapper(*args, **kwargs):
                mock_tx = AsyncMock()
                mock_snap = MagicMock()
                mock_snap.exists = True
                mock_snap.to_dict.return_value = {"isAvailable": True}
                mock_tx.get.return_value = mock_snap
                return await func(mock_tx, *args, **kwargs)
            return wrapper
            
        mock_db.transaction = mock_transaction
        
        data = BookingCreate(
            slotId="slot_1", 
            firstName="Test", 
            lastName="User", 
            email="test@test.com", 
            companyName="Test Inc",
            consent_given=True,
            consent_text="Yes"
        )
        
        result = await create_booking(data, "lead_1")
        assert "id" in result
        assert result["status"] == "confirmed"

@pytest.mark.asyncio
async def test_cancel_booking():
    with patch("app.services.booking_service.get_document", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = {"id": "book_1", "slotId": "slot_1"}
        
        with patch("app.services.booking_service.db") as mock_db:
            mock_doc_ref = AsyncMock()
            mock_db.collection.return_value.document.return_value = mock_doc_ref
            
            result = await cancel_booking("book_1")
            
            assert result is not None
            # Update should have been called twice (once for booking, once for slot)
            assert mock_doc_ref.update.call_count == 2
