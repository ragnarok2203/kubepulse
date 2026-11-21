/**
 * KubePulse Cluster Topology Mesh Visualizer
 * Interactive HTML5 Canvas rendering nodes, microservice pods, and animated telemetry packet flows.
 */

let topoCanvas = null;
let topoCtx = null;
let animationFrameId = null;

// Topology elements
let topoNodes = [];
let topoPods = [];
let packets = [];

function initTopologyMesh(canvasId) {
    topoCanvas = document.getElementById(canvasId);
    if (!topoCanvas) return;
    topoCtx = topoCanvas.getContext("2d");

    setupTopologyData();
    animateTopology();
}

function setupTopologyData() {
    const width = topoCanvas.width;
    const height = topoCanvas.height;

    // 3 Worker Nodes positioned horizontally
    topoNodes = [
        { name: "worker-node-01", x: width * 0.20, y: height * 0.55, w: 220, h: 180, zone: "us-east-1a" },
        { name: "worker-node-02", x: width * 0.50, y: height * 0.55, w: 220, h: 180, zone: "us-east-1b" },
        { name: "worker-node-03", x: width * 0.80, y: height * 0.55, w: 220, h: 180, zone: "us-east-1c" },
    ];

    // Ingress Controller at Top Center
    const ingressX = width * 0.50;
    const ingressY = 70;

    // Pods distributed across the 3 nodes
    topoPods = [
        // Node 1
        { name: "ingress-gw-1", svc: "ingress-gateway", x: topoNodes[0].x - 55, y: topoNodes[0].y - 35, status: "Running", node: 0 },
        { name: "auth-svc-1", svc: "auth-service", x: topoNodes[0].x + 55, y: topoNodes[0].y - 35, status: "Running", node: 0 },
        { name: "order-svc-1", svc: "order-service", x: topoNodes[0].x - 55, y: topoNodes[0].y + 40, status: "Running", node: 0 },
        { name: "db-proxy-1", svc: "database-proxy", x: topoNodes[0].x + 55, y: topoNodes[0].y + 40, status: "Running", node: 0 },

        // Node 2
        { name: "ingress-gw-2", svc: "ingress-gateway", x: topoNodes[1].x - 55, y: topoNodes[1].y - 35, status: "Running", node: 1 },
        { name: "order-svc-2", svc: "order-service", x: topoNodes[1].x + 55, y: topoNodes[1].y - 35, status: "Running", node: 1 },
        { name: "payment-gw-1", svc: "payment-gateway", x: topoNodes[1].x - 55, y: topoNodes[1].y + 40, status: "Running", node: 1 },
        { name: "db-proxy-2", svc: "database-proxy", x: topoNodes[1].x + 55, y: topoNodes[1].y + 40, status: "Running", node: 1 },

        // Node 3
        { name: "auth-svc-2", svc: "auth-service", x: topoNodes[2].x - 55, y: topoNodes[2].y - 35, status: "Running", node: 2 },
        { name: "order-svc-3", svc: "order-service", x: topoNodes[2].x + 55, y: topoNodes[2].y - 35, status: "Running", node: 2 },
        { name: "payment-gw-2", svc: "payment-gateway", x: topoNodes[2].x - 55, y: topoNodes[2].y + 40, status: "Running", node: 2 },
        { name: "db-proxy-3", svc: "database-proxy", x: topoNodes[2].x + 55, y: topoNodes[2].y + 40, status: "Running", node: 2 }
    ];

    // Seed traffic packets
    packets = [];
    for (let i = 0; i < 18; i++) {
        spawnPacket(ingressX, ingressY);
    }
}

function spawnPacket(ingressX, ingressY) {
    const targetPod = topoPods[Math.floor(Math.random() * topoPods.length)];
    packets.push({
        x: ingressX,
        y: ingressY,
        targetX: targetPod.x,
        targetY: targetPod.y,
        progress: Math.random(),
        speed: 0.008 + Math.random() * 0.012
    });
}

