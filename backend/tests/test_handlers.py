import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_cloud_tasks_auth_required():
    response = client.post("/tasks/handlers/recalculate-score", json={"lead_id": "123"})
    assert response.status_code == 403

def test_cloud_tasks_auth_success():
    with pytest.MonkeyPatch.context() as m:
        # Mock calculation
        async def mock_calc(*args, **kwargs):
            return 80
        import app.tasks.handlers as handlers
        m.setattr(handlers, "calculate_lead_score", mock_calc)
        
        response = client.post(
            "/tasks/handlers/recalculate-score", 
            json={"lead_id": "123"},
            headers={"Authorization": "Bearer fake_token"}
        )
        assert response.status_code == 200
        assert response.json()["score"] == 80
