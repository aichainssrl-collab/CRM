"""
Test CORS headers su tutti gli endpoint principali.

Usa FastAPI TestClient (in-process): non richiede uvicorn in esecuzione.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app

ALLOWED_ORIGIN = "http://localhost:3000"
BAD_ORIGIN = "http://evil.example.com"


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


# ---------------------------------------------------------------------------
# Preflight (OPTIONS)
# ---------------------------------------------------------------------------

class TestPreflight:
    @pytest.mark.parametrize("method,path", [
        ("GET",  "/api/v1/users/me"),
        ("GET",  "/api/v1/users/me/avatar"),
        ("GET",  "/api/v1/leads"),
        ("POST", "/api/v1/users/me/avatar"),
        ("PATCH","/api/v1/leads"),
    ])
    def test_preflight_returns_200(self, client, method, path):
        """Il preflight OPTIONS deve rispondere 200 con CORS headers."""
        r = client.options(
            path,
            headers={
                "Origin": ALLOWED_ORIGIN,
                "Access-Control-Request-Method": method,
                "Access-Control-Request-Headers": "Authorization,Content-Type",
            },
        )
        assert r.status_code == 200, f"OPTIONS {path} → {r.status_code}"

    @pytest.mark.parametrize("method,path", [
        ("GET",  "/api/v1/users/me"),
        ("POST", "/api/v1/users/me/avatar"),
        ("GET",  "/api/v1/leads"),
    ])
    def test_preflight_has_allow_origin(self, client, method, path):
        r = client.options(
            path,
            headers={
                "Origin": ALLOWED_ORIGIN,
                "Access-Control-Request-Method": method,
                "Access-Control-Request-Headers": "Authorization",
            },
        )
        assert "access-control-allow-origin" in r.headers, (
            f"Manca Access-Control-Allow-Origin nel preflight di {path}"
        )
        assert r.headers["access-control-allow-origin"] == ALLOWED_ORIGIN

    def test_preflight_allows_authorization_header(self, client):
        r = client.options(
            "/api/v1/users/me",
            headers={
                "Origin": ALLOWED_ORIGIN,
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Authorization",
            },
        )
        allow_headers = r.headers.get("access-control-allow-headers", "").lower()
        assert "authorization" in allow_headers, (
            f"Authorization non è in Access-Control-Allow-Headers: {allow_headers}"
        )

    def test_preflight_allows_credentials(self, client):
        r = client.options(
            "/api/v1/users/me",
            headers={
                "Origin": ALLOWED_ORIGIN,
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Authorization",
            },
        )
        assert r.headers.get("access-control-allow-credentials") == "true"

    def test_preflight_blocked_for_unknown_origin(self, client):
        """Origini non in allowlist non devono ricevere CORS headers."""
        r = client.options(
            "/api/v1/users/me",
            headers={
                "Origin": BAD_ORIGIN,
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Authorization",
            },
        )
        # La risposta non deve contenere access-control-allow-origin per BAD_ORIGIN
        acao = r.headers.get("access-control-allow-origin", "")
        assert acao != BAD_ORIGIN, (
            f"Il server ha permesso l'origine malevola {BAD_ORIGIN}!"
        )


# ---------------------------------------------------------------------------
# Risposte reali (auth fallisce → 401/403, ma CORS headers devono esserci)
# ---------------------------------------------------------------------------

class TestActualResponseCors:
    @pytest.mark.parametrize("path", [
        "/api/v1/users/me",
        "/api/v1/users/me/avatar",
        "/api/v1/leads",
        "/api/v1/deals",
        "/api/v1/tasks",
        "/api/v1/dashboard/metrics",
    ])
    def test_cors_header_present_on_auth_error(self, client, path):
        """
        Anche se il token è invalido (401), il server deve includere
        Access-Control-Allow-Origin. Senza di esso il browser blocca la
        risposta e l'app non può leggere il codice di errore.
        """
        r = client.get(
            path,
            headers={
                "Origin": ALLOWED_ORIGIN,
                "Authorization": "Bearer invalid_token_for_cors_test",
            },
        )
        assert "access-control-allow-origin" in r.headers, (
            f"Manca Access-Control-Allow-Origin su GET {path} (status={r.status_code})"
        )
        assert r.headers["access-control-allow-origin"] == ALLOWED_ORIGIN
        # Deve essere 401 (token invalido), non 0 o connessione rifiutata
        assert r.status_code in (401, 403), (
            f"Atteso 401/403, ricevuto {r.status_code} per {path}"
        )

    def test_health_no_auth_required(self, client):
        """Health endpoint deve rispondere 200 senza token."""
        from unittest.mock import AsyncMock, patch

        with patch("app.main.mongo_db.command", new_callable=AsyncMock, return_value={"ok": 1}):
            r = client.get(
                "/api/health",
                headers={"Origin": ALLOWED_ORIGIN},
            )
        assert r.status_code == 200
        assert r.json()["status"] == "ok"
        assert r.json()["checks"]["api"] == "ok"

    def test_health_has_cors_header(self, client):
        r = client.get(
            "/api/health",
            headers={"Origin": ALLOWED_ORIGIN},
        )
        assert "access-control-allow-origin" in r.headers


# ---------------------------------------------------------------------------
# Verifica che l'endpoint GET /me/avatar esiste (non 405)
# ---------------------------------------------------------------------------

class TestAvatarEndpoint:
    def test_get_avatar_not_405(self, client):
        """GET /me/avatar deve esistere (non Method Not Allowed)."""
        r = client.get(
            "/api/v1/users/me/avatar",
            headers={
                "Origin": ALLOWED_ORIGIN,
                "Authorization": "Bearer invalid",
            },
        )
        assert r.status_code != 405, (
            "GET /api/v1/users/me/avatar restituisce 405 — l'endpoint non esiste!"
        )

    def test_get_avatar_cors_on_auth_error(self, client):
        r = client.get(
            "/api/v1/users/me/avatar",
            headers={
                "Origin": ALLOWED_ORIGIN,
                "Authorization": "Bearer invalid",
            },
        )
        assert "access-control-allow-origin" in r.headers
        assert r.status_code in (401, 403)
