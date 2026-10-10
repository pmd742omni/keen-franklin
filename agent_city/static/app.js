/**
 * ============================================================================
 * SILICON FOREST — Living Voxel Sanctuary Logic & Telemetry Engine
 * Master-Grade Frontend Implementation built from First Principles
 * Compliant with @voxel-art, @anti-slop-design, and @design-spells:
 *
 * • Pure Zero-CDN WebSocket & Resilient REST Telemetry
 * • Dual Antialiased Rolling Sparklines (60fps Canvas)
 * • Direct Win32 Hardware Optimizations (psapi.dll & SSD TRIM defrag)
 * • Per-Process Working Set Compaction via TRIM_PID
 * • Interactive Terminal Console in Sanctuary Harmony Feed
 * • Time-of-Day Ambiance Switching (Dawn, Twilight, Midnight)
 * • Tactile Micro-Interactions & Spring-Loaded HUD Feedback
 * ============================================================================
 */

const state = {
  connected: false,
  telemetry: {
    cpu: { overall_pct: 14, cores: [12, 14, 18, 10], freq_mhz: 2900 },
    memory: { total_mb: 8000, used_mb: 3840, free_mb: 4160, used_pct: 48 },
    storage: { total_gb: 256, used_gb: 195, free_gb: 42.4, junk_mb: 4.7, used_pct: 76 },
    smoothness_index: 92,
    top_processes: [],
    optimizer_agents: [],
  },
  cpuHistory: new Array(30).fill(12),
  ramHistory: new Array(30).fill(1000),
  activeTab: "tabSwarm",
};

let ws = null;
const HALO_CIRCUMFERENCE = 351.85; // 2 * Math.PI * 56

// Top Floating Header Elements
const topCpuVal = document.getElementById("topCpuVal");
const topRamVal = document.getElementById("topRamVal");
const topSsdVal = document.getElementById("topSsdVal");
const topJunkVal = document.getElementById("topJunkVal");

const btnHeaderRam = document.getElementById("btnHeaderRam");
const btnHeaderStorage = document.getElementById("btnHeaderStorage");
const btnHeaderFull = document.getElementById("btnHeaderFull");

// Upper Grid Hero Elements
const haloProgressRing = document.getElementById("haloProgressRing");
const haloScore = document.getElementById("haloScore");
const heroStatusPill = document.getElementById("heroStatusPill");
const heroPulseDot = document.getElementById("heroPulseDot");
const heroStatusText = document.getElementById("heroStatusText");

const labelCpuFreq = document.getElementById("labelCpuFreq");
const coresDeckGrid = document.getElementById("coresDeckGrid");
const cpuSparklineCanvas = document.getElementById("cpuSparklineCanvas");

const labelRamPct = document.getElementById("labelRamPct");
const segActiveRam = document.getElementById("segActiveRam");
const segCompressedRam = document.getElementById("segCompressedRam");
const segFreeRam = document.getElementById("segFreeRam");
const lblUsedMb = document.getElementById("lblUsedMb");
const lblFreeMb = document.getElementById("lblFreeMb");
const ramSparklineCanvas = document.getElementById("ramSparklineCanvas");
const btnQuickFlushRam = document.getElementById("btnQuickFlushRam");

const labelDiskPct = document.getElementById("labelDiskPct");
const segDiskUsed = document.getElementById("segDiskUsed");
const segDiskFree = document.getElementById("segDiskFree");
const lblDiskUsedGb = document.getElementById("lblDiskUsedGb");
const lblDiskFreeGb = document.getElementById("lblDiskFreeGb");
const lblDiskJunkMb = document.getElementById("lblDiskJunkMb");
const btnQuickPurgeDisk = document.getElementById("btnQuickPurgeDisk");

// 3D Voxel Stage & Controls
const voxelCanvas = document.getElementById("voxelMotherboardCanvas");
let voxelEngine = null;

const btnCamIso = document.getElementById("btnCamIso");
const btnCamLow = document.getElementById("btnCamLow");
const btnCamTop = document.getElementById("btnCamTop");
const btnTogglePlantTags = document.getElementById("btnTogglePlantTags");
const btnTogglePackets = document.getElementById("btnTogglePackets");
const btnPcbZoomReset = document.getElementById("btnPcbZoomReset");

