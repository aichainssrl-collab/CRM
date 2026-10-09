"""
Test products & segments router.
Mocks Firebase Auth and MongoDB.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from app.main import app
from app.deps import require_sales, UserRecord

client = TestClient(app)

_SALES_USER = UserRecord(uid="user_sales", role="sales", email="sales@test.com")

_PRODUCT = {
    "id": "prod-1",
    "name": "ZenTratto",
    "description": "RAG documentale",
    "sku": "ZT-001",
    "category": "software",
    "price": 15000,
    "currency": "EUR",
    "billingModel": "yearly",
    "isActive": True,
}

_SEGMENT = {
    "id": "seg-1",
    "name": "Legal Premium",
    "description": "Lead legali con score alto",
    "rules": {"industry": "Legal", "minScore": 70},
    "matchCount": 25,
}


@pytest.fixture(autouse=True)
def override_auth():
    app.dependency_overrides[require_sales] = lambda: _SALES_USER
    yield
    app.dependency_overrides.pop(require_sales, None)


# ── Products ──────────────────────────────────────────────────
def test_list_products():
    with patch("app.routers.products.product_service.list_products", new_callable=AsyncMock, return_value=[_PRODUCT]):
        resp = client.get("/api/v1/products/")
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["name"] == "ZenTratto"


def test_create_product():
    with patch("app.routers.products.product_service.create_product", new_callable=AsyncMock, return_value=_PRODUCT):
        resp = client.post("/api/v1/products/", json={"name": "ZenTratto", "price": 15000, "category": "software"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "ZenTratto"


def test_delete_product():
    with patch("app.routers.products.product_service.delete_product", new_callable=AsyncMock, return_value=True):
        resp = client.delete("/api/v1/products/prod-1")
    assert resp.status_code == 200
    assert resp.json()["ok"] is True


# ── Segments ──────────────────────────────────────────────────
def test_list_segments():
    with patch("app.routers.products.segmentation_service.list_segments", new_callable=AsyncMock, return_value=[_SEGMENT]):
        resp = client.get("/api/v1/segments/")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_create_segment():
    with patch("app.routers.products.segmentation_service.create_segment", new_callable=AsyncMock, return_value=_SEGMENT):
        resp = client.post("/api/v1/segments/", json={"name": "Legal Premium", "rules": {"industry": "Legal"}})
    assert resp.status_code == 200
    assert resp.json()["name"] == "Legal Premium"


def test_delete_segment():
    with patch("app.routers.products.segmentation_service.delete_segment", new_callable=AsyncMock, return_value=True):
        resp = client.delete("/api/v1/segments/seg-1")
    assert resp.status_code == 200
    assert resp.json()["ok"] is True


# ── Analytics ─────────────────────────────────────────────────
def test_tag_analytics():
    tags = [{"tag": "Legal", "count": 30, "avgScore": 72}]
    with patch("app.routers.products.segmentation_service.get_tag_analytics", new_callable=AsyncMock, return_value=tags):
        resp = client.get("/api/v1/segments/analytics/tags")
    assert resp.status_code == 200
    assert resp.json()[0]["tag"] == "Legal"


def test_industry_segments():
    data = [{"industry": "Legal", "total": 50, "avgScore": 65, "statusBreakdown": {"qualified": 10}}]
    with patch("app.routers.products.segmentation_service.get_industry_segments", new_callable=AsyncMock, return_value=data):
        resp = client.get("/api/v1/segments/analytics/industries")
    assert resp.status_code == 200
    assert resp.json()[0]["total"] == 50


def test_source_performance():
    data = [{"source": "playbook", "total": 100, "converted": 25, "conversionRate": 25.0}]
    with patch("app.routers.products.segmentation_service.get_source_performance", new_callable=AsyncMock, return_value=data):
        resp = client.get("/api/v1/segments/analytics/sources")
    assert resp.status_code == 200
    assert resp.json()[0]["conversionRate"] == 25.0