"""
Apollo prospect search & enrichment — unit + router tests (mock mode).
"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.deps import require_sales, UserRecord
from app.services import apollo_service

client = TestClient(app)
_SALES = UserRecord(uid="user_sales", role="sales", email="sales@test.com")


@pytest.fixture(autouse=True)
def override_auth():
    app.dependency_overrides[require_sales] = lambda: _SALES
    yield
    app.dependency_overrides.pop(require_sales, None)


# ── mapping ──────────────────────────────────────────────────────────────────

def test_map_person():
    raw = {
        "id": "a1",
        "first_name": "Ada",
        "last_name": "Lovelace",
        "email": "ada@example.com",
        "email_status": "verified",
        "title": "CTO",
        "linkedin_url": "https://linkedin.com/in/ada",
        "phone_numbers": [{"sanitized_number": "+3902111"}],
        "city": "Milano",
        "country": "Italy",
        "seniority": "c_suite",
        "score": 90,
        "organization": {
            "name": "Analytical Engines",
            "primary_domain": "ae.example",
            "industry": "Legal Services",
            "estimated_num_employees": 30,
        },
    }
    p = apollo_service.map_person(raw)
    assert p["firstName"] == "Ada"
    assert p["email"] == "ada@example.com"
    assert p["companyName"] == "Analytical Engines"
    assert p["apolloScore"] == 90
    assert p["phone"] == "+3902111"


# ── search (mock) ────────────────────────────────────────────────────────────

def test_search_mock_returns_people():
    result = client.post(
        "/api/v1/apollo/search",
        json={"filters": {}, "page": 1, "perPage": 10},
    )
    assert result.status_code == 200
    data = result.json()
    assert data["mode"] == "mock"
    assert data["total"] >= 1
    assert len(data["people"]) == data["total"]
    assert all("email" in p for p in data["people"])


def test_search_mock_filters_title():
    result = client.post(
        "/api/v1/apollo/search",
        json={"filters": {"title": "Managing Partner"}, "page": 1, "perPage": 10},
    )
    data = result.json()
    assert data["total"] == 1
    assert data["people"][0]["title"] == "Managing Partner"


def test_search_excludes_invalid_when_mapping_keeps_status():
    result = client.post(
        "/api/v1/apollo/search",
        json={"filters": {"q": "Operations"}, "page": 1, "perPage": 10},
    )
    data = result.json()
    # mock keeps invalid rows with status so UI can grey them out
    assert data["total"] == 1
    assert data["people"][0]["emailStatus"] == "invalid"


# ── match / enrich ───────────────────────────────────────────────────────────

def test_match_mock():
    result = client.post("/api/v1/apollo/match", json={"email": "marco.bianchi@lexfirm.it"})
    assert result.status_code == 200
    assert result.json()["lastName"] == "Bianchi"


def test_match_mock_miss():
    result = client.post("/api/v1/apollo/match", json={"email": "nobody@x.com"})
    assert result.status_code == 200
    assert result.json() == {}


def test_enrich_lead_not_found():
    with patch(
        "app.services.apollo_service.db") as mock_db:
        mock_db.__getitem__ = MagicMock()
        mock_db["leads"].find_one = AsyncMock(return_value=None)
        resp = client.post("/api/v1/apollo/enrich/missing")
    assert resp.status_code == 404


def test_enrich_lead_merges_fields():
    lead = {
        "_id": "lead-1",
        "email": "marco.bianchi@lexfirm.it",
        "firstName": "Marco",
        "phone": None,
        "linkedinUrl": None,
        "deletedAt": None,
    }
    mock_col = MagicMock()
    mock_col.find_one = AsyncMock(side_effect=[lead, {**lead, "linkedinUrl": "https://linkedin.com/in/marcobianchi", "apolloId": "apollo-mock-1"}])
    mock_col.update_one = AsyncMock()

    with patch("app.services.apollo_service.db") as mock_db:
        mock_db.__getitem__ = MagicMock(return_value=mock_col)
        resp = client.post("/api/v1/apollo/enrich/lead-1")

    assert resp.status_code == 200
    assert mock_col.update_one.await_count == 1
    set_payload = mock_col.update_one.await_args.args[1]["$set"]
    assert set_payload["enrichmentSource"] == "apollo"
    assert set_payload["apolloId"] == "apollo-mock-1"
    assert set_payload["linkedinUrl"] == "https://linkedin.com/in/marcobianchi"


# ── import ───────────────────────────────────────────────────────────────────

def test_import_empty_rejected():
    resp = client.post("/api/v1/apollo/import", json={"prospects": []})
    assert resp.status_code == 400


def test_import_dedupes_and_skips_invalid():
    prospects = [
        {
            "firstName": "Nuovo",
            "lastName": "Lead",
            "email": "nuovo@test.com",
            "emailStatus": "verified",
            "title": "CEO",
            "companyName": "Acme",
            "apolloId": "a-9",
            "apolloScore": 70,
        },
        {
            "firstName": "Dup",
            "lastName": "Row",
            "email": "exists@test.com",
            "emailStatus": "verified",
        },
        {
            "firstName": "Bad",
            "lastName": "Mail",
            "email": "bad@test.com",
            "emailStatus": "invalid",
        },
    ]

    async def find_one_side_effect(query, *args, **kwargs):
        email = (query or {}).get("email")
        if email == "exists@test.com":
            return {"_id": "old", "email": email}
        return None

    mock_leads = MagicMock()
    mock_leads.find_one = AsyncMock(side_effect=find_one_side_effect)
    mock_leads.insert_one = AsyncMock()
    mock_gdpr = MagicMock()
    mock_gdpr.insert_one = AsyncMock()

    def get_col(name):
        return {"leads": mock_leads, "gdpr_consents": mock_gdpr}[name]

    with (
        patch("app.services.apollo_service.db") as mock_db,
        patch("app.services.activity_service.append_activity", new_callable=AsyncMock),
    ):
        mock_db.__getitem__ = MagicMock(side_effect=get_col)
        resp = client.post("/api/v1/apollo/import", json={"prospects": prospects})

    assert resp.status_code == 200
    data = resp.json()
    assert data["importedCount"] == 1
    assert data["skippedCount"] == 1
    assert any("non valida" in e.lower() or "invalid" in e.lower() for e in data["errors"])
    assert mock_leads.insert_one.await_count == 1
    assert mock_gdpr.insert_one.await_count == 1


# ── bulk enrich ──────────────────────────────────────────────────────────────

def test_bulk_enrich_requires_ids():
    resp = client.post("/api/v1/apollo/bulk-enrich", json={"leadIds": []})
    assert resp.status_code == 400


def test_bulk_enrich_max_100():
    resp = client.post(
        "/api/v1/apollo/bulk-enrich",
        json={"leadIds": [f"id-{i}" for i in range(101)]},
    )
    assert resp.status_code == 400


def test_bulk_enrich_only_stale_skips_fresh():
    from datetime import datetime, timezone

    fresh = {
        "_id": "fresh-1",
        "email": "fresh@x.com",
        "deletedAt": None,
        "enrichedAt": datetime.now(timezone.utc),
        "enrichmentSource": "apollo",
    }
    stale = {
        "_id": "stale-1",
        "email": "marco.bianchi@lexfirm.it",
        "deletedAt": None,
        "enrichedAt": None,
    }

    async def find_one(query, *args, **kwargs):
        return {"fresh-1": fresh, "stale-1": stale}.get(query.get("_id"))

    mock_col = MagicMock()
    mock_col.find_one = AsyncMock(side_effect=find_one)
    mock_col.update_one = AsyncMock()

    with patch("app.services.apollo_service.db") as mock_db:
        mock_db.__getitem__ = MagicMock(return_value=mock_col)
        resp = client.post(
            "/api/v1/apollo/bulk-enrich",
            json={"leadIds": ["fresh-1", "stale-1"], "onlyStale": True},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["skippedCount"] == 1
    assert data["enrichedCount"] == 1
    statuses = {r["leadId"]: r["status"] for r in data["results"]}
    assert statuses["fresh-1"] == "skipped_fresh"
    assert statuses["stale-1"] == "enriched"


# ── usage ────────────────────────────────────────────────────────────────────

def test_usage_mock_mode():
    resp = client.get("/api/v1/apollo/usage")
    assert resp.status_code == 200
    body = resp.json()
    assert body["provider"] == "apollo"
    assert body["mode"] in ("mock", "live")
