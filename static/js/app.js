/**
 * KubePulse SRE Platform Core Frontend Engine
 * Real-time Telemetry Poller, Toast Dispatcher, and Automated Healer Trigger.
 */

// Toast Dispatcher
function showToast(message, type = "info") {
    const container = document.getElementById("toast-container");
    if (!container) return;

    const toast = document.createElement("div");
    toast.className = `sre-toast ${type}`;

    let iconClass = "bi-info-circle-fill text-cyan";
    if (type === "success") iconClass = "bi-check-circle-fill text-emerald";
    if (type === "warning") iconClass = "bi-exclamation-triangle-fill text-amber";
    if (type === "error") iconClass = "bi-x-octagon-fill text-crimson";

    toast.innerHTML = `
        <i class="bi ${iconClass}"></i>
        <span>${message}</span>
    `;

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = "0";
        toast.style.transform = "translateX(100%)";
        toast.style.transition = "all 0.3s ease";
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

// Global Automated Self-Healing Trigger
function executeQuickHeal() {
    showToast("Analyzing cluster failure vectors & initiating self-healing...", "info");
    
    fetch("/api/heal", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "AUTO" })
    })
    .then(res => res.json())
    .then(data => {
        showToast("Self-Healing Executed: " + data.summary, "success");
        setTimeout(() => {
            window.location.reload();
        }, 1200);
    })
    .catch(err => {
        showToast("Remediation failed: " + err, "error");
    });
}

// Single Incident Remediation with Live Step Console
function executeRemediation(incidentId, actionType) {
    const consoleBox = document.getElementById(`console-${incidentId}`);
    const consoleBody = document.getElementById(`console-body-${incidentId}`);
    
    if (consoleBox && consoleBody) {
        consoleBox.classList.remove("hidden");
        consoleBody.innerHTML = `<div class="mono-text text-cyan">[INIT] SRE Autonomous Agent acquiring deployment locks...</div>`;
    }

    showToast(`Executing ${actionType} on incident ${incidentId}...`, "warning");

    fetch("/api/heal", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ incident_id: incidentId, action: actionType })
    })
    .then(res => res.json())
    .then(data => {
        if (consoleBody && data.steps) {
            let output = "";
            data.steps.forEach(step => {
                output += `<div class="mono-text">${step}</div>`;
            });
            output += `<div class="mono-text text-emerald mt-1">[RESOLVED] Health checks verified in ${data.duration_ms}ms. Incident closed.</div>`;
            consoleBody.innerHTML = output;
        }

        showToast("Remediation complete: " + data.summary, "success");
        setTimeout(() => {
            window.location.reload();
        }, 1500);
    })
    .catch(err => {
        showToast("Remediation error: " + err, "error");
    });
}

// Real-Time Telemetry Polling (every 3 seconds)
function pollTelemetry() {
    fetch("/api/telemetry")
        .then(res => res.json())
        .then(data => {
            if (!data || data.status !== "success") return;

            const slo = data.slo;
            const overview = data.overview;
            const percentiles = data.percentiles;

            // Update Topbar
            const topbarBurn = document.getElementById("topbar-burnrate-val");
            if (topbarBurn) topbarBurn.textContent = slo.burn_rate_1h + "x";

            const topbarP99 = document.getElementById("topbar-p99-val");
            if (topbarP99) topbarP99.textContent = Math.round(slo.current_p99_ms) + "ms";

            const clusterModeText = document.getElementById("cluster-mode-text");
            if (clusterModeText) clusterModeText.textContent = overview.mode;

            const sidebarBudget = document.getElementById("sidebar-budget-pct");
            if (sidebarBudget) sidebarBudget.textContent = slo.remaining_budget_percent + "%";

            const incidentBadge = document.getElementById("sidebar-incident-badge");
            if (incidentBadge) {
                incidentBadge.textContent = data.active_incidents_count;
                incidentBadge.style.display = data.active_incidents_count > 0 ? "inline-block" : "none";
            }

            // Update Dashboard KPI cards if present
            const kpiHealth = document.getElementById("kpi-health-score");
            if (kpiHealth) kpiHealth.textContent = overview.cluster_health_score + "%";

            const kpiBudget = document.getElementById("kpi-budget-remaining");
            if (kpiBudget) kpiBudget.textContent = slo.remaining_budget_percent + "%";

            const kpiBurn1h = document.getElementById("kpi-burn-rate-1h");
            if (kpiBurn1h) kpiBurn1h.textContent = slo.burn_rate_1h + "x";

            const kpiP99 = document.getElementById("kpi-p99-latency");
            if (kpiP99) kpiP99.textContent = Math.round(slo.current_p99_ms) + " ms";

            // Push to burn rate chart if defined
            if (typeof updateBurnRateChart === "function") {
                updateBurnRateChart(slo.burn_rate_1h);
            }
        })
        .catch(err => {
            // Background polling silent catch
        });
}

document.addEventListener("DOMContentLoaded", () => {
    // Run initial poll and schedule interval
    pollTelemetry();
    setInterval(pollTelemetry, 3000);
});
