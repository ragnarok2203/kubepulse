# ⚡ KubePulse SRE

### Autonomous Kubernetes Observability, Google SRE Error Budget Tracker & Self-Healing Engine
> **Target Audience:** B.Tech CSE (Cloud Computing & DevOps Specialization) — Major Capstone Project & SRE/Cloud Placement Showcase.

---

## 🌟 Executive Overview
Modern cloud-native architectures running on Kubernetes face severe challenges around **alert fatigue**, **unpredictable cascading failures**, and **delayed manual incident triage**. Traditional monitoring tools trigger alerts on arbitrary, noisy thresholds (e.g. CPU > 80%), causing engineers to wake up for non-critical incidents while missing systemic tail-latency degradation.

**KubePulse SRE** is an enterprise-grade Site Reliability Engineering platform engineered around the **Google SRE Multi-Window Multi-Burn-Rate alerting framework** (Google SRE Workbook, Ch. 5). It provides real-time visibility into Kubernetes worker nodes, OpenTelemetry distributed traces, and executes **autonomous self-healing remediations** (Canary Rollbacks, Pod Evictions, Memory Limit Tuning, and Horizontal Autoscaling) within milliseconds of an SLO breach.

---

## 🏗️ System Architecture

```
                                  [ User Traffic ]
                                         │
                                         ▼
                            ┌────────────────────────┐
                            │ Ingress Gateway (v2.4) │
                            └────────────┬───────────┘
                                         │
                        ┌────────────────┴────────────────┐
                        ▼                                 ▼
             ┌─────────────────────┐           ┌─────────────────────┐
             │ Auth Service (v1.8) │           │ Order Service (v3.1)│
             └──────────┬──────────┘           └──────────┬──────────┘
                        │                                 │
                        ▼                                 ▼
             ┌─────────────────────┐           ┌─────────────────────┐
             │  Payment Gateway    │           │ Database Proxy (SQL)│
             └─────────────────────┘           └─────────────────────┘
                                         │
                                         ▼
                       ═════════════════════════════
                         KubePulse SRE Telemetry
                       ═════════════════════════════
                                         │
            ┌────────────────────────────┼────────────────────────────┐
            ▼                            ▼                            ▼
  ┌──────────────────┐         ┌──────────────────┐         ┌──────────────────┐
  │ Google SRE Engine│         │ OpenTelemetry    │         │ Autonomous       │
  │ Multi-Burn-Rate  │         │ Distributed      │         │ Self-Healing     │
  │ Error Budget     │         │ Tracing (P50-P99)│         │ Remediator       │
  └──────────────────┘         └──────────────────┘         └──────────────────┘
```

### Dual-Engine Operation
- **Live Cluster Mode:** Connects to any live Kubernetes cluster (Minikube, Kind, k3s, EKS, GKE, AKS) via the official Kubernetes Python API (`CoreV1Api`, `AppsV1Api`).
- **Autonomous Simulation Mode:** If no cluster is active, KubePulse seamlessly runs an autonomous high-fidelity simulation with 3 multi-zone worker nodes, 12 microservice pods, and dynamic traffic generators. **Demos never fail during viva or campus interviews.**

---

## 📐 Mathematical Framework (Google SRE Multi-Burn-Rate)

### 1. Service Level Indicators (SLI) & Objectives (SLO)
$$\text{Availability SLI} = \frac{\text{Successful Requests (HTTP } < 500\text{)}}{\text{Total Valid Requests}} \ge 99.90\%$$

$$\text{Error Budget} = 1.0 - 0.999 = 0.001 = 0.10\% \text{ (1 failure per 1,000 requests)}$$

### 2. Multi-Window Multi-Burn-Rate Alerting
A burn rate of **1.0x** consumes exactly 100% of the 30-day budget across 720 hours. When outages occur, fast detection is mandatory:

