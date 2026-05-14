import pytest
import firebase_admin
from app.firebase_admin import db, bucket

@pytest.mark.asyncio
async def test_firebase_admin_initialized():
    assert len(firebase_admin._apps) > 0
    assert db is not None
    assert bucket is not None