const pcbInspectorOverlay = document.getElementById("pcbInspectorOverlay");
const insHeading = document.getElementById("insHeading");
const insBody = document.getElementById("insBody");
const btnInsClose = document.getElementById("btnInsClose");

// Lower Deck Elements
const swarmAgentGrid = document.getElementById("swarmAgentGrid");
const processTableBody = document.getElementById("processTableBody");
const auditStreamFeed = document.getElementById("auditStreamFeed");
const btnTrimAllTable = document.getElementById("btnTrimAllTable");

const terminalCmdInput = document.getElementById("terminalCmdInput");
const btnTerminalSubmit = document.getElementById("btnTerminalSubmit");

// Floating HUD Toast
const studioHudToast = document.getElementById("studioHudToast");
const hudToastText = document.getElementById("hudToastText");

// =============================================================================
// 1. WEBSOCKET TELEMETRY STREAM WITH AUTO-RECONNECT
// =============================================================================
function initTelemetry() {
  if (window.location.search.includes("static=1") || window.location.search.includes("screenshot=1")) {
    fetchTelemetryRest();
    return;
  }
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const wsUrl = `${protocol}//${window.location.host}/ws`;

  ws = new WebSocket(wsUrl);

  ws.onopen = () => {
    state.connected = true;
    showToast("Sanctuary stream synchronized with Windows kernel.");
  };

  ws.onmessage = (event) => {
    try {
      const msg = JSON.parse(event.data);
      if (msg.hardware_telemetry) {
        updateHardwareTelemetry(msg.hardware_telemetry);
      }
      if (msg.events && msg.events.length > 0) {
        msg.events.forEach(e => appendAuditRow(e.title || "Sanctuary", e.description || e));
      }
    } catch (e) {
      console.warn("Telemetry frame parse error:", e);
    }
  };

  ws.onclose = () => {
    state.connected = false;
    setTimeout(initTelemetry, 3000);
  };

  ws.onerror = () => {
    fetchTelemetryRest();
  };
}

function fetchTelemetryRest() {
  fetch("/api/hardware")
    .then(r => {
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      return r.json();
    })
    .then(data => {
      if (data && data.cpu && data.memory) {
        updateHardwareTelemetry(data);
      }
    })
    .catch((err) => {
      console.debug("Telemetry polling wait:", err.message);
    });
}

// Background polling ensures real-time parity even if WebSockets are transient
setInterval(fetchTelemetryRest, 1600);