| Alert Tier | Detection Window | Burn Rate Threshold | 30-Day Budget Consumed | SRE Escalation Action |
| :--- | :---: | :---: | :---: | :--- |
| **P1 Pager** | **1 Hour** | **$\ge 14.4\text{x}$** | **$2.0\%$ in 1 hour** | Immediate On-Call Escalation |
| **P2 Ticket** | **6 Hours** | **$\ge 6.0\text{x}$** | **$5.0\%$ in 6 hours** | High-Priority JIRA Ticket |
| **P3 Triage** | **3 Days** | **$\ge 1.0\text{x}$** | **$10.0\%$ in 3 days** | Weekly Reliability Review |

$$\text{Burn Rate} = \frac{\text{Observed Error Rate}}{\text{Allowed Unreliability}} = \frac{\text{Errors} / \text{Total}}{0.001}$$

---

## 🔬 Core Capabilities

### 1. Mission Control Dashboard
- Real-time **Cluster Health Score** computed from Ready node and Running pod ratios.
- **30-Day Error Budget Burndown Meter** with real-time time-to-exhaustion projection.
- Live canvas sparkline tracking **1-hour fast-burn pulse** with visual threshold alert boundaries.
- OpenTelemetry latency percentiles: **P50 (Median)**, **P90**, **P95**, and **P99 (Tail SLA < 250ms)**.

### 2. Interactive Topology Mesh
- HTML5 Canvas interactive rendering of Kubernetes Worker Nodes across Availability Zones (`us-east-1a`, `us-east-1b`, `us-east-1c`).
- Microservice pod inventory tracking CPU millicores, cgroup memory utilization vs limits, and restart counters.
- Visual packet streams showing distributed network traversal from Ingress Gateway to Database Proxy.

### 3. OpenTelemetry Distributed Tracing (W3C TraceContext)
- Hierarchical span trees:
  $$\text{ingress-gateway} \longrightarrow \text{auth-service} \longrightarrow \text{order-service} \longrightarrow \text{payment-gateway} \longrightarrow \text{database-proxy}$$
- Waterfall Gantt chart highlighting the **critical-path bottleneck service** and latency contributions.

### 4. Chaos Engineering Control Plane
Empirically validate SRE alerts and self-healing with 4 synthetic failure modes:
1. **HTTP 500 Error Surge:** Simulates buggy canary release; drives burn rate $>14.4\text{x}$.
2. **Tail Latency Delay:** Injects $+450\text{ms}$ network transit latency; triggers P99 SLA breach.
3. **cgroup OOMKilled Leak:** Forces container memory beyond limit; triggers Linux kernel eviction.
4. **Pod Eviction / Chaos Monkey:** Simulates spot-instance termination to benchmark ReplicaSet failover.

### 5. Autonomous Self-Healing Engine
- **Canary Rollback:** Automatically triggers `kubectl rollout undo deployment/<service>`.
- **Pod Eviction & Recreation:** Flushes memory caches and restarts stuck pods.
- **Memory Limit Tuning:** Expands cgroup memory limit by $+50\%$ upon OOM breaches.
- **HPA Scale-Out:** Adds worker replicas during traffic surges to flatten tail latencies.

---

## 🚀 Quickstart Guide

### 1. Local Python Setup
```bash
# Clone and enter directory
cd D:\kubepulse

# Install dependencies
pip install -r requirements.txt

# Run automated verification tests (21 tests)
python -m pytest tests/ -v

# Launch the SRE Command Center
python run.py
```
Open **`http://127.0.0.1:5050`** in your browser.

### 2. Docker Setup
```bash
# Build multi-stage container
docker build -t kubepulse:v1.0.0 .

# Run with Docker Compose
docker-compose up -d
```

### 3. Kubernetes Cluster Deployment
```bash
# Apply namespace, RBAC permissions, deployment, and service
kubectl apply -f kubernetes/namespace.yaml
kubectl apply -f kubernetes/clusterrole.yaml
kubectl apply -f kubernetes/deployment.yaml
kubectl apply -f kubernetes/service.yaml
kubectl apply -f kubernetes/ingress.yaml
```

---

