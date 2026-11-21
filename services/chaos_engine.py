"""
Chaos Engineering Experiment Engine
Simulates real-world Kubernetes cloud failures (latency injection, 500 error spikes,
OOMKilled pod crashes, and cascading service outages) to validate SRE alert rules and self-healing.
"""

import time
import random
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from services.cluster_state import ClusterStateManager

logger = logging.getLogger("kubepulse.chaos_engine")


class ChaosEngine:
    """Chaos experiment controller."""

    def __init__(self, cluster_state: ClusterStateManager):
        self.state = cluster_state

    def inject_chaos(
        self,
        chaos_type: str,
        target_service: str = "order-service",
        duration_seconds: int = 120,
        latency_ms: float = 450.0
    ) -> Dict[str, Any]:
        """
        Injects a failure mode into the specified service.
        chaos_type: 'error_spike', 'latency', 'oom_kill', 'pod_kill'
        """
        chaos_id = f"CHAOS-{int(time.time())}"

        # Update simulated pods for this service to reflect failure
        affected_pods = []
        for pod in self.state.pods:
            if pod["service"] == target_service:
                affected_pods.append(pod["name"])
                if chaos_type == "oom_kill":
                    pod["status"] = "OOMKilled"
                    pod["restarts"] += 1
                    pod["memory_mib"] = int(pod["memory_limit_mib"] * 1.05)
                elif chaos_type == "error_spike":
                    pod["status"] = "Degraded"
                    pod["cpu_millicores"] = min(800, int(pod["cpu_millicores"] * 2.5))
                elif chaos_type == "pod_kill":
                    pod["status"] = "CrashLoopBackOff"
                    pod["restarts"] += 1

        chaos_spec = {
            "id": chaos_id,
            "type": chaos_type,
            "target_service": target_service,
            "duration_seconds": duration_seconds,
            "latency_ms": latency_ms if chaos_type == "latency" else 0.0,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "affected_pods": affected_pods,
            "description": self._get_description(chaos_type, target_service, latency_ms)
        }

        self.state.active_chaos = chaos_spec
        logger.warning("Injected Chaos Experiment: %s into %s", chaos_type, target_service)
        return chaos_spec

    def stop_chaos(self) -> Dict[str, Any]:
        """Terminates any active chaos experiment and restores nominal pod states."""
        if not self.state.active_chaos:
            return {"status": "NO_ACTIVE_CHAOS"}

        target_service = self.state.active_chaos.get("target_service")
        # Restore pod states
        for pod in self.state.pods:
            if pod["service"] == target_service:
                pod["status"] = "Running"
                pod["memory_mib"] = int(pod["memory_limit_mib"] * 0.45)
                pod["cpu_millicores"] = max(90, int(pod["cpu_millicores"] * 0.5))

        stopped_chaos = self.state.active_chaos
        self.state.active_chaos = None

        return {
            "status": "STOPPED",
            "experiment": stopped_chaos,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    def _get_description(self, chaos_type: str, target: str, latency_ms: float) -> str:
        if chaos_type == "error_spike":
            return f"Surging HTTP 500 Internal Server Errors in {target} (Simulates unhandled exception in canary release)."
        elif chaos_type == "latency":
            return f"Injecting +{latency_ms:.0f}ms synthetic network packet latency in {target} (Simulates database lock contention)."
        elif chaos_type == "oom_kill":
            return f"Triggering runaway heap memory leak causing kernel cgroup OOMKilled pod crashes on {target}."
        elif chaos_type == "pod_kill":
            return f"Forcefully evicting active replicas of {target} (Simulates node spot-instance termination)."
        return f"Active chaos experiment on {target}."
