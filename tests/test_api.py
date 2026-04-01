import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from taskmq.api_server import app, create_token
from taskmq.storage.base import Job, JobStatus
from datetime import datetime, UTC

client = TestClient(app)

@pytest.fixture
def mock_backend():
    with patch("taskmq.api_server.get_backend") as mock:
        backend_instance = MagicMock()
        mock.return_value = backend_instance
        yield backend_instance

def test_health_check(mock_backend):
    mock_backend.check_health.return_value = True
    response = client.get("/health")
    # It might return 200 or 500 depending on heartbeat file, but let's check basic connectivity
    # The health endpoint checks heartbeat file too.
    # If heartbeat file missing, it returns {"status": "ok", "worker": "unknown"} (based on my edit)
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_add_job_unauthorized():
    response = client.post("/add-job", json={"payload": {"task": "test"}})
    assert response.status_code == 401

def test_add_job_authorized(mock_backend):
    token = create_token("admin", "admin")
    headers = {"Authorization": f"Bearer {token}"}
    
    mock_backend.insert_job.return_value = 123
    
    response = client.post("/add-job", json={"payload": {"task": "test"}}, headers=headers)
    assert response.status_code == 200
    assert response.json()["job_id"] == 123
    mock_backend.insert_job.assert_called_once()

def test_get_job(mock_backend):
    token = create_token("admin", "admin")
    headers = {"Authorization": f"Bearer {token}"}
    
    job = Job(
        id=1,
        status=JobStatus.SUCCESS,
        payload={"task": "test"},
        created_at=datetime.now(UTC),
        result="Success"
    )
    mock_backend.get_job.return_value = job
    
    response = client.get("/job/1", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["result"] == "Success"

def test_cancel_job(mock_backend):
    token = create_token("admin", "admin")
    headers = {"Authorization": f"Bearer {token}"}
    
    job = Job(id=1, status=JobStatus.PENDING)
    mock_backend.get_job.return_value = job
    
    response = client.post("/cancel", json={"job_id": 1}, headers=headers)
    assert response.status_code == 200
    mock_backend.update_status.assert_called_with(1, JobStatus.FAILED, 0, 'Cancelled by admin')
