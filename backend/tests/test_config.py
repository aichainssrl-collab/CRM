import pytest
from app.config import settings

def test_settings_loaded():
    assert settings.FIREBASE_PROJECT_ID is not None
    assert settings.GCP_LOCATION == "europe-west1"
    assert len(settings.ALLOWED_ORIGINS) > 0
