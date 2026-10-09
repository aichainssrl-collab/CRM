"""
Test analytics & reports routers.
Mocks Firebase Auth and MongoDB.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
from app.main import app
from app.deps import require_sales, require_admin, UserRecord

client = TestClient(app)

_SALES_USER = UserRecord(uid="user_sales", role="sales", email="sales@test.com")
_ADMIN_USER = UserRecord(uid="user_admin", role="admin", email="admin@test.com")


@pytest.fixture(autouse=True)
def override_auth():
    """Bypassa Firebase Auth per tutti i test di questo modulo."""
    app.dependency_overrides[require_sales] = lambda: _SALES_USER
    app.dependency_overrides[require_admin] = lambda: _ADMIN_USER
    yield
    app.dependency_overrides.pop(require_sales, None)
    app.dependency_overrides.pop(require_admin, None)


# ══════════════════════════════════════════════════════════════
# ANALYTICS ENDPOINTS
# ══════════════════════════════════════════════════════════════

def test_funnel_endpoint():
    """GET /api/v1/analytics/funnel returns funnel data."""
    mock_funnel = [
        {"stage": "new", "count": 100},
        {"stage": "contacted", "count": 50},
        {"stage": "qualified", "count": 20},
    ]
    with patch("app.routers.analytics.analytics_service.get_conversion_funnel", new_callable=AsyncMock, return_value=mock_funnel):
        resp = client.get("/api/v1/analytics/funnel?time_range=30d")

    assert resp.status_code == 200
    body = resp.json()
    assert len(body["funnel"]) == 3
    assert body["funnel"][0]["stage"] == "new"
    assert body["timeRange"] == "30d"


def test_velocity_endpoint():
    """GET /api/v1/analytics/velocity returns velocity data."""
    mock_velocity = [
        {"stage": "proposal", "avgDays": 12.5, "count": 8},
        {"stage": "negotiation", "avgDays": 20.3, "count": 5},
    ]
    with patch("app.routers.analytics.analytics_service.get_pipeline_velocity", new_callable=AsyncMock, return_value=mock_velocity):
        resp = client.get("/api/v1/analytics/velocity")

    assert resp.status_code == 200
    assert len(resp.json()["velocity"]) == 2


def test_performance_endpoint():
    """GET /api/v1/analytics/performance returns per-user data."""
    mock_perf = [
        {"userId": "u1", "userName": "Mario", "leads": 20, "dealsWon": 5, "revenue": 25000, "winRate": 50.0},
    ]
    with patch("app.routers.analytics.analytics_service.get_sales_performance", new_callable=AsyncMock, return_value=mock_perf):
        resp = client.get("/api/v1/analytics/performance")

    assert resp.status_code == 200
    perf = resp.json()["performance"]
    assert len(perf) == 1
    assert perf[0]["userName"] == "Mario"


def test_trends_endpoint():
    """GET /api/v1/analytics/trends returns time series."""
    mock_trends = {"period": "week", "series": [
        {"period": "2026-W03", "leads": 10, "dealsWon": 2, "dealsWonValue": 10000, "dealsLost": 1, "newDeals": 3},
    ]}
    with patch("app.routers.analytics.analytics_service.get_trends", new_callable=AsyncMock, return_value=mock_trends):
        resp = client.get("/api/v1/analytics/trends?period=week")

    assert resp.status_code == 200
    assert resp.json()["period"] == "week"
    assert len(resp.json()["series"]) == 1


def test_forecast_endpoint():
    """GET /api/v1/analytics/forecast returns forecast data."""
    mock_forecast = [
        {"stage": "proposal", "count": 5, "totalValue": 50000, "weightedValue": 30000, "avgProbability": 60},
    ]
    with patch("app.routers.analytics.analytics_service.get_forecast", new_callable=AsyncMock, return_value=mock_forecast):
        resp = client.get("/api/v1/analytics/forecast")

    assert resp.status_code == 200
    body = resp.json()
    assert body["totalWeighted"] == 30000
    assert body["totalPipeline"] == 50000


def test_cohorts_endpoint():
    """GET /api/v1/analytics/cohorts returns cohort data."""
    mock_cohorts = [
        {"month": "2026-01", "total": 50, "contacted": 30, "qualified": 10, "converted": 3,
         "contactRate": 60.0, "qualifyRate": 20.0, "convertRate": 6.0},
    ]
    with patch("app.routers.analytics.analytics_service.get_cohorts", new_callable=AsyncMock, return_value=mock_cohorts):
        resp = client.get("/api/v1/analytics/cohorts?months=6")

    assert resp.status_code == 200
    assert len(resp.json()["cohorts"]) == 1
    assert resp.json()["cohorts"][0]["convertRate"] == 6.0


# ══════════════════════════════════════════════════════════════
# REPORTS ENDPOINTS
# ══════════════════════════════════════════════════════════════

_REPORT_DOC = {
    "_id": "report-uuid-123",
    "title": "Report Gennaio",
    "timeRange": "30d",
    "generatedBy": "user_sales",
    "generatedByName": "sales@test.com",
    "data": {"kpis": {"totalLeads": 100, "newLeads": 20}},
    "createdAt": "2026-01-15T10:00:00Z",
    "updatedAt": "2026-01-15T10:00:00Z",
    "deletedAt": None,
}


def test_generate_report():
    """POST /api/v1/reports/generate creates a report."""
    with patch("app.routers.reports.analytics_service.get_kpi_summary", new_callable=AsyncMock, return_value={"totalLeads": 100}), \
         patch("app.routers.reports.analytics_service.get_conversion_funnel", new_callable=AsyncMock, return_value=[]), \
         patch("app.routers.reports.analytics_service.get_pipeline_velocity", new_callable=AsyncMock, return_value=[]), \
         patch("app.routers.reports.analytics_service.get_sales_performance", new_callable=AsyncMock, return_value=[]), \
         patch("app.routers.reports.analytics_service.get_forecast", new_callable=AsyncMock, return_value=[]), \
         patch("app.routers.reports.db") as mock_db:
        mock_col = AsyncMock()
        mock_db.__getitem__ = MagicMock(return_value=mock_col)
        mock_col.insert_one = AsyncMock()
        resp = client.post("/api/v1/reports/generate", json={"title": "Test Report", "timeRange": "30d"})

    assert resp.status_code == 200
    body = resp.json()
    assert body["title"] == "Test Report"
    assert "data" in body


def test_list_reports():
    """GET /api/v1/reports/ returns list of reports."""
    mock_cursor = AsyncMock()
    mock_cursor.to_list = AsyncMock(return_value=[_REPORT_DOC])

    with patch("app.routers.reports.db") as mock_db:
        mock_col = MagicMock()
        mock_db.__getitem__ = MagicMock(return_value=mock_col)
        mock_col.find.return_value.sort.return_value.limit.return_value = mock_cursor
        resp = client.get("/api/v1/reports/")

    assert resp.status_code == 200
    reports = resp.json()
    assert len(reports) >= 1
    assert reports[0]["title"] == "Report Gennaio"


def test_get_single_report():
    """GET /api/v1/reports/{id} returns full report."""
    with patch("app.routers.reports.db") as mock_db:
        mock_col = AsyncMock()
        mock_db.__getitem__ = MagicMock(return_value=mock_col)
        mock_col.find_one = AsyncMock(return_value=_REPORT_DOC)
        resp = client.get("/api/v1/reports/report-uuid-123")

    assert resp.status_code == 200
    assert resp.json()["title"] == "Report Gennaio"


def test_get_report_not_found():
    """GET /api/v1/reports/{id} returns 404 when not found."""
    with patch("app.routers.reports.db") as mock_db:
        mock_col = AsyncMock()
        mock_db.__getitem__ = MagicMock(return_value=mock_col)
        mock_col.find_one = AsyncMock(return_value=None)
        resp = client.get("/api/v1/reports/nonexistent")

    assert resp.status_code == 404


def test_delete_report_admin():
    """DELETE /api/v1/reports/{id} requires admin."""
    with patch("app.routers.reports.db") as mock_db:
        mock_col = AsyncMock()
        mock_db.__getitem__ = MagicMock(return_value=mock_col)
        mock_result = MagicMock()
        mock_result.modified_count = 1
        mock_col.update_one = AsyncMock(return_value=mock_result)
        resp = client.delete("/api/v1/reports/report-uuid-123")

    assert resp.status_code == 200
    assert resp.json()["ok"] is True


def test_send_report_email():
    """POST /api/v1/reports/{id}/send sends email."""
    with patch("app.routers.reports.db") as mock_db, \
         patch("app.routers.reports.send_email", new_callable=AsyncMock, return_value="email-id-123") as mock_send:
        mock_col = AsyncMock()
        mock_db.__getitem__ = MagicMock(return_value=mock_col)
        mock_col.find_one = AsyncMock(return_value=_REPORT_DOC)
        resp = client.post(
            "/api/v1/reports/report-uuid-123/send",
            json={"to": "dest@test.com", "message": "Ecco il report"},
        )

    assert resp.status_code == 200
    assert resp.json()["ok"] is True
    mock_send.assert_called_once()
    call_kwargs = mock_send.call_args
    assert call_kwargs.kwargs["to"] == "dest@test.com" or call_kwargs[1]["to"] == "dest@test.com"