// =============================================================================
// 2. LIVE HARDWARE TELEMETRY & SPARKLINE RENDERERS
// =============================================================================
function updateHardwareTelemetry(hw) {
  if (!hw) return;
  state.telemetry = hw;

  const cpu = hw.cpu || { overall_pct: 0, cores: [0, 0, 0, 0], freq_mhz: 800 };
  const mem = hw.memory || { total_mb: 8000, used_mb: 4000, free_mb: 4000, used_pct: 50 };
  const storage = hw.storage || { total_gb: 256, used_gb: 200, free_gb: 56, junk_mb: 124.5, used_pct: 78 };
  const smoothness = (hw.smoothness_index !== undefined) ? hw.smoothness_index : 85;

  // 1. History Buffers for Rolling Sparklines
  const cpuLoad = Math.round(cpu.overall_pct || 0);
  const freeRam = Math.round(mem.free_mb || 0);

  state.cpuHistory.push(cpuLoad);
  state.cpuHistory.shift();

  state.ramHistory.push(freeRam);
  state.ramHistory.shift();

  // Draw Rolling Canvas Sparklines (High-Agency Antialiased Vector Spline)
  drawSparkline(cpuSparklineCanvas, state.cpuHistory, "#f472b6", 0, 100);
  drawSparkline(ramSparklineCanvas, state.ramHistory, "#10b981", 0, 4500);

  // 2. Circular Harmony Ring Gauge
  const score = Math.max(0, Math.min(100, smoothness));
  haloScore.textContent = score;

  const offset = HALO_CIRCUMFERENCE - (score / 100) * HALO_CIRCUMFERENCE;
  haloProgressRing.style.strokeDashoffset = offset;

  if (score >= 80) {
    haloProgressRing.style.stroke = "var(--forest-jade)";
    heroStatusText.textContent = "Flourishing Bloom";
    heroStatusPill.style.color = "var(--forest-jade)";
    heroStatusPill.style.borderColor = "var(--accent-border)";
    heroPulseDot.style.background = "var(--forest-jade)";
  } else if (score >= 60) {
    haloProgressRing.style.stroke = "var(--status-warning)";
    heroStatusText.textContent = "Tranquil Grove";
    heroStatusPill.style.color = "var(--status-warning)";
    heroStatusPill.style.borderColor = "rgba(245, 158, 11, 0.3)";
    heroPulseDot.style.background = "var(--status-warning)";
  } else {
    haloProgressRing.style.stroke = "var(--status-alert)";
    heroStatusText.textContent = "Strained Canopy";
    heroStatusPill.style.color = "var(--status-alert)";
    heroStatusPill.style.borderColor = "rgba(244, 63, 94, 0.3)";
    heroPulseDot.style.background = "var(--status-alert)";
  }

  // 3. Header Telemetry Pills
  topCpuVal.textContent = `${cpuLoad}%`;
  topRamVal.textContent = `${freeRam} MB`;
  topSsdVal.textContent = `${storage.free_gb || 0} GB`;
  topJunkVal.textContent = `${storage.junk_mb || 0} MB`;

  // 4. Sacred Core Canopy Grid
  labelCpuFreq.textContent = `${Math.round(cpu.freq_mhz || 800)} MHz`;
  renderCoresGrid(cpu.cores || [0, 0, 0, 0]);

  // 5. Memory Architecture Stack
  const usedRam = Math.round(mem.used_mb || 0);
  const ramPct = Math.round(mem.used_pct || 0);

  labelRamPct.textContent = `${ramPct}%`;
  lblUsedMb.textContent = `${usedRam} MB`;
  lblFreeMb.textContent = `${freeRam} MB`;

  const activePct = Math.max(10, ramPct - 15);
  const compPct = Math.min(25, Math.max(5, ramPct - activePct));
  const freePct = Math.max(5, 100 - activePct - compPct);

  segActiveRam.style.width = `${activePct}%`;
  segCompressedRam.style.width = `${compPct}%`;
  segFreeRam.style.width = `${freePct}%`;

  // 6. NVMe Storage Stack
  const diskPct = Math.round(storage.used_pct || 0);
  labelDiskPct.textContent = `${diskPct}%`;
  segDiskUsed.style.width = `${diskPct}%`;
  segDiskFree.style.width = `${100 - diskPct}%`;
  lblDiskUsedGb.textContent = `Rooted: ${storage.used_gb || 0} GB`;
  lblDiskFreeGb.textContent = `Fertile: ${storage.free_gb || 0} GB`;
  lblDiskJunkMb.textContent = `${storage.junk_mb || 0} MB`;

  // 7. Dynamic 3D Voxel Engine Update
  if (voxelEngine) {
    voxelEngine.updateTelemetry(hw);
  }

  // 8. Lower Deck: Swarm & Processes
  renderSwarmDeck(hw.optimizer_agents || []);
  renderProcessTable(hw.top_processes || []);
}

function renderCoresGrid(cores) {
  coresDeckGrid.innerHTML = "";
  const treeNames = [
    "🌸 Sakura 0",
    "🍂 Ginkgo 1",
    "🌲 Pine 2",
    "🍁 Maple 3"
  ];
  const treePlantIds = [
    "plant-sakura",
    "plant-ginkgo",
    "plant-pine",
    "plant-maple"
  ];
  cores.forEach((load, idx) => {
    const box = document.createElement("div");
    box.className = "core-monitor-capsule";
    box.style.cursor = "pointer";
    box.title = `Click to isolate ${treeNames[idx]} in the 3D diorama`;
    const color = load > 75 ? "var(--status-alert)" : (load > 40 ? "var(--status-warning)" : "var(--sakura-pink)");
    box.innerHTML = `
      <div class="core-meta-line">
        <span class="core-id-label">${treeNames[idx] || `Core ${idx}`}</span>
        <span class="core-pct-reading">${Math.round(load)}%</span>
      </div>
      <div class="core-meter-track">
        <div class="core-meter-progress" style="width:${load}%;background:${color};"></div>
      </div>
    `;
    box.addEventListener("click", () => {
      if (voxelEngine && voxelEngine.specimens) {
        const spec = voxelEngine.specimens.find(s => s.id === treePlantIds[idx]);
        if (spec) {
          voxelEngine.triggerDistrictSpell(spec);
          showToast(`Isolating ${spec.name} • ${Math.round(load)}% load`);
        }
      }
    });
    coresDeckGrid.appendChild(box);
  });
}

