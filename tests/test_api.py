import io
import json
import pytest
from PIL import Image
from app import create_app
from config import TestConfig

@pytest.fixture
def client(tmp_path):
    class DynamicTestConfig(TestConfig):
        UPLOAD_FOLDER = str(tmp_path / "uploads")
        OUTPUT_FOLDER = str(tmp_path / "outputs")
        SAMPLE_FOLDER = str(tmp_path / "samples")
        
    app = create_app(DynamicTestConfig)
    with app.test_client() as client:
        yield client

def test_full_api_workflow(client):
    # 1. Create a dummy test image in memory
    img_io = io.BytesIO()
    img = Image.new("RGB", (150, 100), color=(80, 120, 160))
    img.save(img_io, format="PNG")
    img_io.seek(0)
    
    # 2. Upload image via POST /api/images/upload
    upload_res = client.post(
        "/api/images/upload",
        data={"image": (img_io, "test_pic.png")},
        content_type="multipart/form-data"
    )
    assert upload_res.status_code == 200
    upload_data = upload_res.get_json()
    assert upload_data["status"] == "success"
    experiment_id = upload_data["experiment_id"]
    assert experiment_id is not None
    assert upload_data["metadata"]["width"] == 150
    assert upload_data["metadata"]["height"] == 100
    
    # 3. Trigger asynchronous benchmark via POST /api/experiments
    exp_res = client.post(
        "/api/experiments",
        json={
            "experiment_id": experiment_id,
            "formats": ["JPEG", "WEBP"],
            "qualities": [50, 80]
        }
    )
    assert exp_res.status_code == 202
    exp_data = exp_res.get_json()
    assert exp_data["status"] == "accepted"
    task_id = exp_data["task_id"]
    assert task_id is not None

    # 4. Check Celery task status via GET /api/status/<task_id>
    task_status_res = client.get(f"/api/status/{task_id}")
    assert task_status_res.status_code == 200
    task_status_data = task_status_res.get_json()
    assert task_status_data["state"] == "SUCCESS"
    assert task_status_data["percent"] == 100

    # 5. Check experiment state via GET /api/experiments/<id>
    status_res = client.get(f"/api/experiments/{experiment_id}")
    assert status_res.status_code == 200
    assert status_res.get_json()["state"] == "completed"
    
    # 5. Fetch comparison results via GET /api/experiments/<id>/results
    results_res = client.get(f"/api/experiments/{experiment_id}/results")
    assert results_res.status_code == 200
    assert len(results_res.get_json()["data"]["results"]) >= 2
    
    # 6. Export CSV report via GET /api/experiments/<id>/report?format=csv
    report_res = client.get(f"/api/experiments/{experiment_id}/report?format=csv")
    assert report_res.status_code == 200
    assert "text/csv" in report_res.content_type
    assert b"B\xc3\x81O C\xc3\x81O" in report_res.data or "BÁO CÁO".encode("utf-8") in report_res.data
    
    # 7. Delete experiment via DELETE /api/experiments/<id>
    del_res = client.delete(f"/api/experiments/{experiment_id}")
    assert del_res.status_code == 200
    
    # Verify it is deleted
    del_check = client.get(f"/api/experiments/{experiment_id}")
    assert del_check.status_code == 404

def test_health_endpoint(client):
    """Verifies that the Docker container healthcheck endpoint returns 200 OK."""
    res = client.get("/health")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "healthy"
    assert data["service"] == "XLA_TGMT"


