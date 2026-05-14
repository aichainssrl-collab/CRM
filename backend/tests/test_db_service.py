import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone
from app.services.db_service import (
    create_document,
    update_document,
    get_document,
    soft_delete,
    list_collection,
    append_to_subcollection,
    list_subcollection
)

@pytest.mark.asyncio
async def test_create_document():
    with patch("app.services.db_service.db") as mock_db:
        mock_doc_ref = AsyncMock()
        mock_db.collection.return_value.document.return_value = mock_doc_ref
        
        data = {"name": "Test"}
        result = await create_document("test_col", data)
        
        assert "id" in result
        assert result["name"] == "Test"
        assert "createdAt" in result
        mock_doc_ref.set.assert_called_once()

@pytest.mark.asyncio
async def test_update_document():
    with patch("app.services.db_service.db") as mock_db:
        mock_doc_ref = AsyncMock()
        mock_snap = MagicMock()
        mock_snap.exists = True
        mock_snap.id = "123"
        mock_snap.to_dict.return_value = {"name": "Updated", "updatedAt": datetime.now()}
        mock_doc_ref.get.return_value = mock_snap
        mock_db.collection.return_value.document.return_value = mock_doc_ref
        
        result = await update_document("test_col", "123", {"name": "Updated"})
        
        assert result is not None
        assert result["id"] == "123"
        assert result["name"] == "Updated"
        mock_doc_ref.update.assert_called_once()

@pytest.mark.asyncio
async def test_soft_delete():
    with patch("app.services.db_service.db") as mock_db:
        mock_doc_ref = AsyncMock()
        mock_db.collection.return_value.document.return_value = mock_doc_ref
        
        await soft_delete("test_col", "123")
        
        mock_doc_ref.update.assert_called_once()
        call_args = mock_doc_ref.update.call_args[0][0]
        assert "deletedAt" in call_args

@pytest.mark.asyncio
async def test_get_document_exists():
    with patch("app.services.db_service.db") as mock_db:
        mock_doc_ref = AsyncMock()
        mock_snap = MagicMock()
        mock_snap.exists = True
        mock_snap.id = "123"
        mock_snap.to_dict.return_value = {"name": "Test", "deletedAt": None}
        mock_doc_ref.get.return_value = mock_snap
        mock_db.collection.return_value.document.return_value = mock_doc_ref
        
        result = await get_document("test_col", "123")
        
        assert result is not None
        assert result["id"] == "123"

@pytest.mark.asyncio
async def test_get_document_deleted():
    with patch("app.services.db_service.db") as mock_db:
        mock_doc_ref = AsyncMock()
        mock_snap = MagicMock()
        mock_snap.exists = True
        mock_snap.id = "123"
        mock_snap.to_dict.return_value = {"name": "Test", "deletedAt": datetime.now()}
        mock_doc_ref.get.return_value = mock_snap
        mock_db.collection.return_value.document.return_value = mock_doc_ref
        
        result = await get_document("test_col", "123")
        
        assert result is None
