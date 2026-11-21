"""
KubePulse SRE Platform - Main Application Entrypoint
Autonomous Kubernetes Observability, Error Budget Tracker & Self-Healing Engine.
"""

import os
import json
import logging
from pathlib import Path
from flask import Flask, render_template, request, jsonify, redirect, url_for

from config import Config
from services.cluster_state import ClusterStateManager
from services.auto_healer import AutoHealer
from services.chaos_engine import ChaosEngine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s]: %(message)s"
)
logger = logging.getLogger("kubepulse.app")

BASE_DIR = Path(__file__).resolve().parent

def create_app(config_class=Config) -> Flask:
    """Application factory for KubePulse SRE."""
    app = Flask(
        __name__,
        template_folder=str(BASE_DIR / "templates"),
        static_folder=str(BASE_DIR / "static")
    )
    app.config.from_object(config_class)

    # Initialize Core Engines
    cluster_state = ClusterStateManager(
        mode=app.config["CLUSTER_MODE"],
        kubeconfig_path=app.config["KUBECONFIG_PATH"]
    )
    auto_healer = AutoHealer(cluster_state)
    chaos_engine = ChaosEngine(cluster_state)

    # Attach instances to app context
    app.cluster_state = cluster_state
    app.auto_healer = auto_healer
    app.chaos_engine = chaos_engine

    # -------------------------------------------------------------
    # WEB UI PAGES
    # -------------------------------------------------------------

    @app.route("/")
    @app.route("/dashboard")
    def dashboard():
        """Main SRE Mission Control Center."""
        telemetry = cluster_state.tick_telemetry()
        overview = cluster_state.get_cluster_overview()
        traces = cluster_state.tracer.get_recent_traces(limit=8)
        return render_template(
            "dashboard.html",
            page="dashboard",
            telemetry=telemetry,
            overview=overview,
            traces=traces,
            incidents=cluster_state.incidents[:5]
        )

    @app.route("/topology")
    def topology():
        """Interactive visual topology map of nodes, pods, and services."""
        overview = cluster_state.get_cluster_overview()
        return render_template(
            "topology.html",
            page="topology",
            overview=overview,
            nodes=cluster_state.nodes,
            pods=cluster_state.pods
        )

    @app.route("/slo")
    def slo():
        """Deep dive Google SRE Error Budget Burndown and Multi-Window Burn Rates."""
        telemetry = cluster_state.tick_telemetry()
        return render_template(
            "slo.html",
            page="slo",
            slo=telemetry["slo"],
            config=app.config
        )

    @app.route("/traces")
    def traces():
        """OpenTelemetry Distributed Waterfall Trace Viewer."""
        trace_list = cluster_state.tracer.get_recent_traces(limit=25)
        percentiles = cluster_state.tracer.get_percentiles()
        selected_trace_id = request.args.get("id")
        selected_trace = None
        if selected_trace_id:
            selected_trace = cluster_state.tracer.get_trace_by_id(selected_trace_id)
        if not selected_trace and trace_list:
            selected_trace = trace_list[0]

        return render_template(
            "traces.html",
            page="traces",
            traces=trace_list,
            selected_trace=selected_trace,
            percentiles=percentiles
        )

    @app.route("/incidents")
    def incidents():
        """SRE Incident Timeline, AI Root Cause Analysis & Self-Healing."""
        return render_template(
            "incidents.html",
            page="incidents",
            incidents=cluster_state.incidents,
            active_count=sum(1 for i in cluster_state.incidents if i["status"] == "ACTIVE")
        )

    @app.route("/chaos")
    def chaos():
        """Chaos Engineering Control Plane."""
        overview = cluster_state.get_cluster_overview()
        return render_template(
            "chaos.html",
            page="chaos",
            overview=overview,
            active_chaos=cluster_state.active_chaos,
            services=app.config["SIMULATED_SERVICES"]
        )

    # -------------------------------------------------------------
    # REST API & TELEMETRY STREAM
    # -------------------------------------------------------------

    @app.route("/api/telemetry")
    def api_telemetry():
        """Real-time cluster telemetry feed."""
        data = cluster_state.tick_telemetry()
        overview = cluster_state.get_cluster_overview()
        return jsonify({
            "status": "success",
            "overview": overview,
            "slo": data["slo"],
            "percentiles": data["percentiles"],
            "active_chaos": data["active_chaos"],
            "active_incidents_count": data["active_incidents_count"],
            "latest_trace": data["latest_trace"]
        })

    @app.route("/api/cluster")
    def api_cluster():
        """Cluster overview and node states."""
        return jsonify(cluster_state.get_cluster_overview())

    @app.route("/api/traces")
    def api_traces():
        """Recent distributed traces."""
        limit = int(request.args.get("limit", 20))
        return jsonify({
            "percentiles": cluster_state.tracer.get_percentiles(),
            "traces": cluster_state.tracer.get_recent_traces(limit=limit)
        })

    @app.route("/api/traces/<trace_id>")
    def api_trace_detail(trace_id):
        """Single trace details."""
        trace = cluster_state.tracer.get_trace_by_id(trace_id)
        if not trace:
            return jsonify({"error": "Trace not found"}), 404
        return jsonify(trace)

    @app.route("/api/incidents")
    def api_incidents():
        """All recorded incidents."""
        return jsonify(cluster_state.incidents)

    @app.route("/api/heal", methods=["POST"])
    def api_heal():
        """Execute automated SRE self-healing remediation."""
        payload = request.get_json(silent=True) or {}
        incident_id = payload.get("incident_id")
        action = payload.get("action", "AUTO")

        # If no incident_id was provided, pick the first active incident
        if not incident_id:
            active_inc = next((i for i in cluster_state.incidents if i["status"] == "ACTIVE"), None)
            if active_inc:
                incident_id = active_inc["id"]

        result = auto_healer.execute_remediation(incident_id=incident_id, action_type=action)
        return jsonify(result)

    @app.route("/api/chaos/inject", methods=["POST"])
    def api_chaos_inject():
        """Inject synthetic chaos failure experiment."""
        payload = request.get_json(silent=True) or {}
        chaos_type = payload.get("type", "error_spike")
        target_service = payload.get("target_service", "order-service")
        duration = int(payload.get("duration", 120))
        latency_ms = float(payload.get("latency_ms", 450.0))

        result = chaos_engine.inject_chaos(
            chaos_type=chaos_type,
            target_service=target_service,
            duration_seconds=duration,
            latency_ms=latency_ms
        )
        return jsonify({"status": "success", "experiment": result})

    @app.route("/api/chaos/stop", methods=["POST"])
    def api_chaos_stop():
        """Terminate active chaos experiment."""
        result = chaos_engine.stop_chaos()
        return jsonify(result)

    # -------------------------------------------------------------
    # KUBERNETES PROBE CHECKS
    # -------------------------------------------------------------

    @app.route("/healthz")
    @app.route("/readyz")
    def health_probes():
        """Kubernetes liveness and readiness probe endpoint."""
        return jsonify({
            "status": "UP",
            "cluster_mode": cluster_state.mode,
            "connected_to_real_k8s": cluster_state.is_live_cluster_active(),
            "slo_healthy": cluster_state.cumulative_budget_consumed < 100.0
        }), 200

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)