function drawSparkline(canvas, data, strokeColor, minVal, maxVal) {
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  const w = canvas.width;
  const h = canvas.height;

  ctx.clearRect(0, 0, w, h);
  if (!data || data.length < 2) return;

  const step = w / (data.length - 1);
  const range = maxVal - minVal || 1;

  ctx.beginPath();
  data.forEach((val, i) => {
    const clamped = Math.max(minVal, Math.min(maxVal, val));
    const y = h - ((clamped - minVal) / range) * (h - 8) - 4;
    const x = i * step;

    if (i === 0) {
      ctx.moveTo(x, y);
    } else {
      const prevX = (i - 1) * step;
      const prevVal = Math.max(minVal, Math.min(maxVal, data[i - 1]));
      const prevY = h - ((prevVal - minVal) / range) * (h - 8) - 4;
      const cpX = (prevX + x) / 2;
      ctx.bezierCurveTo(cpX, prevY, cpX, y, x, y);
    }
  });

  ctx.strokeStyle = strokeColor;
  ctx.lineWidth = 1.75;
  ctx.stroke();

  ctx.lineTo(w, h);
  ctx.lineTo(0, h);
  ctx.closePath();

  const grad = ctx.createLinearGradient(0, 0, 0, h);
  grad.addColorStop(0, strokeColor === "#10b981" ? "rgba(16, 185, 129, 0.22)" : "rgba(244, 114, 182, 0.18)");
  grad.addColorStop(1, "rgba(0, 0, 0, 0)");
  ctx.fillStyle = grad;
  ctx.fill();
}

function renderSwarmDeck(agents) {
  swarmAgentGrid.innerHTML = "";
  agents.forEach(a => {
    const card = document.createElement("div");
    card.className = "guardian-agent-box";
    card.innerHTML = `
      <div class="agent-header-row">
        <div class="agent-title-cluster">
          <svg class="icon-svg" viewBox="0 0 24 24"><path d="M12 2C9 5 5 9 5 13a7 7 0 0 0 14 0c0-4-4-8-7-11z"/></svg>
          <span>${a.name}</span>
        </div>
        <span class="agent-state-pill">${a.state}</span>
      </div>
      <div class="agent-deliberation-text">"${a.last_action}"</div>
      <div class="agent-metrics-row">
        <span>Dew Freed: <strong style="color:var(--forest-jade);">+${a.total_freed_mb || 0} MB</strong></span>
        <span>Harmonies: <strong>${a.optimizations_performed || 0}</strong></span>
      </div>
    `;
    card.addEventListener("click", () => showPcbInspector(a.name, a.last_action, [
      `Guardian Spirit: ${a.name}`,
      `Grove Territory: ${a.district}`,
      `Dew Compaction: +${a.total_freed_mb} MB`,
      `Sanctuary Quota: Elevated Win32 psapi`,
    ]));
    swarmAgentGrid.appendChild(card);
  });
}

