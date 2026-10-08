import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone
from app.services.db_service import (
    create_document,
    update_document,
    get_document,
    soft_delete,
    list_collection,
)


@pytest.mark.asyncio
async def test_create_document():
    with patch("app.services.db_service.db") as mock_db:
        mock_col = AsyncMock()
        mock_db.__getitem__ = MagicMock(return_value=mock_col)
        mock_col.insert_one = AsyncMock()

        data = {"name": "Test"}
        result = await create_document("test_col", data)

        assert "id" in result
        assert result["name"] == "Test"
        assert "createdAt" in result
        assert "updatedAt" in result
        assert result["deletedAt"] is None
        mock_col.insert_one.assert_called_once()


@pytest.mark.asyncio
async def test_update_document():
    with patch("app.services.db_service.db") as mock_db:
        mock_col = AsyncMock()
        mock_db.__getitem__ = MagicMock(return_value=mock_col)
        mock_col.find_one_and_update = AsyncMock(return_value={
            "_id": "123", "name": "Updated", "deletedAt": None,
        })

        result = await update_document("test_col", "123", {"name": "Updated"})

        assert result is not None
        assert result["id"] == "123"
        assert result["name"] == "Updated"
        mock_col.find_one_and_update.assert_called_once()


@pytest.mark.asyncio
async def test_soft_delete():
    with patch("app.services.db_service.db") as mock_db:
        mock_col = AsyncMock()
        mock_db.__getitem__ = MagicMock(return_value=mock_col)
        mock_col.update_one = AsyncMock()

        await soft_delete("test_col", "123")

        mock_col.update_one.assert_called_once()
        call_args = mock_col.update_one.call_args[0]
        assert call_args[0] == {"_id": "123"}
        assert "deletedAt" in call_args[1]["$set"]


@pytest.mark.asyncio
async def test_get_document_exists():
    with patch("app.services.db_service.db") as mock_db:
        mock_col = AsyncMock()
        mock_db.__getitem__ = MagicMock(return_value=mock_col)
        mock_col.find_one = AsyncMock(return_value={
            "_id": "123", "name": "Test", "deletedAt": None,
        })

        result = await get_document("test_col", "123")

        assert result is not None
        assert result["id"] == "123"
        assert result["name"] == "Test"


@pytest.mark.asyncio
async def test_get_document_deleted():
    with patch("app.services.db_service.db") as mock_db:
        mock_col = AsyncMock()
        mock_db.__getitem__ = MagicMock(return_value=mock_col)
        mock_col.find_one = AsyncMock(return_value=None)

        result = await get_document("test_col", "123")

        assert result is None