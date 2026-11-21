"""
Tests for OpenTelemetry Distributed Tracing & Waterfall Analyzer
"""

import pytest
from services.otel_tracer import OTelTracer


def test_trace_creation():
    tracer = OTelTracer(max_history=10)
    trace = tracer.create_trace()

    assert len(trace["trace_id"]) == 32
    assert trace["span_count"] == 5
    assert trace["root_service"] == "ingress-gateway"
    assert trace["total_duration_ms"] > 0
    assert trace["bottleneck_service"] in [
        "ingress-gateway", "auth-service", "order-service", "payment-gateway", "database-proxy"
    ]


def test_percentile_calculation():
    tracer = OTelTracer(max_history=20)
    for _ in range(15):
        tracer.create_trace()

    percentiles = tracer.get_percentiles()
    assert "p50" in percentiles
    assert "p90" in percentiles
    assert "p95" in percentiles
    assert "p99" in percentiles
    assert percentiles["p50"] <= percentiles["p99"]


def test_chaos_trace_injection():
    tracer = OTelTracer(max_history=10)
    # Inject error spike in order-service
    trace = tracer.create_trace(chaos_target="order-service", chaos_type="error_spike")

    assert trace["status"] == "ERROR"
    order_span = next(s for s in trace["spans"] if s["service"] == "order-service")
    assert order_span["status_code"] == 500
