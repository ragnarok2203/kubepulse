"""
Tests for SRE Autonomous Self-Healing Engine
"""

import pytest
from services.cluster_state import ClusterStateManager
from services.auto_healer import AutoHealer


def test_canary_rollback_remediation():
    state = ClusterStateManager(mode="simulation")
    healer = AutoHealer(state)

    # Create dummy incident
    state.incidents.append({
        "id": "INC-TEST-1",
        "service": "order-service",
        "status": "ACTIVE",
        "severity": "CRITICAL"
    })

    result = healer.execute_remediation(incident_id="INC-TEST-1", action_type="CANARY_ROLLBACK")
    assert result["status"] == "SUCCESS"
    assert result["action_type"] == "CANARY_ROLLBACK"
    assert "Canary Rollback executed" in result["summary"]
    assert len(result["steps"]) >= 4

    # Incident should be resolved
    assert state.incidents[0]["status"] == "RESOLVED"


def test_pod_restart_remediation():
    state = ClusterStateManager(mode="simulation")
    healer = AutoHealer(state)

    result = healer.execute_remediation(incident_id="", action_type="POD_RESTART")
    assert result["status"] == "SUCCESS"
    assert "restarted" in result["summary"].lower()


def test_tune_memory_remediation():
    state = ClusterStateManager(mode="simulation")
    healer = AutoHealer(state)

    initial_limit = next(p["memory_limit_mib"] for p in state.pods if p["service"] == "ingress-gateway")
    result = healer.execute_remediation(incident_id="", action_type="TUNE_MEMORY")
    assert result["status"] == "SUCCESS"

    new_limit = next(p["memory_limit_mib"] for p in state.pods if p["service"] == "ingress-gateway")
    assert new_limit > initial_limit
