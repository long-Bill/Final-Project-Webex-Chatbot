import json
from app import app

def test_health():
    c = app.test_client()
    r = c.get("/health")
    assert r.status_code == 200
    assert r.json.get("ok") is True

def test_metrics():
    c = app.test_client()
    r = c.get("/metrics")
    assert r.status_code == 200
    assert b"webexbot_requests_total" in r.data
