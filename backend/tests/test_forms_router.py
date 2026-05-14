import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from app.main import app

client = TestClient(app)

def test_submit_playbook_no_consent():
    response = client.post("/api/v1/forms/playbook", json={
        "email": "test@test.com",
        "firstName": "Test",
        "consent_given": False,
        "consent_text": "I do not consent"
    })
    
    assert response.status_code == 422
    assert "Consenso GDPR obbligatorio" in response.json()["detail"]

def test_submit_playbook_success():
    with patch("app.routers.forms.LeadService.create_or_update_from_form", new_callable=AsyncMock) as mock_create:
        mock_create.return_value = {"id": "lead_123"}
        with patch("app.routers.forms.log_consent", new_callable=AsyncMock) as mock_log:
            with patch("app.routers.forms.enqueue_task", new_callable=AsyncMock) as mock_enqueue:
                
                response = client.post("/api/v1/forms/playbook", json={
                    "email": "test@test.com",
                    "firstName": "Test",
                    "consent_given": True,
                    "consent_text": "I consent"
                })
                
                assert response.status_code == 201
                assert response.json()["success"] is True
                assert "download_url" in response.json()
                
                mock_create.assert_called_once()
                mock_log.assert_called_once()
                assert mock_enqueue.call_count == 2

def test_submit_contact_success():
    with patch("app.routers.forms.LeadService.create_or_update_from_form", new_callable=AsyncMock) as mock_create:
        mock_create.return_value = {"id": "lead_123"}
        with patch("app.routers.forms.log_consent", new_callable=AsyncMock) as mock_log:
            with patch("app.routers.forms.enqueue_task", new_callable=AsyncMock) as mock_enqueue:
                with patch("app.routers.forms.send_sales_notification", new_callable=AsyncMock) as mock_send:
                    response = client.post("/api/v1/forms/contact", json={
                        "email": "test@test.com",
                        "firstName": "Test",
                        "lastName": "User",
                        "message": "Hello",
                        "consent_given": True,
                        "consent_text": "I consent"
                    })
                    
                    assert response.status_code == 201
                    assert response.json()["success"] is True
                    
                    mock_create.assert_called_once()
                    mock_log.assert_called_once()
                    mock_enqueue.assert_called_once()
                    mock_send.assert_called_once()