function animateTopology() {
    if (!topoCtx || !topoCanvas) return;
    const ctx = topoCtx;
    const width = topoCanvas.width;
    const height = topoCanvas.height;

    ctx.clearRect(0, 0, width, height);

    const ingressX = width * 0.50;
    const ingressY = 60;

    // Draw mesh connection lines from Ingress to Node centers
    ctx.lineWidth = 1;
    topoNodes.forEach(node => {
        ctx.beginPath();
        ctx.strokeStyle = "rgba(6, 182, 212, 0.2)";
        ctx.moveTo(ingressX, ingressY + 15);
        ctx.lineTo(node.x, node.y - node.h / 2);
        ctx.stroke();
    });

    // Draw Ingress Gateway Controller
    ctx.fillStyle = "rgba(16, 22, 34, 0.9)";
    ctx.strokeStyle = "#06b6d4";
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.roundRect(ingressX - 90, ingressY - 20, 180, 40, 8);
    ctx.fill();
    ctx.stroke();

    ctx.fillStyle = "#ffffff";
    ctx.font = "bold 12px Inter, sans-serif";
    ctx.textAlign = "center";
    ctx.fillText("Ingress Controller", ingressX, ingressY + 5);

    // Draw Worker Nodes (Bounding boxes)
    topoNodes.forEach(node => {
        ctx.fillStyle = "rgba(16, 22, 34, 0.65)";
        ctx.strokeStyle = "rgba(255, 255, 255, 0.1)";
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        ctx.roundRect(node.x - node.w / 2, node.y - node.h / 2, node.w, node.h, 12);
        ctx.fill();
        ctx.stroke();

        // Node label
        ctx.fillStyle = "#94a3b8";
        ctx.font = "bold 11px JetBrains Mono, monospace";
        ctx.textAlign = "center";
        ctx.fillText(node.name, node.x, node.y - node.h / 2 + 18);
        ctx.fillStyle = "#64748b";
        ctx.font = "10px Inter, sans-serif";
        ctx.fillText(node.zone, node.x, node.y - node.h / 2 + 30);
    });

    // Draw Pods inside nodes
    topoPods.forEach(pod => {
        ctx.fillStyle = "rgba(22, 30, 46, 0.95)";
        ctx.strokeStyle = (pod.status === "Running") ? "#10b981" : "#ef4444";
        ctx.lineWidth = 1.5;

        ctx.beginPath();
        ctx.roundRect(pod.x - 42, pod.y - 18, 84, 36, 6);
        ctx.fill();
        ctx.stroke();

        // Pod Status Indicator Dot
        ctx.beginPath();
        ctx.arc(pod.x - 30, pod.y, 4, 0, Math.PI * 2);
        ctx.fillStyle = (pod.status === "Running") ? "#10b981" : "#ef4444";
        ctx.fill();

        // Pod Short Title
        ctx.fillStyle = "#ffffff";
        ctx.font = "10px Inter, sans-serif";
        ctx.textAlign = "center";
        ctx.fillText(pod.svc.split("-")[0], pod.x + 8, pod.y + 3);
    });

    // Animate moving data packets
    packets.forEach((p, index) => {
        p.progress += p.speed;
        if (p.progress >= 1.0) {
            p.progress = 0.0;
            const targetPod = topoPods[Math.floor(Math.random() * topoPods.length)];
            p.targetX = targetPod.x;
            p.targetY = targetPod.y;
        }

        const currX = ingressX + (p.targetX - ingressX) * p.progress;
        const currY = (ingressY + 15) + (p.targetY - (ingressY + 15)) * p.progress;

        ctx.beginPath();
        ctx.arc(currX, currY, 3, 0, Math.PI * 2);
        ctx.fillStyle = "#06b6d4";
        ctx.shadowColor = "#06b6d4";
        ctx.shadowBlur = 6;
        ctx.fill();
        ctx.shadowBlur = 0;
    });

    animationFrameId = requestAnimationFrame(animateTopology);
}

function resetTopologyZoom() {
    setupTopologyData();
}
