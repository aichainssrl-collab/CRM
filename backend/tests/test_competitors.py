"""
Test Competitor Intelligence — extract/diff unit + router + scan storage.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock

from app.main import app
from app.deps import require_sales, UserRecord

client = TestClient(app)
_SALES_USER = UserRecord(uid="user_sales", role="sales", email="sales@test.com")

_HTML_V1 = """
<html><head><title>Acme AI - Document AI</title>
<meta name="description" content="AI per documenti legali"/>
</head><body>
<h1>Acme AI</h1><h2>Prezzi</h2><p>Piani da 99 EUR al mese</p>
</body></html>
"""

_HTML_V2 = """
<html><head><title>Acme AI - Enterprise Document AI</title>
<meta name="description" content="AI enterprise per documenti"/>
</head><body>
<h1>Acme AI Enterprise</h1><h2>Pricing</h2><p>Da 149 EUR al mese</p>
</body></html>
"""

_COMP = {
    "id": "comp-1",
    "name": "Acme AI",
    "website": "https://acme.example",
    "status": "active",
    "tags": ["legal", "rag"],
}

_SNAP = {
    "id": "snap-1",
    "competitorId": "comp-1",
    "title": "Acme AI - Document AI",
    "bodyHash": "abc",
}


@pytest.fixture(autouse=True)
def override_auth():
    app.dependency_overrides[require_sales] = lambda: _SALES_USER
    yield
    app.dependency_overrides.pop(require_sales, None)


# ── unit: extract_signals / diff_signals ────────────────────────

def test_extract_signals():
    from app.services.competitor_service import extract_signals

    sig = extract_signals(_HTML_V1)
    assert sig["title"] == "Acme AI - Document AI"
    assert "documenti legali" in sig["metaDescription"]
    assert "Acme AI" in sig["headings"]
    assert "Prezzi" in sig["headings"]
    assert any("99" in p for p in sig["pricingMentions"])
    assert "prezzo" in sig["pricingKeywords"] or "pricing" in sig["pricingKeywords"]
    assert len(sig["bodyHash"]) == 64


def test_diff_signals_detects_changes():
    from app.services.competitor_service import extract_signals, diff_signals

    prev = extract_signals(_HTML_V1)
    curr = extract_signals(_HTML_V2)
    changes = diff_signals(prev, curr)
    fields = {c["field"] for c in changes}
    assert "title" in fields
    assert "bodyHash" in fields
    assert "pricingMentions" in fields
    assert diff_signals(None, curr) == []
    assert diff_signals(prev, prev) == []


# ── router ──────────────────────────────────────────────────────

def test_list_competitors():
    with patch(
        "app.routers.competitors.competitor_service.list_competitors",
        new_callable=AsyncMock,
        return_value=[_COMP],
    ):
        resp = client.get("/api/v1/competitors/")
    assert resp.status_code == 200
    assert resp.json()[0]["name"] == "Acme AI"


def test_create_competitor():
    with patch(
        "app.routers.competitors.competitor_service.create_competitor",
        new_callable=AsyncMock,
        return_value=_COMP,
    ):
        resp = client.post(
            "/api/v1/competitors/",
            json={"name": "Acme AI", "website": "https://acme.example", "tags": ["legal"]},
        )
    assert resp.status_code == 200
    assert resp.json()["website"] == "https://acme.example"


def test_get_competitor_not_found():
    with patch(
        "app.routers.competitors.competitor_service.get_competitor",
        new_callable=AsyncMock,
        return_value=None,
    ):
        resp = client.get("/api/v1/competitors/missing")
    assert resp.status_code == 404


def test_update_and_delete():
    with patch(
        "app.routers.competitors.competitor_service.update_competitor",
        new_callable=AsyncMock,
        return_value={**_COMP, "status": "archived"},
    ):
        resp = client.patch("/api/v1/competitors/comp-1", json={"status": "archived"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "archived"

    with patch(
        "app.routers.competitors.competitor_service.delete_competitor",
        new_callable=AsyncMock,
        return_value=True,
    ):
        resp = client.delete("/api/v1/competitors/comp-1")
    assert resp.status_code == 200
    assert resp.json()["ok"] is True


def test_scan_with_injected_html():
    result = {
        "snapshot": {**_SNAP, "title": "Acme AI - Enterprise Document AI"},
        "changes": [{"field": "title", "from": "old", "to": "new"}],
    }
    with patch(
        "app.routers.competitors.competitor_service.scan_competitor",
        new_callable=AsyncMock,
        return_value=result,
    ) as scan:
        resp = client.post(
            "/api/v1/competitors/comp-1/scan",
            json={"html": _HTML_V2},
        )
    assert resp.status_code == 200
    assert resp.json()["changes"][0]["field"] == "title"
    assert scan.call_args.kwargs.get("html") == _HTML_V2 or scan.call_args.args[1] is not None


def test_scan_not_found():
    with patch(
        "app.routers.competitors.competitor_service.scan_competitor",
        new_callable=AsyncMock,
        return_value={},
    ):
        resp = client.post("/api/v1/competitors/missing/scan", json={})
    assert resp.status_code == 404


def test_scan_all():
    with patch(
        "app.routers.competitors.competitor_service.scan_all",
        new_callable=AsyncMock,
        return_value=[{"competitorId": "comp-1", "ok": True, "changes": 1}],
    ):
        resp = client.post("/api/v1/competitors/scan-all")
    assert resp.status_code == 200
    assert resp.json()[0]["ok"] is True


def test_last_monitor_endpoint():
    with patch(
        "app.routers.competitors.competitor_service.last_monitor_run",
        new_callable=AsyncMock,
        return_value={"ranAt": "2026-01-20T10:00:00Z", "changeCount": 2},
    ):
        resp = client.get("/api/v1/competitors/monitor/last")
    assert resp.status_code == 200
    assert resp.json()["changeCount"] == 2


def test_monitor_competitors_handler():
    with patch(
        "app.tasks.handlers.scan_all",
        create=True,
    ):
        pass
    with patch(
        "app.services.competitor_service.scan_all",
        new_callable=AsyncMock,
        return_value=[
            {"competitorId": "c1", "ok": True, "changes": 2},
            {"competitorId": "c2", "ok": True, "changes": 0},
        ],
    ):
        resp = client.post(
            "/tasks/handlers/monitor-competitors",
            json={},
            headers={"Authorization": "Bearer test"},
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["scanned"] == 2
    assert body["changes"] == 2


def test_list_snapshots_and_changes():
    with patch(
        "app.routers.competitors.competitor_service.list_snapshots",
        new_callable=AsyncMock,
        return_value=[_SNAP],
    ):
        resp = client.get("/api/v1/competitors/comp-1/snapshots")
    assert resp.status_code == 200

    with patch(
        "app.routers.competitors.competitor_service.list_changes",
        new_callable=AsyncMock,
        return_value=[{"field": "title"}],
    ):
        resp = client.get("/api/v1/competitors/comp-1/changes")
    assert resp.status_code == 200

    with patch(
        "app.routers.competitors.competitor_service.list_changes",
        new_callable=AsyncMock,
        return_value=[],
    ):
        resp = client.get("/api/v1/competitors/changes")
    assert resp.status_code == 200


def test_stats():
    stats = {"totalCount": 2, "activeCount": 1, "changeCount": 4, "snapshotCount": 6}
    with (
        patch(
            "app.routers.competitors.competitor_service.competitor_stats",
            new_callable=AsyncMock,
            return_value=stats,
        ),
        patch(
            "app.routers.competitors.competitor_service.last_monitor_run",
            new_callable=AsyncMock,
            return_value=None,
        ),
    ):
        resp = client.get("/api/v1/competitors/stats")
    assert resp.status_code == 200
    assert resp.json()["changeCount"] == 4
    assert "lastMonitorRun" in resp.json()


# ── scan_competitor storage integration (mocked db) ─────────────

@pytest.mark.asyncio
async def test_scan_competitor_stores_snapshot_and_changes():
    from app.services import competitor_service

    prev_snap = {
        "_id": "snap-0",
        "id": "snap-0",
        "competitorId": "comp-1",
        **competitor_service.extract_signals(_HTML_V1),
    }

    mock_comp = MagicMock()
    mock_comp.find_one = AsyncMock(return_value={**_COMP, "_id": "comp-1"})
    mock_comp.update_one = AsyncMock()

    mock_snap = MagicMock()
    mock_snap.insert_one = AsyncMock()
    mock_snap.find_one = AsyncMock(return_value=prev_snap)

    mock_chg = MagicMock()
    mock_chg.insert_one = AsyncMock()

    def get_col(name):
        return {
            "competitors": mock_comp,
            "competitor_snapshots": mock_snap,
            "competitor_changes": mock_chg,
        }.get(name, MagicMock())

    mock_db = MagicMock()
    mock_db.__getitem__ = MagicMock(side_effect=get_col)

    with patch("app.services.competitor_service.db", mock_db), patch(
        "app.services.competitor_service.notify_competitor_changes",
        new_callable=AsyncMock,
        return_value=2,
    ) as notify:
        result = await competitor_service.scan_competitor("comp-1", html=_HTML_V2)

    assert result["snapshot"]["bodyHash"]
    assert len(result["changes"]) >= 2
    mock_snap.insert_one.assert_awaited_once()
    assert mock_chg.insert_one.await_count >= 2
    mock_comp.update_one.assert_awaited_once()
    notify.assert_awaited_once()


@pytest.mark.asyncio
async def test_notify_competitor_changes_pricing_is_warning():
    from app.services import competitor_service

    mock_col = MagicMock()
    mock_col.find = MagicMock()
    mock_col.find.return_value.to_list = AsyncMock(
        return_value=[{"_id": "u1", "role": "admin", "isActive": True}]
    )
    mock_col.insert_one = AsyncMock()
    mock_db = MagicMock()
    mock_db.__getitem__ = MagicMock(return_value=mock_col)

    changes = [{"field": "pricingMentions", "from": "99 EUR", "to": "149 EUR"}]
    with patch("app.services.competitor_service.db", mock_db), patch(
        "app.services.notification_service.create_notification",
        new_callable=AsyncMock,
        return_value={},
    ) as notify:
        # re-import path used inside function is local; patch module-level too
        sent = await competitor_service.notify_competitor_changes(
            {"id": "comp-1", "name": "Acme"}, changes
        )

    assert sent == 1
    notify.assert_awaited_once()
    kwargs = notify.call_args.kwargs
    assert kwargs["kind"] == "warning"
    assert "Acme" in kwargs["title"]
    assert kwargs["link"] == "/crm/competitors"
