"""
OpenTelemetry Distributed Tracing Synthesizer & Span Analyzer
Simulates realistic microservice trace trees (W3C TraceContext standard),
computes P50, P90, P95, and P99 percentiles, and detects critical-path bottlenecks.
"""

import uuid
import time
import random
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone


def generate_trace_id() -> str:
    """Generates a 32-character hexadecimal OpenTelemetry TraceID."""
    return uuid.uuid4().hex


def generate_span_id() -> str:
    """Generates a 16-character hexadecimal OpenTelemetry SpanID."""
    return uuid.uuid4().hex[:16]


class OTelTracer:
    """
    OpenTelemetry trace synthesizer and waterfall span analyzer.
    """

    def __init__(self, max_history: int = 50):
        self.max_history = max_history
        self.trace_history: List[Dict[str, Any]] = []

    def create_trace(
        self,
        chaos_target: Optional[str] = None,
        chaos_type: Optional[str] = None,
        latency_boost_ms: float = 0.0
    ) -> Dict[str, Any]:
        """
        Synthesizes a realistic distributed trace through the Kubernetes microservice mesh:
        ingress-gateway -> auth-service -> order-service -> payment-gateway -> database-proxy
        """
        trace_id = generate_trace_id()
        timestamp = datetime.now(timezone.utc).isoformat()

        # Base latencies for each service in healthy state (ms)
        latencies = {
            "ingress-gateway": round(random.uniform(5.0, 15.0), 2),
            "auth-service": round(random.uniform(10.0, 30.0), 2),
            "order-service": round(random.uniform(20.0, 60.0), 2),
            "payment-gateway": round(random.uniform(35.0, 85.0), 2),
            "database-proxy": round(random.uniform(15.0, 45.0), 2),
        }

        # Status codes default to 200 OK
        status_codes = {k: 200 for k in latencies}

        # Apply chaos injection if active
        if chaos_target and chaos_target in latencies:
            if chaos_type == "latency":
                latencies[chaos_target] += latency_boost_ms
            elif chaos_type == "error_spike":
                status_codes[chaos_target] = 500
                latencies[chaos_target] += round(random.uniform(150.0, 400.0), 2)
            elif chaos_type == "oom_kill":
                status_codes[chaos_target] = 502
                latencies[chaos_target] += 50.0

        # Construct hierarchical spans
        # 1. Root Span: ingress-gateway
        ingress_span_id = generate_span_id()
        # 2. auth-service span
        auth_span_id = generate_span_id()
        # 3. order-service span
        order_span_id = generate_span_id()
        # 4. payment-gateway span
        payment_span_id = generate_span_id()
        # 5. database-proxy span
        db_span_id = generate_span_id()

        total_trace_duration = (
            latencies["ingress-gateway"] +
            latencies["auth-service"] +
            latencies["order-service"] +
            latencies["payment-gateway"] +
            latencies["database-proxy"]
        )

        spans = [
            {
                "span_id": ingress_span_id,
                "parent_span_id": None,
                "service": "ingress-gateway",
                "operation": "HTTP GET /api/v1/checkout",
                "duration_ms": round(latencies["ingress-gateway"], 2),
                "status_code": status_codes["ingress-gateway"],
                "start_offset_ms": 0.0,
                "node": "worker-node-01",
                "pod": "ingress-gateway-7b9c9f4d76-x8r9q"
            },
            {
                "span_id": auth_span_id,
                "parent_span_id": ingress_span_id,
                "service": "auth-service",
                "operation": "RPC ValidateSessionToken",
                "duration_ms": round(latencies["auth-service"], 2),
                "status_code": status_codes["auth-service"],
                "start_offset_ms": round(latencies["ingress-gateway"], 2),
                "node": "worker-node-01",
                "pod": "auth-service-589f86588d-m2kqw"
            },
            {
                "span_id": order_span_id,
                "parent_span_id": auth_span_id,
                "service": "order-service",
                "operation": "HTTP POST /internal/orders",
                "duration_ms": round(latencies["order-service"], 2),
                "status_code": status_codes["order-service"],
                "start_offset_ms": round(latencies["ingress-gateway"] + latencies["auth-service"], 2),
                "node": "worker-node-02",
                "pod": "order-service-67845f9cc7-p4jnl"
            },
            {
                "span_id": payment_span_id,
                "parent_span_id": order_span_id,
                "service": "payment-gateway",
                "operation": "RPC AuthorizeTransaction",
                "duration_ms": round(latencies["payment-gateway"], 2),
                "status_code": status_codes["payment-gateway"],
                "start_offset_ms": round(latencies["ingress-gateway"] + latencies["auth-service"] + latencies["order-service"], 2),
                "node": "worker-node-02",
                "pod": "payment-gateway-84bc4675df-w9ztv"
            },
            {
                "span_id": db_span_id,
                "parent_span_id": payment_span_id,
                "service": "database-proxy",
                "operation": "SQL ExecuteBatchTransaction",
                "duration_ms": round(latencies["database-proxy"], 2),
                "status_code": status_codes["database-proxy"],
                "start_offset_ms": round(total_trace_duration - latencies["database-proxy"], 2),
                "node": "worker-node-03",
                "pod": "database-proxy-5dc8bbf68c-l5k3x"
            }
        ]

        # Determine critical bottleneck span (longest or non-200)
        bottleneck_span = max(spans, key=lambda s: (s["status_code"] >= 400, s["duration_ms"]))

        trace_summary = {
            "trace_id": trace_id,
            "timestamp": timestamp,
            "root_service": "ingress-gateway",
            "total_duration_ms": round(total_trace_duration, 2),
            "status": "ERROR" if any(s["status_code"] >= 400 for s in spans) else "OK",
            "span_count": len(spans),
            "bottleneck_service": bottleneck_span["service"],
            "bottleneck_duration_ms": bottleneck_span["duration_ms"],
            "spans": spans
        }

        self.trace_history.insert(0, trace_summary)
        if len(self.trace_history) > self.max_history:
            self.trace_history.pop()

        return trace_summary

    def get_percentiles(self) -> Dict[str, float]:
        """Calculates P50, P90, P95, and P99 latency percentiles across stored traces."""
        if not self.trace_history:
            return {"p50": 0.0, "p90": 0.0, "p95": 0.0, "p99": 0.0}

        durations = sorted([t["total_duration_ms"] for t in self.trace_history])
        n = len(durations)

        def percentile(p: float) -> float:
            idx = int(p * n)
            return round(durations[min(idx, n - 1)], 2)

        return {
            "p50": percentile(0.50),
            "p90": percentile(0.90),
            "p95": percentile(0.95),
            "p99": percentile(0.99),
        }

    def get_recent_traces(self, limit: int = 15) -> List[Dict[str, Any]]:
        """Returns the most recent trace summaries."""
        return self.trace_history[:limit]

    def get_trace_by_id(self, trace_id: str) -> Optional[Dict[str, Any]]:
        """Finds a specific trace by ID."""
        for t in self.trace_history:
            if t["trace_id"] == trace_id:
                return t
        return None
