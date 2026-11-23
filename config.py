"""
KubePulse SRE Platform Configuration
Autonomous Kubernetes Observability, Error Budget Tracker & Self-Healing Engine.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

class Config:
    """Application configuration parameters."""
    # Cryptographic Session & Telemetry Signing
    _env_secret = os.environ.get("SECRET_KEY")
    if _env_secret:
        SECRET_KEY = _env_secret
    elif os.environ.get("FLASK_ENV") == "production":
        import secrets
        SECRET_KEY = secrets.token_hex(32)
    else:
        SECRET_KEY = "kubepulse-sre-telemetry-secret-key-2026"

    # Session & Cookie Security
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.environ.get("FLASK_ENV") == "production" or os.environ.get("SESSION_COOKIE_SECURE", "False").lower() in ("true", "1")
    PORT = int(os.environ.get("KUBEPULSE_PORT", os.environ.get("PORT", 5050)))
    HOST = os.environ.get("KUBEPULSE_HOST", "0.0.0.0")
    DEBUG = os.environ.get("FLASK_DEBUG", "True").lower() in ("true", "1", "yes")

    # Cluster Operation Mode: 'auto', 'simulation', or 'live'
    # 'auto': attempts to connect to live cluster; falls back to high-fidelity simulation if unreachable
    CLUSTER_MODE = os.environ.get("KUBEPULSE_MODE", "auto").lower()
    KUBECONFIG_PATH = os.environ.get("KUBECONFIG", str(Path.home() / ".kube" / "config"))
    IN_CLUSTER = os.environ.get("KUBERNETES_SERVICE_HOST") is not None

    # Google SRE SLO / SLI Defaults (Rolling 30-day window)
    SLO_AVAILABILITY_TARGET = float(os.environ.get("SLO_AVAILABILITY_TARGET", 99.9))  # 99.9%
    SLO_LATENCY_P99_TARGET_MS = float(os.environ.get("SLO_LATENCY_P99_TARGET_MS", 250.0))  # 250 ms
    ROLLING_WINDOW_DAYS = 30

    # Multi-Window Multi-Burn-Rate Alert Thresholds (Google SRE Book Ch. 5)
    # Burn Rate 14.4: 2% of budget burned in 1 hour -> Page On-Call immediately
    BURN_RATE_CRITICAL_1H = 14.4
    # Burn Rate 6.0: 5% of budget burned in 6 hours -> Ticket/Warning
    BURN_RATE_WARN_6H = 6.0

    # OpenTelemetry Tracing simulation defaults
    TRACE_RETENTION_MAX = 50
    INCIDENT_RETENTION_MAX = 100

    # Simulated Services
    SIMULATED_SERVICES = [
        "ingress-gateway",
        "auth-service",
        "order-service",
        "payment-gateway",
        "database-proxy",
    ]

    # Namespaces monitored
    NAMESPACES = ["default", "production", "kube-system"]
