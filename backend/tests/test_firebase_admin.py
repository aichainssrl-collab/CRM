import pytest
import firebase_admin


def test_firebase_admin_initialized():
    """Firebase Admin SDK inizializzato (solo auth JWT)."""
    assert len(firebase_admin._apps) > 0


def test_firebase_auth_available():
    """Modulo auth accessibile per verifica token."""
    from firebase_admin import auth
    assert hasattr(auth, "verify_id_token")