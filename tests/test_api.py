import io 
import pytest
from fastapi.testclient import TestClient
from app.main import app 
from app.tasks.image_tasks import refine_sketch_task

client = TestClient(app)

def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}

def test_refine_endpoint_bad_upload():
    r = client.post("/api/sketch/refine", files={})
    assert r.status_code == 422

def test_refine_emdpoint_bad_upload(monkeypatch):

    class DummyJob:
        id = "fake_job"
    
    monkeypatch.setattr(refine_sketch_task, "delay", lambda prompt, data: DummyJob())


    fake_img = io.BytesIO(b"\x00\x01")
    fake_img.name = "fake.png"
    r = client.post(
        "/api/sketch/refine",
        files={"file": ("fake.png", fake_img, "image/png")}
    )
    assert r.status_code == 200
    body = r.json()
    assert body["job_id"] == "fake_job"
    assert body["status"] == "PENDING"


