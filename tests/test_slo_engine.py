"""
Tests for Google SRE Multi-Window Multi-Burn-Rate SLO Engine
"""

import pytest
from services.slo_engine import SLOEngine


def test_slo_engine_initialization():
    engine = SLOEngine(target_availability=99.9, target_p99_ms=250.0)
    assert engine.target_availability == 99.9
    assert engine.target_p99_ms == 250.0
    assert abs(engine.allowed_unreliability - 0.001) < 1e-6


def test_burn_rate_calculation():
    engine = SLOEngine(target_availability=99.9)  # allowed unreliability = 0.001
    # 0.1% error rate = exactly 1.0x burn rate
    assert engine.compute_burn_rate(0.001) == 1.0
    # 1.44% error rate = exactly 14.4x burn rate (2% in 1 hour alert)
    assert engine.compute_burn_rate(0.0144) == 14.4
    # 0.6% error rate = 6.0x burn rate (5% in 6 hours alert)
    assert engine.compute_burn_rate(0.006) == 6.0


def test_time_to_exhaustion():
    engine = SLOEngine(target_availability=99.9, rolling_window_days=30)
    # 100% budget at 1.0x burn rate lasts 30 days
    time_str = engine.calculate_time_to_exhaustion(100.0, 1.0)
    assert "30.0 days" in time_str

    # 0% remaining budget
    assert engine.calculate_time_to_exhaustion(0.0, 5.0) == "EXHAUSTED"

    # Fast burn: 10% budget at 14.4x burn rate = 5 hours
    time_fast = engine.calculate_time_to_exhaustion(10.0, 14.4)
    assert "hours" in time_fast


def test_evaluate_healthy_state():
    engine = SLOEngine(target_availability=99.9, target_p99_ms=250.0)
    eval_result = engine.evaluate(
        total_requests=100000,
        failed_requests=10,
        latency_p99_ms=115.0,
        error_rate_1h=0.0001,
        error_rate_6h=0.0001,
        cumulative_budget_consumed_percent=10.0
    )
    assert eval_result["severity"] == "HEALTHY"
    assert eval_result["status"] == "NORMAL"
    assert eval_result["remaining_budget_percent"] == 90.0
    assert eval_result["current_availability"] >= 99.9


def test_evaluate_critical_pager():
    engine = SLOEngine(target_availability=99.9, target_p99_ms=250.0)
    # Fast burn rate >= 14.4x
    eval_result = engine.evaluate(
        total_requests=10000,
        failed_requests=200,
        latency_p99_ms=350.0,
        error_rate_1h=0.020,  # 2.0% error rate -> burn rate 20.0x
        error_rate_6h=0.010,
        cumulative_budget_consumed_percent=45.0
    )
    assert eval_result["severity"] == "CRITICAL"
    assert eval_result["status"] == "PAGE_ON_CALL"
    assert "On-call paged" in eval_result["alert_message"]


def test_evaluate_budget_exhaustion():
    engine = SLOEngine(target_availability=99.9)
    eval_result = engine.evaluate(
        total_requests=50000,
        failed_requests=500,
        latency_p99_ms=180.0,
        error_rate_1h=0.001,
        error_rate_6h=0.001,
        cumulative_budget_consumed_percent=100.0  # 100% consumed
    )
    assert eval_result["severity"] == "CRITICAL"
    assert eval_result["status"] == "BUDGET_EXHAUSTED"
