"""
Cluster State Manager (Dual-Engine: Live Kubernetes API & Autonomous High-Fidelity Simulation)
Maintains cluster topology, node health, pod replica states, real-time telemetry metrics,
and incident histories.
"""

import time
import random
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from services.slo_engine import SLOEngine
from services.otel_tracer import OTelTracer
from services.k8s_client import K8sClient

logger = logging.getLogger("kubepulse.cluster_state")


class ClusterStateManager:
    """
    Central operational state repository for KubePulse SRE.
    Seamlessly synchronizes with a live Kubernetes cluster or powers an autonomous,
    high-fidelity simulated cluster with nodes, pods, and streaming metrics.
    """

    def __init__(self, mode: str = "auto", kubeconfig_path: Optional[str] = None):
        self.mode = mode
        self.k8s_client = K8sClient(kubeconfig_path=kubeconfig_path)
        self.slo_engine = SLOEngine(target_availability=99.9, target_p99_ms=250.0)
        self.tracer = OTelTracer(max_history=50)

        # Operational metrics tracking
        self.total_requests = 142850
        self.failed_requests = 42
        self.cumulative_budget_consumed = 14.5  # % of 30-day budget consumed
        self.error_rate_1h = 0.00028  # 0.028% (Burn rate ~ 0.28x)
        self.error_rate_6h = 0.00035  # 0.035% (Burn rate ~ 0.35x)
        self.current_latency_p99 = 112.5  # ms

        # Incidents repository
        self.incidents: List[Dict[str, Any]] = []

        # Chaos state
        self.active_chaos: Optional[Dict[str, Any]] = None

        # Simulation Topology Setup
        self._init_simulation_topology()

    def _init_simulation_topology(self):
        """Initializes simulated nodes and microservice pods."""
        self.nodes = [
            {
                "name": "worker-node-01",
                "zone": "us-east-1a",
                "status": "Ready",
                "cpu_cores": 4,
                "cpu_usage_percent": 34.2,
                "memory_total_gib": 16.0,
                "memory_usage_percent": 58.6,
                "kubelet_version": "v1.29.2",
                "os_image": "Ubuntu 22.04 LTS (Jammy Jellyfish)",
                "pod_count": 4
            },
            {
                "name": "worker-node-02",
                "zone": "us-east-1b",
                "status": "Ready",
                "cpu_cores": 4,
                "cpu_usage_percent": 41.5,
                "memory_total_gib": 16.0,
                "memory_usage_percent": 63.1,
                "kubelet_version": "v1.29.2",
                "os_image": "Ubuntu 22.04 LTS (Jammy Jellyfish)",
                "pod_count": 4
            },
            {
                "name": "worker-node-03",
                "zone": "us-east-1c",
                "status": "Ready",
                "cpu_cores": 8,
                "cpu_usage_percent": 29.8,
                "memory_total_gib": 32.0,
                "memory_usage_percent": 44.7,
                "kubelet_version": "v1.29.2",
                "os_image": "Ubuntu 22.04 LTS (Jammy Jellyfish)",
                "pod_count": 4
            }
        ]

        self.pods = [
            # Ingress Gateway (2 replicas)
            {
                "id": "pod-1",
                "name": "ingress-gateway-7b9c9f4d76-x8r9q",
                "service": "ingress-gateway",
                "namespace": "production",
                "node": "worker-node-01",
                "ip": "10.244.1.14",
                "status": "Running",
                "restarts": 0,
                "cpu_millicores": 85,
                "memory_mib": 142,
                "memory_limit_mib": 512,
                "version": "v2.4.1",
                "uptime": "14d 6h"
            },
            {
                "id": "pod-2",
                "name": "ingress-gateway-7b9c9f4d76-v2p4k",
                "service": "ingress-gateway",
                "namespace": "production",
                "node": "worker-node-02",
                "ip": "10.244.2.18",
                "status": "Running",
                "restarts": 0,
                "cpu_millicores": 92,
                "memory_mib": 148,
                "memory_limit_mib": 512,
                "version": "v2.4.1",
                "uptime": "14d 6h"
            },
            # Auth Service (2 replicas)
            {
                "id": "pod-3",
                "name": "auth-service-589f86588d-m2kqw",
                "service": "auth-service",
                "namespace": "production",
                "node": "worker-node-01",
                "ip": "10.244.1.25",
                "status": "Running",
                "restarts": 1,
                "cpu_millicores": 110,
                "memory_mib": 210,
                "memory_limit_mib": 512,
                "version": "v1.8.0",
                "uptime": "8d 3h"
            },
            {
                "id": "pod-4",
                "name": "auth-service-589f86588d-9zlw8",
                "service": "auth-service",
                "namespace": "production",
                "node": "worker-node-03",
                "ip": "10.244.3.11",
                "status": "Running",
                "restarts": 0,
                "cpu_millicores": 105,
                "memory_mib": 204,
                "memory_limit_mib": 512,
                "version": "v1.8.0",
                "uptime": "14d 6h"
            },
            # Order Service (3 replicas)
            {
                "id": "pod-5",
                "name": "order-service-67845f9cc7-p4jnl",
                "service": "order-service",
                "namespace": "production",
                "node": "worker-node-02",
                "ip": "10.244.2.33",
                "status": "Running",
                "restarts": 0,
                "cpu_millicores": 175,
                "memory_mib": 320,
                "memory_limit_mib": 768,
                "version": "v3.1.2",
                "uptime": "5d 11h"
            },
            {
                "id": "pod-6",
                "name": "order-service-67845f9cc7-k78bm",
                "service": "order-service",
                "namespace": "production",
                "node": "worker-node-01",
                "ip": "10.244.1.41",
                "status": "Running",
                "restarts": 0,
                "cpu_millicores": 168,
                "memory_mib": 315,
                "memory_limit_mib": 768,
                "version": "v3.1.2",
                "uptime": "5d 11h"
            },
            {
                "id": "pod-7",
                "name": "order-service-67845f9cc7-tr5w1",
                "service": "order-service",
                "namespace": "production",
                "node": "worker-node-03",
                "ip": "10.244.3.22",
                "status": "Running",
                "restarts": 0,
                "cpu_millicores": 182,
                "memory_mib": 328,
                "memory_limit_mib": 768,
                "version": "v3.1.2",
                "uptime": "5d 11h"
            },
            # Payment Gateway (2 replicas)
            {
                "id": "pod-8",
                "name": "payment-gateway-84bc4675df-w9ztv",
                "service": "payment-gateway",
                "namespace": "production",
                "node": "worker-node-02",
                "ip": "10.244.2.49",
                "status": "Running",
                "restarts": 0,
                "cpu_millicores": 140,
                "memory_mib": 275,
                "memory_limit_mib": 512,
                "version": "v2.0.4",
                "uptime": "19d 1h"
            },
            {
                "id": "pod-9",
                "name": "payment-gateway-84bc4675df-c8d4e",
                "service": "payment-gateway",
                "namespace": "production",
                "node": "worker-node-03",
                "ip": "10.244.3.37",
                "status": "Running",
                "restarts": 0,
                "cpu_millicores": 136,
                "memory_mib": 268,
                "memory_limit_mib": 512,
                "version": "v2.0.4",
                "uptime": "19d 1h"
            },
            # Database Proxy (3 replicas)
            {
                "id": "pod-10",
                "name": "database-proxy-5dc8bbf68c-l5k3x",
                "service": "database-proxy",
                "namespace": "production",
                "node": "worker-node-03",
                "ip": "10.244.3.50",
                "status": "Running",
                "restarts": 0,
                "cpu_millicores": 215,
                "memory_mib": 480,
                "memory_limit_mib": 1024,
                "version": "v1.4.0",
                "uptime": "25d 14h"
            },
            {
                "id": "pod-11",
                "name": "database-proxy-5dc8bbf68c-q7nm4",
                "service": "database-proxy",
                "namespace": "production",
                "node": "worker-node-01",
                "ip": "10.244.1.62",
                "status": "Running",
                "restarts": 0,
                "cpu_millicores": 208,
                "memory_mib": 465,
                "memory_limit_mib": 1024,
                "version": "v1.4.0",
                "uptime": "25d 14h"
            },
            {
                "id": "pod-12",
                "name": "database-proxy-5dc8bbf68c-b9v2z",
                "service": "database-proxy",
                "namespace": "production",
                "node": "worker-node-02",
                "ip": "10.244.2.71",
                "status": "Running",
                "restarts": 0,
                "cpu_millicores": 220,
                "memory_mib": 490,
                "memory_limit_mib": 1024,
                "version": "v1.4.0",
                "uptime": "25d 14h"
            }
        ]

    def is_live_cluster_active(self) -> bool:
        """Returns True if connected to an authentic Kubernetes cluster."""
        return self.mode != "simulation" and self.k8s_client.is_connected()

    def get_cluster_overview(self) -> Dict[str, Any]:
        """Provides an aggregated view of cluster nodes, pods, and overall status."""
        live_active = self.is_live_cluster_active()
        nodes = self.k8s_client.get_cluster_nodes() if live_active else self.nodes
        pods = self.k8s_client.get_cluster_pods() if live_active else self.pods

        ready_nodes = sum(1 for n in nodes if n.get("status") in ("Ready", "True"))
        running_pods = sum(1 for p in pods if p.get("status") in ("Running", "Completed"))
        failing_pods = len(pods) - running_pods

        return {
            "mode": "Live Cluster" if live_active else "Autonomous Simulation",
            "connected_to_real_k8s": live_active,
            "total_nodes": len(nodes),
            "ready_nodes": ready_nodes,
            "total_pods": len(pods),
            "running_pods": running_pods,
            "failing_pods": failing_pods,
            "cluster_health_score": round((ready_nodes / max(1, len(nodes)) * 50) + (running_pods / max(1, len(pods)) * 50), 1),
            "active_chaos": self.active_chaos is not None,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    def tick_telemetry(self) -> Dict[str, Any]:
        """
        Simulates dynamic traffic pulse across the cluster:
        - Increment requests
        - Generate distributed trace
        - Apply active chaos impacts
        - Re-evaluate SLO metrics
        """
        # Increment synthetic requests
        new_batch = random.randint(120, 240)
        self.total_requests += new_batch

        # Determine if chaos is impacting traffic
        chaos_fail = 0
        target_service = None
        chaos_type = None
        latency_boost = 0.0

        if self.active_chaos:
            target_service = self.active_chaos.get("target_service")
            chaos_type = self.active_chaos.get("type")
            
            if chaos_type == "error_spike":
                # Inject 35-50% 500 errors
                chaos_fail = int(new_batch * random.uniform(0.35, 0.50))
                self.error_rate_1h = min(0.045, self.error_rate_1h + 0.003)
                self.error_rate_6h = min(0.020, self.error_rate_6h + 0.001)
                self.cumulative_budget_consumed = min(100.0, self.cumulative_budget_consumed + 1.2)
                self.current_latency_p99 = min(980.0, self.current_latency_p99 + 25.0)

            elif chaos_type == "latency":
                latency_boost = float(self.active_chaos.get("latency_ms", 350.0))
                self.current_latency_p99 = min(1200.0, 180.0 + latency_boost + random.uniform(-20, 20))
                # Slight error trickle from timeouts
                chaos_fail = int(new_batch * 0.02)
                self.error_rate_1h = min(0.015, self.error_rate_1h + 0.0005)

            elif chaos_type == "oom_kill":
                chaos_fail = int(new_batch * 0.15)
                self.error_rate_1h = min(0.025, self.error_rate_1h + 0.001)
                self.cumulative_budget_consumed = min(100.0, self.cumulative_budget_consumed + 0.4)

        else:
            # Healthy baseline jitter
            normal_error_chance = 0.0002
            chaos_fail = 1 if random.random() < normal_error_chance else 0
            # Gently heal/stabilize error rates towards baseline
            self.error_rate_1h = max(0.00025, self.error_rate_1h * 0.98)
            self.error_rate_6h = max(0.00030, self.error_rate_6h * 0.99)
            self.current_latency_p99 = max(95.0, min(140.0, self.current_latency_p99 + random.uniform(-4, 4)))

        self.failed_requests += chaos_fail

        # Generate a new distributed trace
        trace = self.tracer.create_trace(
            chaos_target=target_service,
            chaos_type=chaos_type,
            latency_boost_ms=latency_boost
        )

        # Evaluate SLO metrics
        slo_eval = self.slo_engine.evaluate(
            total_requests=self.total_requests,
            failed_requests=self.failed_requests,
            latency_p99_ms=self.current_latency_p99,
            error_rate_1h=self.error_rate_1h,
            error_rate_6h=self.error_rate_6h,
            cumulative_budget_consumed_percent=self.cumulative_budget_consumed
        )

        # Auto-create incident if Burn Rate >= 6.0 and no active incident exists
        if (slo_eval["burn_rate_1h"] >= 14.4 or slo_eval["burn_rate_6h"] >= 6.0) and not any(i["status"] == "ACTIVE" for i in self.incidents):
            self.create_incident_from_slo(slo_eval, target_service or "ingress-gateway")

        return {
            "slo": slo_eval,
            "latest_trace": trace,
            "percentiles": self.tracer.get_percentiles(),
            "nodes": self.nodes,
            "pods": self.pods,
            "active_chaos": self.active_chaos,
            "active_incidents_count": sum(1 for i in self.incidents if i["status"] == "ACTIVE")
        }

    def create_incident_from_slo(self, slo_eval: Dict[str, Any], service: str):
        """Constructs an SRE Incident object with AI-suggested remediation."""
        incident_id = f"INC-{int(time.time())}"
        severity = slo_eval["severity"]
        burn_rate = slo_eval["burn_rate_1h"]

        rca_details = {
            "root_cause": f"Abnormal 5xx failure spike and elevated latency in {service} violating 30-day Error Budget.",
            "impact": f"Consuming error budget at {burn_rate}x normal rate. Remaining: {slo_eval['remaining_budget_percent']}%.",
            "recommended_action": "Roll back recent deployment canary revision and increase pod memory limits."
        }

        incident = {
            "id": incident_id,
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            "service": service,
            "severity": severity,
            "status": "ACTIVE",
            "title": f"Critical Error Budget Burn Rate Detected on {service}",
            "burn_rate": burn_rate,
            "error_rate": slo_eval["instant_error_rate"],
            "latency_p99": slo_eval["current_p99_ms"],
            "rca": rca_details,
            "remediated_at": None,
            "action_taken": None
        }
        self.incidents.insert(0, incident)
        logger.warning("Created SRE Incident: %s (%s)", incident_id, severity)

    def resolve_incident(self, incident_id: str, remediation_action: str) -> bool:
        """Marks an incident as remediated and stabilizes metrics."""
        for inc in self.incidents:
            if inc["id"] == incident_id:
                inc["status"] = "RESOLVED"
                inc["remediated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
                inc["action_taken"] = remediation_action
                # Clear chaos if matching
                self.active_chaos = None
                self.error_rate_1h = 0.0003
                self.error_rate_6h = 0.00035
                self.current_latency_p99 = 110.0
                return True
        return False
