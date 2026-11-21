"""
Tests for Cluster State Manager & Telemetry Engine
"""

import pytest
from services.cluster_state import ClusterStateManager


def test_cluster_initialization():
    state = ClusterStateManager(mode="simulation")
    overview = state.get_cluster_overview()

    assert overview["total_nodes"] == 3
    assert overview["total_pods"] == 12
    assert overview["cluster_health_score"] >= 90.0
    assert overview["mode"] == "Autonomous Simulation"
    assert not overview["active_chaos"]


def test_telemetry_tick():
    state = ClusterStateManager(mode="simulation")
    initial_requests = state.total_requests

    telemetry = state.tick_telemetry()
    assert state.total_requests > initial_requests
    assert "slo" in telemetry
    assert "latest_trace" in telemetry
    assert len(telemetry["nodes"]) == 3
    assert len(telemetry["pods"]) == 12


def test_incident_creation_and_resolution():
    state = ClusterStateManager(mode="simulation")
    assert len(state.incidents) == 0

    # Simulate critical SLO evaluation
    slo_eval = state.slo_engine.evaluate(
        total_requests=1000,
        failed_requests=100,
        latency_p99_ms=450.0,
        error_rate_1h=0.025,  # 25x burn rate
        error_rate_6h=0.015,
        cumulative_budget_consumed_percent=30.0
    )
    state.create_incident_from_slo(slo_eval, "order-service")

    assert len(state.incidents) == 1
    incident = state.incidents[0]
    assert incident["status"] == "ACTIVE"
    assert incident["service"] == "order-service"
    assert incident["severity"] == "CRITICAL"

    # Resolve incident
    resolved = state.resolve_incident(incident["id"], "Canary rollback verified")
    assert resolved is True
    assert state.incidents[0]["status"] == "RESOLVED"
    assert state.incidents[0]["action_taken"] == "Canary rollback verified"
