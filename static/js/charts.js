/**
 * KubePulse Real-Time Canvas Charts
 * Lightweight, zero-dependency canvas renderer for Error Budget Burn Rate pulse.
 */

let burnRateHistory = [0.28, 0.32, 0.25, 0.30, 0.29, 0.35, 0.28, 0.31, 0.27, 0.34, 0.28];
let chartCanvas = null;
let chartCtx = null;

function initBurnRateChart(canvasId) {
    chartCanvas = document.getElementById(canvasId);
    if (!chartCanvas) return;
    chartCtx = chartCanvas.getContext("2d");
    renderBurnRateChart();
}

function updateBurnRateChart(latestVal) {
    if (!chartCtx || !chartCanvas) return;
    burnRateHistory.push(latestVal);
    if (burnRateHistory.length > 25) {
        burnRateHistory.shift();
    }
    renderBurnRateChart();
}

function renderBurnRateChart() {
    if (!chartCtx || !chartCanvas) return;

    const ctx = chartCtx;
    const width = chartCanvas.width;
    const height = chartCanvas.height;

    ctx.clearRect(0, 0, width, height);

    // Padding
    const padX = 40;
    const padY = 25;
    const plotW = width - padX - 20;
    const plotH = height - padY * 2;

    // Scale calculation (Max at least 16 to fit 14.4x threshold)
    const maxVal = Math.max(16.0, Math.max(...burnRateHistory) * 1.15);
    const minVal = 0.0;

    // Draw grid lines
    ctx.strokeStyle = "rgba(255, 255, 255, 0.06)";
    ctx.lineWidth = 1;

    // Alert threshold lines: 14.4x (Pager - Red)
    const y14_4 = padY + plotH - ((14.4 - minVal) / (maxVal - minVal)) * plotH;
    ctx.beginPath();
    ctx.strokeStyle = "rgba(239, 68, 68, 0.4)";
    ctx.setLineDash([4, 4]);
    ctx.moveTo(padX, y14_4);
    ctx.lineTo(padX + plotW, y14_4);
    ctx.stroke();

    ctx.fillStyle = "#f87171";
    ctx.font = "9px JetBrains Mono, monospace";
    ctx.fillText("14.4x PAGER", 2, y14_4 + 3);

    // Alert threshold line: 6.0x (Warn - Amber)
    const y6_0 = padY + plotH - ((6.0 - minVal) / (maxVal - minVal)) * plotH;
    ctx.beginPath();
    ctx.strokeStyle = "rgba(245, 158, 11, 0.4)";
    ctx.setLineDash([4, 4]);
    ctx.moveTo(padX, y6_0);
    ctx.lineTo(padX + plotW, y6_0);
    ctx.stroke();

    ctx.fillStyle = "#fbbf24";
    ctx.fillText("6.0x WARN", 5, y6_0 + 3);

    // Baseline: 1.0x (Cyan)
    const y1_0 = padY + plotH - ((1.0 - minVal) / (maxVal - minVal)) * plotH;
    ctx.beginPath();
    ctx.strokeStyle = "rgba(6, 182, 212, 0.25)";
    ctx.setLineDash([2, 4]);
    ctx.moveTo(padX, y1_0);
    ctx.lineTo(padX + plotW, y1_0);
    ctx.stroke();
    ctx.setLineDash([]); // Reset dash

    // Plot data points
    if (burnRateHistory.length < 2) return;

    const stepX = plotW / (burnRateHistory.length - 1);
    const points = burnRateHistory.map((val, idx) => {
        const x = padX + idx * stepX;
        const y = padY + plotH - ((val - minVal) / (maxVal - minVal)) * plotH;
        return { x, y, val };
    });

    // Create Gradient Fill
    const latestVal = burnRateHistory[burnRateHistory.length - 1];
    let strokeColor = "#06b6d4";
    let glowColor = "rgba(6, 182, 212, 0.4)";
    if (latestVal >= 14.4) {
        strokeColor = "#ef4444";
        glowColor = "rgba(239, 68, 68, 0.5)";
    } else if (latestVal >= 6.0) {
        strokeColor = "#f59e0b";
        glowColor = "rgba(245, 158, 11, 0.5)";
    }

    const grad = ctx.createLinearGradient(0, padY, 0, padY + plotH);
    grad.addColorStop(0, glowColor);
    grad.addColorStop(1, "rgba(0, 0, 0, 0)");

    // Fill curve area
    ctx.beginPath();
    ctx.moveTo(points[0].x, padY + plotH);
    points.forEach(p => ctx.lineTo(p.x, p.y));
    ctx.lineTo(points[points.length - 1].x, padY + plotH);
    ctx.closePath();
    ctx.fillStyle = grad;
    ctx.fill();

    // Draw curve line
    ctx.beginPath();
    ctx.strokeStyle = strokeColor;
    ctx.lineWidth = 2.5;
    ctx.shadowColor = strokeColor;
    ctx.shadowBlur = 8;
    points.forEach((p, i) => {
        if (i === 0) ctx.moveTo(p.x, p.y);
        else ctx.lineTo(p.x, p.y);
    });
    ctx.stroke();
    ctx.shadowBlur = 0; // Reset shadow

    // Pulse dot on current head
    const lastP = points[points.length - 1];
    ctx.beginPath();
    ctx.arc(lastP.x, lastP.y, 4, 0, Math.PI * 2);
    ctx.fillStyle = "#ffffff";
    ctx.fill();
    ctx.beginPath();
    ctx.arc(lastP.x, lastP.y, 7, 0, Math.PI * 2);
    ctx.strokeStyle = strokeColor;
    ctx.lineWidth = 2;
    ctx.stroke();
}