function renderProcessTable(procs) {
  processTableBody.innerHTML = "";
  procs.forEach(p => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td style="font-weight:600;">${p.name}</td>
      <td style="font-family:var(--font-mono);color:var(--text-dim);">${p.pid}</td>
      <td><span class="memory-tag-chip">${p.mem_mb} MB</span></td>
      <td><span style="color:var(--forest-jade);font-size:11px;">Active Flora</span></td>
      <td>
        <button class="pill-btn btn-secondary" style="padding:2px 8px;font-size:10px;" onclick="trimSpecificProcess(${p.pid}, '${p.name}')">
          Trim
        </button>
      </td>
    `;
    processTableBody.appendChild(tr);
  });
}

window.trimSpecificProcess = function(pid, name) {
  showToast(`Compacting leaf dew for PID ${pid} (${name || "Flora"})...`);
  triggerPcbShockwave("chip-ram");

  fetch("/api/controls", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ action: "TRIM_PID", payload: { pid: pid } }),
  })
    .then(r => r.json())
    .then(data => {
      showToast(`Pruned leaf working set for PID ${pid}. Recovered dew.`);
      appendAuditRow("Process Trimming", `Pruned working set for PID ${pid} (${name}).`);
      fetchTelemetryRest();
    })
    .catch(err => showToast(`Notice: ${err}`));
};

function appendAuditRow(title, desc) {
  const row = document.createElement("div");
  row.className = "audit-stream-entry";
  const now = new Date().toLocaleTimeString();
  row.innerHTML = `
    <span class="audit-entry-time">[${now}]</span>
    <span style="color:var(--sakura-pink);font-weight:600;">${title}:</span>
    <span>${desc}</span>
  `;
  auditStreamFeed.prepend(row);
}

// =============================================================================
// 3. 3D VOXEL SANCTUARY STAGE INITIALIZATION
// =============================================================================
function initVoxelStage() {
  if (!voxelCanvas || !window.VoxelMotherboardEngine) return;
  voxelEngine = new window.VoxelMotherboardEngine();
  voxelEngine.init(voxelCanvas, {
    onDistrictClick: (district) => {
      if (district && district.name) {
        showPcbInspector(
          district.name,
          district.desc || district.subtitle || "Sanctuary Subsystem Telemetry",
          district.items || [
            "Subsystem Target: Silicon Sanctuary Hardware",
            "Privilege Level: Windows 11 Elevated Quota",
            "Autonomous Mode: Live Monitoring & Botanical Compaction",
          ]
        );
      }
    },
  });

  function setActiveCamBtn(btn) {
    [btnCamIso, btnCamLow, btnCamTop].forEach(b => b && b.classList.remove("active"));
    if (btn) btn.classList.add("active");
  }

  if (btnCamIso) {
    btnCamIso.addEventListener("click", () => {
      voxelEngine.setCameraPreset("isometric");
      setActiveCamBtn(btnCamIso);
    });
  }
  if (btnCamLow) {
    btnCamLow.addEventListener("click", () => {
      voxelEngine.setCameraPreset("lowAngle");
      setActiveCamBtn(btnCamLow);
    });
  }
  if (btnCamTop) {
    btnCamTop.addEventListener("click", () => {
      voxelEngine.setCameraPreset("topDown");
      setActiveCamBtn(btnCamTop);
    });
  }
  if (btnTogglePlantTags) {
    btnTogglePlantTags.addEventListener("click", () => {
      if (voxelEngine) {
        voxelEngine.plantTagsEnabled = !voxelEngine.plantTagsEnabled;
        btnTogglePlantTags.textContent = voxelEngine.plantTagsEnabled ? "🏷️ Plant Tags: ON" : "🏷️ Plant Tags: OFF";
        btnTogglePlantTags.classList.toggle("active", voxelEngine.plantTagsEnabled);
        showToast(voxelEngine.plantTagsEnabled ? "Floating in-world plant badges enabled." : "Plant badges hidden.");
      }
    });
  }
  if (btnTogglePackets) {
    btnTogglePackets.addEventListener("click", () => {
      if (voxelEngine) {
        voxelEngine.firefliesEnabled = !voxelEngine.firefliesEnabled;
        voxelEngine.packetFlowEnabled = voxelEngine.firefliesEnabled;
        btnTogglePackets.textContent = voxelEngine.firefliesEnabled ? "Fireflies: ON" : "Fireflies: OFF";
        btnTogglePackets.classList.toggle("active", voxelEngine.firefliesEnabled);
      }
    });
  }
  if (btnPcbZoomReset) {
    btnPcbZoomReset.addEventListener("click", () => {
      voxelEngine.resetCamera();
      setActiveCamBtn(btnCamIso);
    });
  }

  // Time of Day Buttons
  document.querySelectorAll(".tod-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".tod-btn").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      const tod = btn.getAttribute("data-tod") || "twilight";
      if (voxelEngine) {
        voxelEngine.setTimeOfDay(tod);
        showToast(`Sanctuary ambiance shifted to ${tod.toUpperCase()}.`);
      }
    });
  });
}

function showPcbInspector(title, subtitle, items) {
  insHeading.textContent = title;
  insBody.innerHTML = `
    <p style="color:var(--text-lead);font-weight:600;margin-bottom:8px;">${subtitle}</p>
    <ul style="list-style:none;display:flex;flex-direction:column;gap:5px;">
      ${items.map(it => `<li>• ${it}</li>`).join("")}
    </ul>
  `;
  pcbInspectorOverlay.style.display = "block";
}

btnInsClose.addEventListener("click", () => {
  pcbInspectorOverlay.style.display = "none";
});

// =============================================================================
// 4. DIRECT OPTIMIZATION ACTIONS WITH VOXEL FX
// =============================================================================
const btnHeaderNative = document.getElementById("btnHeaderNative");
if (btnHeaderNative) {
  btnHeaderNative.addEventListener("click", executeNativeKernelCompact);
}

btnHeaderRam.addEventListener("click", executeRamBoost);
btnQuickFlushRam.addEventListener("click", executeRamBoost);

btnHeaderStorage.addEventListener("click", executeStorageClean);
btnQuickPurgeDisk.addEventListener("click", executeStorageClean);

btnHeaderFull.addEventListener("click", executeFullOptimize);
btnTrimAllTable.addEventListener("click", executeRamBoost);

function executeNativeKernelCompact() {
  showToast("⚡ Engaging C silicon_kernel.dll for microsecond Win32 working set compaction...");
  triggerPcbShockwave("plant-ram");

  fetch("/api/native/compact", { method: "POST" })
    .then(r => r.json())
    .then(data => {
      const reclaimed = data.reclaimed_mb || 0;
      const count = data.processes_trimmed || 0;
      const ms = data.execution_duration_ms || 0;
      showToast(`⚡ C-Kernel compaction complete! Reclaimed +${reclaimed} MB across ${count} processes in ${ms} ms.`);
      appendAuditRow("C-Kernel Compact", `Flushed ${reclaimed} MB working sets in ${ms} ms via Win32 NT PSAPI.`);
      fetchTelemetryRest();
      fetchEvolutionStatus();
    })
    .catch(err => showToast(`Notice: ${err}`));
}

function fetchEvolutionStatus() {
  fetch("/api/evolution/status")
    .then(r => r.json())
    .then(data => {
      const el = document.getElementById("topEvolutionVal");
      if (el && data.timeline) {
        el.textContent = `Epoch ${data.timeline.current_epoch} / ${data.timeline.total_epochs}`;
      }
    })
    .catch(() => {});
}

function executeRamBoost() {
  showToast("Pruning idle leaf working sets with Windows psapi...");
  triggerPcbShockwave("chip-ram");

  fetch("/api/controls", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ action: "BOOST_MEMORY" }),
  })
    .then(r => r.json())
    .then(data => {
      const res = data.optimization_result || {};
      const freed = res.freed_mb || 0;
      const count = res.trimmed_processes || 0;
      showToast(`Leaves pruned! Restored +${freed} MB fresh dew from ${count} flora processes.`);
      appendAuditRow("Memory Relief", `Flushed ${freed} MB working sets from ${count} processes.`);
      fetchTelemetryRest();
    })
    .catch(err => showToast(`Notice: ${err}`));
}

function executeStorageClean() {
  showToast("Clearing deadwood brambles & dispatching sunlight TRIM...");
  triggerPcbShockwave("chip-nvme");

  fetch("/api/controls", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ action: "PURGE_STORAGE" }),
  })
    .then(r => r.json())
    .then(data => {
      const res = data.optimization_result || {};
      showToast(`Cleared ${res.reclaimed_mb || 0} MB deadwood & nourished NVMe bonsai roots.`);
      appendAuditRow("Storage TRIM", `Purged ${res.reclaimed_mb || 0} MB temp bloat & re-trimmed Drive C:.`);
      fetchTelemetryRest();
    })
    .catch(err => showToast(`Notice: ${err}`));
}

function executeFullOptimize() {
  showToast("Invoking forest spirits for complete sanctuary harmonization...");
  triggerPcbShockwave("chip-soc");

  fetch("/api/controls", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ action: "FULL_OPTIMIZE" }),
  })
    .then(r => r.json())
    .then(data => {
      const res = data.optimization_result || {};
      const memFreed = (res.memory && res.memory.freed_mb) || 0;
      const diskFreed = (res.storage && res.storage.reclaimed_mb) || 0;
      showToast(`Sanctuary harmonized! Restored +${memFreed} MB dew & cleared ${diskFreed} MB deadwood.`);
      appendAuditRow("Full Harmonize", `Recovered +${memFreed} MB RAM and cleared ${diskFreed} MB deadwood.`);
      fetchTelemetryRest();
    })
    .catch(err => showToast(`Notice: ${err}`));
}

function triggerPcbShockwave(districtId) {
  if (voxelEngine) {
    voxelEngine.triggerFlash(districtId || "chip-soc");
  }
}

function showToast(msg) {
  hudToastText.textContent = msg;
  studioHudToast.classList.add("active");
  setTimeout(() => {
    studioHudToast.classList.remove("active");
  }, 3200);
}

// =============================================================================
// 5. INTERACTIVE TERMINAL COMMAND INTERPRETER
// =============================================================================
function handleTerminalCommand() {
  if (!terminalCmdInput) return;
  const raw = terminalCmdInput.value.trim().toLowerCase();
  terminalCmdInput.value = "";
  if (!raw) return;

  appendAuditRow("Terminal [USER]", `> ${raw}`);

  if (raw === "prune" || raw === "ram") {
    executeRamBoost();
  } else if (raw === "clean" || raw === "trim" || raw === "ssd") {
    executeStorageClean();
  } else if (raw === "harmonize" || raw === "optimize" || raw === "full") {
    executeFullOptimize();
  } else if (raw === "status" || raw === "info") {
    const hw = state.telemetry;
    appendAuditRow("Status", `Smoothness: ${hw.smoothness_index}/100 • CPU: ${Math.round(hw.cpu.overall_pct)}% • Free RAM: ${hw.memory.free_mb} MB • Disk Free: ${hw.storage.free_gb} GB`);
  } else if (raw === "dawn" || raw === "day" || raw === "twilight" || raw === "night" || raw === "midnight") {
    const targetTod = raw === "day" ? "daylight" : (raw === "night" ? "midnight" : raw);
    if (voxelEngine) {
      voxelEngine.setTimeOfDay(targetTod);
      showToast(`Sanctuary ambiance shifted to ${targetTod.toUpperCase()}.`);
    }
  } else if (raw === "clear") {
    auditStreamFeed.innerHTML = "";
    appendAuditRow("Sanctuary", "Audit feed cleared.");
  } else if (raw === "help") {
    appendAuditRow("Help", "Commands: prune | clean | harmonize | status | dawn | twilight | night | clear");
  } else {
    appendAuditRow("Terminal", `Unknown command: '${raw}'. Type 'help' for available actions.`);
  }
}

if (btnTerminalSubmit) {
  btnTerminalSubmit.addEventListener("click", handleTerminalCommand);
}
if (terminalCmdInput) {
  terminalCmdInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") handleTerminalCommand();
  });
}

// =============================================================================
// 6. LOWER DECK TAB NAVIGATION
// =============================================================================
document.querySelectorAll(".lower-deck-tab-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".lower-deck-tab-btn").forEach(b => b.classList.remove("active"));
    document.querySelectorAll(".lower-deck-view-panel").forEach(p => p.classList.remove("active"));
    btn.classList.add("active");
    const target = document.getElementById(btn.getAttribute("data-tab"));
    if (target) target.classList.add("active");
  });
});

// Bootstrap Sanctuary
initVoxelStage();
updateHardwareTelemetry(state.telemetry);
fetchTelemetryRest();
initTelemetry();
fetchEvolutionStatus();
setInterval(fetchEvolutionStatus, 5000);
