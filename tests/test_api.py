"""
Tests for KubePulse SRE Flask API and Web Endpoints
"""

import pytest
from app import create_app


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_healthz_endpoint(client):
    response = client.get("/healthz")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "UP"


def test_api_telemetry_endpoint(client):
    response = client.get("/api/telemetry")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "success"
    assert "slo" in data
    assert "overview" in data


def test_api_traces_endpoint(client):
    response = client.get("/api/traces")
    assert response.status_code == 200
    data = response.get_json()
    assert "traces" in data
    assert "percentiles" in data


def test_ui_pages_return_200(client):
    pages = ["/", "/dashboard", "/topology", "/slo", "/traces", "/incidents", "/chaos"]
    for page in pages:
        res = client.get(page)
        assert res.status_code == 200, f"Page {page} returned status {res.status_code}"


def test_api_chaos_lifecycle(client):
    # Inject chaos
    inject_res = client.post("/api/chaos/inject", json={
        "type": "error_spike",
        "target_service": "order-service",
        "duration": 60
    })
    assert inject_res.status_code == 200
    inject_data = inject_res.get_json()
    assert inject_data["status"] == "success"

    # Stop chaos
    stop_res = client.post("/api/chaos/stop")
    assert stop_res.status_code == 200
    stop_data = stop_res.get_json()
    assert stop_data["status"] == "STOPPED"


def test_api_auto_heal_endpoint(client):
    heal_res = client.post("/api/heal", json={"action": "AUTO"})
    assert heal_res.status_code == 200
    data = heal_res.get_json()
    assert data["status"] == "SUCCESS"
