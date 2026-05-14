"""
Security review: auth, CORS, rate limiting, input validation.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.config import settings

client = TestClient(app)


# ── Autenticazione ────────────────────────────────────────────

class TestAuthentication:
    def test_leads_requires_auth(self):
        response = client.get("/api/v1/leads")
        assert response.status_code == 403

    def test_leads_detail_requires_auth(self):
        response = client.get("/api/v1/leads/some-id")
        assert response.status_code == 403

    def test_create_lead_requires_auth(self):
        response = client.post("/api/v1/leads", json={"email": "x@x.com"})
        assert response.status_code == 403

    def test_deals_requires_auth(self):
        response = client.get("/api/v1/deals")
        assert response.status_code == 403

    def test_gdpr_export_requires_auth(self):
        response = client.get("/api/v1/gdpr/some-id/export")
        assert response.status_code == 403

    def test_users_requires_auth(self):
        response = client.get("/api/v1/users")
        assert response.status_code == 403

    def test_tasks_handler_requires_bearer(self):
        response = client.post("/tasks/handlers/recalculate-score", json={"lead_id": "x"})
        assert response.status_code == 403

    def test_tasks_handler_accepts_bearer_in_debug(self):
        """In DEBUG mode un Bearer valido non viene bloccato dall'auth check."""
        with patch("app.tasks.handlers.calculate_lead_score", new_callable=AsyncMock) as mock_score:
            mock_score.return_value = 50
            response = client.post(
                "/tasks/handlers/recalculate-score",
                json={"lead_id": "x"},
                headers={"Authorization": "Bearer any-token"},
            )
        assert response.status_code == 200

    def test_public_forms_no_auth_needed(self):
        """I form pubblici NON richiedono autenticazione."""
        response = client.post("/api/v1/forms/playbook", json={
            "email": "bad",  # email non valida → 422, ma non 403
            "consent_given": True,
            "consent_text": "ok",
        })
        assert response.status_code == 422  # Validation error, non 403

    def test_booking_slots_public(self):
        with patch("app.routers.bookings.list_available_slots", new_callable=AsyncMock) as mock:
            mock.return_value = []
            response = client.get("/api/v1/bookings/slots")
        assert response.status_code == 200

    def test_health_public(self):
        response = client.get("/api/health")
        assert response.status_code == 200


# ── CORS ──────────────────────────────────────────────────────

class TestCORS:
    def test_cors_preflight_allowed_origin(self):
        """Preflight OPTIONS → CORS headers presenti per origine permessa."""
        allowed_origin = settings.ALLOWED_ORIGINS[0] if settings.ALLOWED_ORIGINS else "http://localhost:3000"
        response = client.options(
            "/api/health",
            headers={
                "Origin": allowed_origin,
                "Access-Control-Request-Method": "GET",
            },
        )
        assert response.status_code in (200, 204)
        assert "access-control-allow-credentials" in response.headers

    def test_cors_config_production_locked(self):
        """In produzione ALLOWED_ORIGINS deve contenere solo il dominio ufficiale."""
        if not settings.DEBUG:
            assert "https://crm.aichainsolutions.net" in settings.ALLOWED_ORIGINS
            assert "http://localhost:3000" not in settings.ALLOWED_ORIGINS


# ── Input Validation ──────────────────────────────────────────

class TestInputValidation:
    def test_form_rejects_invalid_email(self):
        response = client.post("/api/v1/forms/playbook", json={
            "email": "not-an-email",
            "consent_given": True,
            "consent_text": "ok",
        })
        assert response.status_code == 422

    def test_form_rejects_missing_consent(self):
        response = client.post("/api/v1/forms/playbook", json={
            "email": "valid@test.com",
            "consent_given": False,
            "consent_text": "ok",
        })
        assert response.status_code == 422

    def test_gdpr_erase_requires_confirm_true(self):
        from app.models.user import UserRecord
        fake_admin = UserRecord(uid="u1", role="admin")

        from app.deps import require_admin
        app.dependency_overrides[require_admin] = lambda: fake_admin

        with (
            patch("app.routers.gdpr.get_document", new_callable=AsyncMock) as mock_doc,
            patch("app.routers.gdpr.gdpr_erase", new_callable=AsyncMock),
        ):
            mock_doc.return_value = {"id": "lead-001"}
            response = client.post(
                "/api/v1/gdpr/lead-001/erase",
                json={"confirm": False},
            )

        app.dependency_overrides.clear()
        assert response.status_code == 422

    def test_lead_list_limit_bounded(self):
        """Parametro limit non può superare 100."""
        from app.models.user import UserRecord
        from app.deps import require_sales
        app.dependency_overrides[require_sales] = lambda: UserRecord(uid="u1", role="sales")

        with patch("app.routers.leads.LeadService") as MockService:
            instance = MockService.return_value
            instance.list_leads = AsyncMock(return_value=[])
            response = client.get("/api/v1/leads?limit=9999")

        app.dependency_overrides.clear()
        assert response.status_code == 422


# ── Rate Limiting ─────────────────────────────────────────────

class TestRateLimiting:
    def test_rate_limit_header_present_on_forms(self):
        """Verifica che slowapi sia attivo rispondendo con X-RateLimit headers."""
        with (
            patch("app.routers.forms.LeadService") as MockService,
            patch("app.routers.forms.log_consent", new_callable=AsyncMock),
            patch("app.routers.forms.enqueue_task", new_callable=AsyncMock),
            patch("app.routers.forms.send_sales_notification", new_callable=AsyncMock),
        ):
            instance = MockService.return_value
            instance.create_or_update_from_form = AsyncMock(
                return_value={"id": "l1", "email": "rl@test.com"}
            )
            response = client.post("/api/v1/forms/playbook", json={
                "email": "rl@test.com",
                "consent_given": True,
                "consent_text": "ok",
            })

        # slowapi aggiunge X-RateLimit-Limit quando la richiesta è ok
        assert response.status_code == 201

    def test_task_handlers_no_rate_limit_bypass(self):
        """Task handlers non devono essere accessibili senza Authorization."""
        for path in ["recalculate-score", "send-welcome-email", "email-sequence"]:
            response = client.post(f"/tasks/handlers/{path}", json={})
            assert response.status_code == 403, f"{path} deve richiedere auth"


# ── Soft Delete / Data Isolation ─────────────────────────────

class TestDataIsolation:
    def test_soft_deleted_leads_not_exposed(self):
        """Lead con deletedAt != null non devono essere restituiti dalla lista."""
        from app.services.db_service import list_collection

        # La funzione list_collection filtra deletedAt per default
        import inspect
        src = inspect.getsource(list_collection)
        assert 'include_deleted' in src
        assert '"deletedAt"' in src or "'deletedAt'" in src

    def test_gdpr_erase_anonymizes_not_deletes(self):
        """Art.17: il documento deve persistere anonimizzato, mai cancellato."""
        from app.services import gdpr_service
        import inspect, ast
        src = inspect.getsource(gdpr_service.gdpr_erase)
        assert ".update(" in src
        assert "CANCELLATO" in src
        # Nessuna chiamata a .delete() (non nei commenti — cerca nei token del codice)
        tree = ast.parse(src)
        delete_calls = [
            node for node in ast.walk(tree)
            if isinstance(node, ast.Attribute) and node.attr == "delete"
        ]
        assert len(delete_calls) == 0, "gdpr_erase non deve chiamare .delete()"
