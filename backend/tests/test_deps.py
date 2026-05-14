import pytest
from fastapi import HTTPException
from unittest.mock import patch, MagicMock
from app.deps import require_admin, require_sales
from app.models.user import UserRecord

@pytest.mark.asyncio
async def test_require_admin_success():
    user = UserRecord(uid="123", email="admin@test.com", role="admin")
    result = await require_admin(user)
    assert result.uid == "123"

@pytest.mark.asyncio
async def test_require_admin_fail():
    user = UserRecord(uid="123", email="sales@test.com", role="sales")
    with pytest.raises(HTTPException) as exc:
        await require_admin(user)
    assert exc.value.status_code == 403

@pytest.mark.asyncio
async def test_require_sales_success():
    user = UserRecord(uid="123", email="sales@test.com", role="sales")
    result = await require_sales(user)
    assert result.uid == "123"
    
    user_admin = UserRecord(uid="123", email="admin@test.com", role="admin")
    result_admin = await require_sales(user_admin)
    assert result_admin.uid == "123"

@pytest.mark.asyncio
async def test_require_sales_fail():
    user = UserRecord(uid="123", email="readonly@test.com", role="readonly")
    with pytest.raises(HTTPException) as exc:
        await require_sales(user)
    assert exc.value.status_code == 403