## 📂 Project Structure
```
D:\kubepulse\
├── config.py                 # Configuration parameters & SLO thresholds
├── run.py                    # Server launcher with ASCII SRE banner
├── app.py                    # Flask application factory, REST APIs & UI routes
├── services/
│   ├── slo_engine.py         # Google SRE multi-window burn rate mathematical engine
│   ├── otel_tracer.py        # OpenTelemetry distributed trace synthesizer & span analyzer
│   ├── cluster_state.py      # Dual-engine state manager (Live K8s API + Simulation)
│   ├── k8s_client.py         # Kubernetes Python API client (CoreV1Api, AppsV1Api)
│   ├── auto_healer.py        # Automated SRE remediation workflows (Rollback, Restart, HPA)
│   └── chaos_engine.py       # Chaos engineering experiment runner (500 spike, latency, OOM)
├── templates/
│   ├── base.html             # Cyber-SRE master shell with live pulse & cluster indicator
│   ├── dashboard.html        # SRE Mission Control Center
│   ├── topology.html         # Interactive canvas cluster mesh
│   ├── slo.html              # Google SRE Error Budget calculator & alerting rules
│   ├── traces.html           # OpenTelemetry distributed waterfall trace viewer
│   ├── incidents.html        # Incidents log, AI Root Cause Analysis (RCA) & 1-click self-healing
│   └── chaos.html            # Chaos experiment control plane
├── static/
│   ├── css/style.css         # Glassmorphic dark theme with glowing neon accents
│   └── js/
│       ├── app.js            # Real-time telemetry polling & auto-remediator
│       ├── topology.js       # HTML5 canvas mesh renderer with particle flow
│       └── charts.js         # Real-time canvas burn rate sparkline
├── kubernetes/               # Production Kubernetes manifests
├── .github/workflows/        # Automated CI/CD pipeline (lint, test, build)
└── tests/                    # 21 automated unit & integration tests
```

---

## 🎓 Campus Viva & Placement Interview Cheat Sheet

### Q1: Why use Error Budget Burn Rates instead of static CPU/Memory alerts?
> **Answer:** Static thresholds (e.g. CPU > 80%) generate massive alert fatigue because high CPU utilization is often desirable under healthy load. Google SRE Error Budgets directly correlate alerting with **user pain**. If users aren't experiencing HTTP 5xx errors or tail-latency breaches, no alert should fire. Multi-window burn rates prevent false alarms by requiring both short-window (fast burn) and medium-window (sustained burn) confirmation.

### Q2: What is the significance of Burn Rate = 14.4 in a 1-hour window?
> **Answer:** A 30-day window has $30 \times 24 = 720\text{ hours}$. If an outage consumes $2\%$ of the total error budget in 1 hour:
> $$\text{Burn Rate} = \frac{2\%}{1\text{ hr}} \times \frac{720\text{ hrs}}{100\%} = 0.02 \times 720 = 14.4$$
> A burn rate $\ge 14.4$ indicates that the entire monthly error budget will be depleted in just 50 hours (2 days), requiring an immediate on-call pager.

### Q3: How does OpenTelemetry Distributed Tracing help identify microservice bottlenecks?
> **Answer:** Through W3C TraceContext headers (`traceparent`), each HTTP/gRPC request carries a unique `TraceID` and passing `SpanID`. KubePulse constructs the dependency tree and calculates the duration of every child span. The **critical-path bottleneck** is isolated by finding the span with the highest latency delta or a non-200 status code.

### Q4: What self-healing mechanisms does KubePulse implement for Kubernetes?
> **Answer:**
> 1. **Rollout Undo:** Automatically executes `kubectl rollout undo` when an error surge is detected following a deployment revision.
> 2. **Pod Eviction:** Deletes stuck pods so the Kubernetes ReplicaSet controller recreates clean instances.
> 3. **Memory Tuning:** Dynamically patches container cgroup memory limits by $+50\%$ upon detecting OOMKilled events.
> 4. **Horizontal Scaling:** Spawns additional replicas when P99 tail latency breaches the 250ms target.

---

## 📄 License
MIT License &mdash; Developed for Cloud Computing & DevOps SRE Capstone Portfolio.
