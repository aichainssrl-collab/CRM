import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from app.main import app

client = TestClient(app)

@pytest.fixture
def mock_auth():
    with patch("app.deps.get_current_user") as mock_user:
        mock_user.return_value = AsyncMock(uid="user_1", role="sales", email="sales@test.com")
        yield mock_user

def test_create_lead_success(mock_auth):
    with patch("app.routers.leads.LeadService.find_by_email", new_callable=AsyncMock) as mock_find:
        mock_find.return_value = None
        with patch("app.routers.leads.LeadService.create_lead", new_callable=AsyncMock) as mock_create:
            mock_create.return_value = {"id": "lead_123", "email": "new@test.com"}
            with patch("app.routers.leads.enqueue_task", new_callable=AsyncMock) as mock_enqueue:
                
                # FastAPI TestClient bypassa le dipendenze in un modo particolare,
                # ma abbiamo patchato i metodi del service e deps.
                app.dependency_overrides = {}
                
                # Mockamo anche require_sales
                from app.deps import require_sales, UserRecord
                app.dependency_overrides[require_sales] = lambda: UserRecord(uid="user_1", role="sales", email="sales@test.com")
                
                response = client.post("/api/v1/leads", json={"email": "new@test.com", "firstName": "Test"})
                
                assert response.status_code == 201
                assert response.json()["id"] == "lead_123"
                mock_create.assert_called_once()
                mock_enqueue.assert_called_once()

def test_create_lead_conflict():
    with patch("app.routers.leads.LeadService.find_by_email", new_callable=AsyncMock) as mock_find:
        mock_find.return_value = {"id": "lead_123"}
        
        from app.deps import require_sales, UserRecord
        app.dependency_overrides[require_sales] = lambda: UserRecord(uid="user_1", role="sales", email="sales@test.com")
        
        response = client.post("/api/v1/leads", json={"email": "existing@test.com"})
        
        assert response.status_code == 409

def test_get_lead_found():
    with patch("app.routers.leads.LeadService.get_lead_with_activities", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = {"id": "lead_123", "email": "test@test.com"}
        
        from app.deps import require_sales, UserRecord
        app.dependency_overrides[require_sales] = lambda: UserRecord(uid="user_1", role="sales", email="sales@test.com")
        
        response = client.get("/api/v1/leads/lead_123")
        
        assert response.status_code == 200
        assert response.json()["id"] == "lead_123"

def test_get_lead_not_found():
    with patch("app.routers.leads.LeadService.get_lead_with_activities", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = None
        
        from app.deps import require_sales, UserRecord
        app.dependency_overrides[require_sales] = lambda: UserRecord(uid="user_1", role="sales", email="sales@test.com")
        
        response = client.get("/api/v1/leads/lead_123")
        
        assert response.status_code == 404

def test_update_lead():
    with patch("app.routers.leads.LeadService.update_lead", new_callable=AsyncMock) as mock_update:
        mock_update.return_value = {"id": "lead_123", "firstName": "Updated"}
        with patch("app.routers.leads.enqueue_task", new_callable=AsyncMock) as mock_enqueue:
            
            from app.deps import require_sales, UserRecord
            app.dependency_overrides[require_sales] = lambda: UserRecord(uid="user_1", role="sales", email="sales@test.com")
            
            response = client.patch("/api/v1/leads/lead_123", json={"firstName": "Updated"})
            
            assert response.status_code == 200
            assert response.json()["firstName"] == "Updated"
            mock_update.assert_called_once()
            mock_enqueue.assert_called_once()

def test_delete_lead_not_admin():
    from app.deps import require_admin, UserRecord
    # User is sales, not admin. But we must override require_admin to raise 403
    from fastapi import HTTPException
    app.dependency_overrides[require_admin] = lambda: (_ for _ in ()).throw(HTTPException(403, "Solo admin può eliminare lead"))
    
    response = client.delete("/api/v1/leads/lead_123")
    assert response.status_code == 403

def test_delete_lead_admin():
    from app.deps import require_admin, UserRecord
    # User is admin
    app.dependency_overrides[require_admin] = lambda: UserRecord(uid="user_1", role="admin", email="admin@test.com")
    
    with patch("app.routers.leads.LeadService.delete_lead", new_callable=AsyncMock) as mock_del:
        response = client.delete("/api/v1/leads/lead_123")
        assert response.status_code == 204
        mock_del.assert_called_once()
