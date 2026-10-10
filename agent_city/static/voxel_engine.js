/**
 * ============================================================================
 * SILICON FOREST — Master-Grade Living Voxel Sanctuary Engine
 * Built from First Principles according to @voxel-art & @anti-slop-design
 *
 * Authentic 2.5D Isometric Diorama Architecture:
 * • 28x28 Square Isometric Plot with True 3D Diamond Projection & Close-Up Framing
 * • Multi-Tree Botanical Grove (4 Dedicated Non-Overlapping Quadrants):
 *    - 🌸 Sakura Cherry Blossom (Top-Left  • Intel N100 Core 0 — Pastel Spring Rose Canopy)
 *    - 🍂 Golden Ginkgo Tree    (Top-Right • Intel N100 Core 1 — Amber Conical Fan Spire)
 *    - 🌲 Emerald Jade Pine     (Mid-Left  • Intel N100 Core 2 — Pagoda Tiered Needles)
 *    - 🍁 Scarlet Autumn Maple  (Mid-Right • Intel N100 Core 3 — Cascading Fiery Momiji Drape)
 *    - 🪷 Azure Lotus Dew Basin (Center    • Physical 8GB RAM — Crystalline Pool & Lotuses)
 *    - 🎋 Cedar Root Palisade   (Perimeter • Storage Drive C: — Boundary Pickets & Thorns)
 *    - 🌷 Meadow Flora Cluster  (Fore-Left • Active Processes — Vibrant Tulips & Lavender)
 *    - 🐇 White Voxel Bunny     (Fore-Mid  • Thread Governor — Animated Ears & Tail)
 * • 3-Tier Botanical Identification System:
 *    1. Planted 3D Voxel Wooden Signposts with carved plaques at the base of every specimen
 *    2. Floating In-World Billboard Identification Badges with live telemetry metrics
 *    3. Cursor-Tracking Rich Glassmorphic Botanical Inspector Card (Hover HUD)
 * • MagicaVoxel Shading Model: Top (+Z: 1.32x), Left (+Y: 0.94x), Right (+X: 0.70x)
 * • Depth-Sorted Painter's Algorithm with True View Ray Projection
 * ============================================================================
 */

(function (window) {
  "use strict";

  // ===========================================================================
  // 1. MASTER 44-COLOR BOTANICAL PALETTE (Palette-First Design Pattern)
  // ===========================================================================
  const PALETTE = {
    // Stone & Bedrock Stratum
    STONE_DARK: "#1e2430",
    STONE_MID: "#384354",
    STONE_LIGHT: "#5a687d",
    STONE_PEBBLE: "#8594a8",
    STONE_WHITE: "#f8fafc",
    STONE_SLATE: "#cbd5e1",

    // Earth, Soil & Foundation Rim
    EARTH_DEEP: "#1a120b",
    EARTH_MID: "#301e12",
    EARTH_RICH: "#452b1b",
    MOSS_SHADOW: "#1b4d35",

    // Lawn Turf & Tactile Grass Blades (Soft Spring Meadow)
    LAWN_TOP: "#86c975",
    LAWN_SHADOW: "#6fae5e",
    GRASS_BLADE: "#78c466",
    GRASS_EMERALD: "#60ab4f",
    GRASS_DARK: "#4d943e",
    LILY_PAD: "#3b8a38",

    // Cedar Wood & Picket Fence (Warm Natural Timber)
    WOOD_DARK: "#4a2d18",
    WOOD_MID: "#5e3920",
    WOOD_BARK: "#734829",
    WOOD_BRANCH: "#54331b",
    WOOD_POST: "#b58557",
    WOOD_HIGHLIGHT: "#caa074",

    // Signpost Wood & Plaques
    SIGN_POST: "#78350f",
    SIGN_PLAQUE: "#caa074",
    SIGN_PLAQUE_LIGHT: "#e2c9a5",
    SIGN_TEXT: "#451a03",

    // 🌸 Tree 0: Sakura Cherry Blossom (Core 0 — Pastel Spring Pink)
    SAKURA_DARK: "#be185d",
    SAKURA_MID: "#e07a97",
    SAKURA_LIGHT: "#f799b2",
    SAKURA_PALE: "#ffdbe5",
    SAKURA_WHITE: "#fff3f6",

    // 🍂 Tree 1: Golden Ginkgo Tree (Core 1 — Warm Amber Gold)
    GINKGO_DARK: "#9a3412",
    GINKGO_MID: "#d97706",
    GINKGO_LIGHT: "#f59e0b",
    GINKGO_GOLD: "#fbbf24",
    GINKGO_PALE: "#fef08a",

    // 🌲 Tree 2: Emerald Jade Pine / Bonsai (Core 2 — Rich Forest Evergreen)
    PINE_DARK: "#064e3b",
    PINE_MID: "#047857",
    PINE_LIGHT: "#059669",
    PINE_EMERALD: "#10b981",
    PINE_SPRING: "#34d399",

    // 🍁 Tree 3: Scarlet Autumn Maple (Core 3 — Fiery Japanese Momiji Crimson)
    MAPLE_DARK: "#7f1d1d",
    MAPLE_MID: "#991b1b",
    MAPLE_LIGHT: "#b91c1c",
    MAPLE_RUBY: "#dc2626",
    MAPLE_FLAME: "#ef4444",

    // 🪷 Crystalline Water Basin & Lotuses (RAM Sanctuary)
    WATER_DEEP: "#245870",
    WATER_MID: "#367594",
    WATER_SURFACE: "#529ebf",
    WATER_RIPPLE: "#7ec3db",
    WATER_FOAM: "#d2f0f9",
    LOTUS_WHITE: "#ffffff",
    LOTUS_PINK: "#f472b6",
    LOTUS_GOLD: "#fef08a",

    // Flowers (Tulips, Dandelions, Lavender)
    TULIP_RED: "#e12d39",
    TULIP_CRIMSON: "#b91c28",
    TULIP_LIGHT: "#f87171",
    TULIP_STEM: "#3f8c3c",
    DANDY_GOLD: "#f6cf3e",
    DANDY_LIGHT: "#fef08a",
    LAVENDER_PURPLE: "#a259e8",
    LAVENDER_LILAC: "#c084fc",

    // White Voxel Bunny Rabbit
    BUNNY_WHITE: "#fefefe",
    BUNNY_SHADOW: "#ebe6df",
    BUNNY_EAR_PINK: "#f9a8be",
    BUNNY_NOSE: "#f0718f",
    BUNNY_EYES: "#1c1917",

    // Fluttering Butterflies
    BUTTERFLY_CYAN: "#38bdf8",
    BUTTERFLY_ORANGE: "#fb923c",
    BUTTERFLY_VIOLET: "#c084fc",
    BUTTERFLY_LIME: "#a3e635",
    BUTTERFLY_BODY: "#1e293b",

    // Destructible Deadwood Thorns (Disk Bloat)
    THORN_DARK: "#450a0a",
    THORN_CRIMSON: "#991b1b",
    THORN_RED: "#ef4444",

    // Lanterns & Owls
    LANTERN_CORE: "#fef08a",
    OWL_BEAK: "#f59e0b",
  };

  const SHADE_CACHE = new Map();

  function parseHex(hex) {
    if (!hex || hex[0] !== "#") return [140, 140, 150];
    const c = hex.slice(1);
    if (c.length === 3) {
      return [
        parseInt(c[0] + c[0], 16),
        parseInt(c[1] + c[1], 16),
        parseInt(c[2] + c[2], 16),
      ];
    }
    return [
      parseInt(c.slice(0, 2), 16),
      parseInt(c.slice(2, 4), 16),
      parseInt(c.slice(4, 6), 16),
    ];
  }

  function getShade(hex, factor) {
    const key = `${hex}_${factor.toFixed(2)}`;
    let cached = SHADE_CACHE.get(key);
    if (cached) return cached;

    const rgb = parseHex(hex);
    const r = Math.min(255, Math.max(0, Math.round(rgb[0] * factor)));
    const g = Math.min(255, Math.max(0, Math.round(rgb[1] * factor)));
    const b = Math.min(255, Math.max(0, Math.round(rgb[2] * factor)));
    cached = `rgb(${r},${g},${b})`;
    SHADE_CACHE.set(key, cached);
    return cached;
  }

  // ===========================================================================
  // 2. ENGINE CORE CLASS
  // ===========================================================================
  class VoxelMotherboardEngine {
    constructor() {
      this.canvas = null;
      this.ctx = null;
      this.width = 0;
      this.height = 0;
      this.dpr = 1;

      // Camera State with optimal framing
      this.camera = {
        angle: Math.PI / 4,
        targetAngle: Math.PI / 4,
        pitch: 0.6154,
        targetPitch: 0.6154,
        zoom: 1.0,
        targetZoom: 1.0,
        panX: 0,
        targetPanX: 0,
        panY: 46,
        targetPanY: 46,
        timeOfDay: "twilight",
      };

      // Telemetry Store
      this.telemetry = {
        cpuCores: [12, 14, 18, 10],
        cpuOverall: 14,
        cpuFreqMhz: 2900,
        ramUsedPct: 48,
        ramUsedMb: 3840,
        ramFreeMb: 4160,
        diskUsedPct: 74,
        diskFreeGb: 58,
        junkMb: 124.5,
        smoothness: 92,
        agents: [],
      };

      // Animation & Timing
      this.time = 0;
      this.lastTime = performance.now();
      this.animId = null;
      this.unit = 21;
      this.windForce = 0;

      // Particle Systems
      this.fallingPetals = [];
      this.fireflies = [];
      this.physicsVoxels = [];
      this.shockwaves = [];
      this.grassBlades = [];
      this.butterflies = [];

      // Interactivity & Hit-testing
      this.hitZones = [];
      this.specimens = [];
      this.hoveredDistrict = null;
      this.hoverPoint = null;
      this.isDragging = false;
      this.lastMouseX = 0;
      this.lastMouseY = 0;
      this.firefliesEnabled = true;
      this.packetFlowEnabled = true;
      this.plantTagsEnabled = true;

      // External Callback Hooks
      this.onDistrictClick = null;
      this.onDistrictHover = null;

      this._boundRender = this.render.bind(this);
    }

    init(canvasElement, options = {}) {
      this.canvas = canvasElement;
      this.ctx = this.canvas.getContext("2d", { alpha: false });
      this.onDistrictClick = options.onDistrictClick || null;
      this.onDistrictHover = options.onDistrictHover || null;

      this.resize();
      window.addEventListener("resize", () => this.resize());

      this.initEvents();
      this.initGrassBlades();
      this.initButterflies();
      this.initFireflies();
      this.initFallingPetals();

      this.lastTime = performance.now();
      this.animId = requestAnimationFrame(this._boundRender);
    }

    resize() {
      if (!this.canvas) return;
      const rect = this.canvas.parentElement.getBoundingClientRect();
      this.width = rect.width;
      this.height = Math.max(460, rect.height);
      this.dpr = Math.min(2, window.devicePixelRatio || 1);

      this.canvas.width = this.width * this.dpr;
      this.canvas.height = this.height * this.dpr;
      this.canvas.style.width = `${this.width}px`;
      this.canvas.style.height = `${this.height}px`;

      this.ctx.scale(this.dpr, this.dpr);

      // Framed scale: fills ~80% of canvas with complete breathing room
      this.unit = Math.min(this.width / 34, this.height / 24) * 1.10 * this.camera.zoom;
    }

    initEvents() {
      const cv = this.canvas;

      cv.addEventListener("mousedown", (e) => {
        this.isDragging = true;
        this.lastMouseX = e.clientX;
        this.lastMouseY = e.clientY;
      });

      window.addEventListener("mouseup", () => {
        this.isDragging = false;
      });

      cv.addEventListener("mousemove", (e) => {
        const rect = cv.getBoundingClientRect();
        const mx = e.clientX - rect.left;
        const my = e.clientY - rect.top;

        if (this.isDragging) {
          const dx = e.clientX - this.lastMouseX;
          const dy = e.clientY - this.lastMouseY;

          this.camera.targetAngle += dx * 0.007;
          this.camera.targetPitch = Math.max(0.25, Math.min(1.15, this.camera.targetPitch + dy * 0.004));

          this.lastMouseX = e.clientX;
          this.lastMouseY = e.clientY;
        } else {
          this.checkHover(mx, my);
        }
      });

      cv.addEventListener("wheel", (e) => {
        e.preventDefault();
        const factor = e.deltaY < 0 ? 1.08 : 0.92;
        this.camera.targetZoom = Math.max(0.7, Math.min(1.85, this.camera.targetZoom * factor));
      }, { passive: false });

      cv.addEventListener("click", (e) => {
        const rect = cv.getBoundingClientRect();
        const mx = e.clientX - rect.left;
        const my = e.clientY - rect.top;
        const hit = this.findHitDistrict(mx, my);
        if (hit) {
          this.triggerDistrictSpell(hit);
          if (this.onDistrictClick) this.onDistrictClick(hit);
        }
      });

      cv.addEventListener("mouseleave", () => {
        this.hoveredDistrict = null;
        this.hoverPoint = null;
      });
    }

    initGrassBlades() {
      this.grassBlades = [];
      const colors = [PALETTE.GRASS_BLADE, PALETTE.GRASS_EMERALD, PALETTE.LAWN_TOP];
      for (let x = 1.8; x < 26.2; x += 1.4) {
        for (let y = 1.8; y < 26.2; y += 1.4) {
          const distToCenter = Math.hypot(x - 13.5, y - 13.5);
          if (distToCenter < 3.8) continue;

          const hash = Math.sin(x * 12.9898 + y * 78.233) * 43758.5453;
          const rand = hash - Math.floor(hash);
          if (rand > 0.52) {
            const cIdx = Math.floor(rand * 3) % 3;
            const h = 0.35 + (rand * 0.32);
            const jx = (rand - 0.5) * 0.4;
            const jy = (((rand * 5) % 1) - 0.5) * 0.4;
            this.grassBlades.push({
              x: x + jx,
              y: y + jy,
              h: h,
              color: colors[cIdx],
              topColor: PALETTE.GRASS_BLADE,
            });
          }
        }
      }
    }

    initButterflies() {
      this.butterflies = [
        { id: 0, color: PALETTE.BUTTERFLY_ORANGE, baseX: 5.5, baseY: 11.0, baseZ: 8.5, radius: 2.2, speed: 1.2, phase: 0.0 },
        { id: 1, color: PALETTE.BUTTERFLY_LIME,   baseX: 11.5, baseY: 5.5, baseZ: 9.0, radius: 2.0, speed: 1.4, phase: 1.8 },
        { id: 2, color: PALETTE.BUTTERFLY_CYAN,   baseX: 6.5,  baseY: 18.5, baseZ: 7.8, radius: 2.4, speed: 1.1, phase: 3.5 },
        { id: 3, color: PALETTE.BUTTERFLY_VIOLET, baseX: 19.5, baseY: 13.5, baseZ: 8.0, radius: 1.8, speed: 1.5, phase: 5.1 },
      ];
    }

    initFireflies() {
      this.fireflies = [];
      const colors = [PALETTE.LANTERN_CORE, PALETTE.GRASS_BLADE, PALETTE.WATER_SURFACE, PALETTE.SAKURA_LIGHT];
      for (let i = 0; i < 16; i++) {
        this.fireflies.push({
          baseX: 3 + Math.random() * 22,
          baseY: 3 + Math.random() * 22,
          baseZ: 1.2 + Math.random() * 4,
          x: 0,
          y: 0,
          z: 0,
          ampX: 0.8 + Math.random() * 1.5,
          ampY: 0.8 + Math.random() * 1.5,
          freqX: 0.8 + Math.random() * 1.2,
          freqY: 0.8 + Math.random() * 1.2,
          phase: Math.random() * Math.PI * 2,
          color: colors[i % colors.length],
        });
      }
    }

    initFallingPetals() {
      this.fallingPetals = [];
      const colors = [
        PALETTE.SAKURA_LIGHT, PALETTE.SAKURA_PALE, PALETTE.SAKURA_WHITE,
        PALETTE.GINKGO_GOLD, PALETTE.MAPLE_RUBY
      ];
      for (let i = 0; i < 32; i++) {
        this.fallingPetals.push({
          x: Math.random() * 26 + 1,
          y: Math.random() * 26 + 1,
          z: 6 + Math.random() * 8,
          vx: (Math.random() - 0.5) * 0.8,
          vy: (Math.random() - 0.5) * 0.8,
          vz: -0.6 - Math.random() * 0.8,
          size: 2.2 + Math.random() * 1.6,
          rot: Math.random() * Math.PI * 2,
          rotSpeed: (Math.random() - 0.5) * 3,
          color: colors[Math.floor(Math.random() * colors.length)],
        });
      }
    }

    updateTelemetry(hw) {
      if (!hw) return;
      const cpu = hw.cpu || {};
      const mem = hw.memory || {};
      const storage = hw.storage || {};

      this.telemetry.cpuCores = cpu.cores || [10, 12, 16, 8];
      this.telemetry.cpuOverall = cpu.overall_pct || 14;
      this.telemetry.cpuFreqMhz = cpu.freq_mhz || 2900;

      this.telemetry.ramUsedPct = mem.used_pct || 48;
      this.telemetry.ramUsedMb = mem.used_mb || 3840;
      this.telemetry.ramFreeMb = mem.free_mb || 4160;

      this.telemetry.diskUsedPct = storage.used_pct || 74;
      this.telemetry.diskFreeGb = storage.free_gb || 58;
      this.telemetry.junkMb = storage.junk_mb || 0;

      this.telemetry.smoothness = hw.smoothness_index || 92;
      this.telemetry.agents = hw.optimizer_agents || [];
    }

    setCameraPreset(preset) {
      if (preset === "isometric") {
        this.camera.targetAngle = Math.PI / 4;
        this.camera.targetPitch = 0.6154;
        this.camera.targetZoom = 1.0;
        this.camera.targetPanY = 46;
      } else if (preset === "lowAngle") {
        this.camera.targetAngle = Math.PI / 4 + 0.12;
        this.camera.targetPitch = 0.32;
        this.camera.targetZoom = 1.25;
        this.camera.targetPanY = 52;
      } else if (preset === "topDown") {
        this.camera.targetAngle = Math.PI / 4;
        this.camera.targetPitch = 1.15;
        this.camera.targetZoom = 1.05;
        this.camera.targetPanY = 16;
      }
    }

    setTimeOfDay(tod) {
      this.camera.timeOfDay = tod;
    }

    resetCamera() {
      this.setCameraPreset("isometric");
      this.camera.targetPanX = 0;
      this.camera.targetPanY = 46;
    }

    triggerDistrictSpell(district) {
      if (!district) return;
      if (district.id === "plant-sakura") {
        this.burstPetals(5.5, 11.0, 7.5, 36, PALETTE.SAKURA_LIGHT);
      } else if (district.id === "plant-ginkgo") {
        this.burstPetals(11.5, 5.5, 8.0, 36, PALETTE.GINKGO_GOLD);
      } else if (district.id === "plant-pine") {
        this.burstPetals(6.5, 18.5, 6.5, 36, PALETTE.PINE_EMERALD);
      } else if (district.id === "plant-maple") {
        this.burstPetals(19.5, 13.5, 7.0, 36, PALETTE.MAPLE_RUBY);
      } else if (district.id === "plant-ram") {
        this.burstDewLeaves(13.5, 13.5, 1.5, 32);
      } else if (district.id === "plant-nvme") {
        this.shatterThorns(14.0, 3.0, 1.0, 24);
      } else if (district.id === "plant-flora") {
        this.burstPetals(8.5, 23.5, 2.5, 24, PALETTE.TULIP_LIGHT);
      } else if (district.id === "plant-bunny") {
        this.burstPetals(14.0, 21.0, 2.0, 18, PALETTE.BUNNY_WHITE);
      }

      this.shockwaves.push({
        x: district.worldX || 14,
        y: district.worldY || 14,
        radius: 2,
        maxRadius: 22,
        alpha: 0.9,
      });
    }

    burstPetals(cx, cy, cz, count, color = PALETTE.SAKURA_LIGHT) {
      for (let i = 0; i < count; i++) {
        const ang = Math.random() * Math.PI * 2;
        const spd = 2.0 + Math.random() * 4.5;
        this.physicsVoxels.push({
          x: cx,
          y: cy,
          z: cz + Math.random() * 1.5,
          vx: Math.cos(ang) * spd,
          vy: Math.sin(ang) * spd,
          vz: 1.5 + Math.random() * 4.0,
          size: 2.6,
          color: color,
          life: 1.0,
          decay: 0.7 + Math.random() * 0.5,
        });
      }
    }

    burstDewLeaves(cx, cy, cz, count) {
      for (let i = 0; i < count; i++) {
        const ang = Math.random() * Math.PI * 2;
        const spd = 2.5 + Math.random() * 3.5;
        this.physicsVoxels.push({
          x: cx + (Math.random() - 0.5) * 3,
          y: cy + (Math.random() - 0.5) * 3,
          z: cz + Math.random() * 1.5,
          vx: Math.cos(ang) * spd,
          vy: Math.sin(ang) * spd,
          vz: 2.0 + Math.random() * 3.0,
          size: 2.8,
          color: Math.random() > 0.4 ? PALETTE.WATER_SURFACE : PALETTE.LILY_PAD,
          life: 1.0,
          decay: 0.6 + Math.random() * 0.4,
        });
      }
    }

    shatterThorns(cx, cy, cz, count) {
      for (let i = 0; i < count; i++) {
        const ang = Math.random() * Math.PI * 2;
        const spd = 3.0 + Math.random() * 5.0;
        this.physicsVoxels.push({
          x: cx + (Math.random() - 0.5) * 3,
          y: cy + (Math.random() - 0.5) * 3,
          z: cz + 0.5,
          vx: Math.cos(ang) * spd,
          vy: Math.sin(ang) * spd,
          vz: 2.5 + Math.random() * 5.0,
          size: 3.0,
          color: Math.random() > 0.5 ? PALETTE.THORN_CRIMSON : PALETTE.THORN_RED,
          life: 1.0,
          decay: 0.8 + Math.random() * 0.5,
        });
      }
    }

    project(x, y, z) {
      const cosA = Math.cos(this.camera.angle);
      const sinA = Math.sin(this.camera.angle);

      const dx = x - 14;
      const dy = y - 14;

      const rx = dx * cosA - dy * sinA;
      const ry = dx * sinA + dy * cosA;

      const sinP = Math.sin(this.camera.pitch);
      const cosP = Math.cos(this.camera.pitch);

      const screenX = this.width / 2 + rx * this.unit + this.camera.panX;
      const screenY = this.height / 2 + ry * sinP * this.unit - z * cosP * this.unit + this.camera.panY;

      return { x: screenX, y: screenY };
    }

    calcDepth(x, y, z) {
      const cosA = Math.cos(this.camera.angle);
      const sinA = Math.sin(this.camera.angle);

      const dx = x - 14;
      const dy = y - 14;

      const ry = dx * sinA + dy * cosA;
      const sinP = Math.sin(this.camera.pitch);
      const cosP = Math.cos(this.camera.pitch);

      return ry * cosP + z * sinP;
    }

    render(now) {
      const dt = Math.min(0.1, (now - this.lastTime) / 1000);
      this.lastTime = now;
      this.time += dt;

      this.camera.angle += (this.camera.targetAngle - this.camera.angle) * 0.12;
      this.camera.pitch += (this.camera.targetPitch - this.camera.pitch) * 0.12;
      this.camera.zoom += (this.camera.targetZoom - this.camera.zoom) * 0.14;
      this.camera.panX += (this.camera.targetPanX - this.camera.panX) * 0.14;
      this.camera.panY += (this.camera.targetPanY - this.camera.panY) * 0.14;

      this.unit = Math.min(this.width / 34, this.height / 24) * 1.10 * this.camera.zoom;
      this.windForce = Math.sin(this.time * 1.2) * 0.35 + Math.cos(this.time * 0.4) * 0.15;

      // Update fireflies
      if (this.firefliesEnabled && this.packetFlowEnabled !== false) {
        this.fireflies.forEach(f => {
          f.x = f.baseX + Math.sin(this.time * f.freqX + f.phase) * f.ampX;
          f.y = f.baseY + Math.cos(this.time * f.freqY + f.phase) * f.ampY;
          f.z = 1.0 + Math.sin(this.time * 2.2 + f.phase) * 0.6;
        });
      }

      // Update falling petals
      this.fallingPetals.forEach(p => {
        p.x += (p.vx + this.windForce * 0.8) * dt;
        p.y += p.vy * dt;
        p.z += p.vz * dt;
        p.rot += p.rotSpeed * dt;

        if (p.z <= 0.2 || p.x > 30 || p.y > 30) {
          p.x = Math.random() * 26 + 1;
          p.y = Math.random() * 26 + 1;
          p.z = 10 + Math.random() * 5;
        }
      });

      // Update physics debris
      for (let i = this.physicsVoxels.length - 1; i >= 0; i--) {
        const pv = this.physicsVoxels[i];
        pv.x += pv.vx * dt;
        pv.y += pv.vy * dt;
        pv.z += pv.vz * dt;
        pv.vz -= 9.8 * dt;
        if (pv.z <= 0) {
          pv.z = 0;
          pv.vz = -pv.vz * 0.35;
          pv.vx *= 0.7;
          pv.vy *= 0.7;
        }
        pv.life -= pv.decay * dt;
        if (pv.life <= 0) {
          this.physicsVoxels.splice(i, 1);
        }
      }

      // Update shockwaves
      for (let i = this.shockwaves.length - 1; i >= 0; i--) {
        const sw = this.shockwaves[i];
        sw.radius += 18 * dt;
        sw.alpha -= 1.2 * dt;
        if (sw.alpha <= 0 || sw.radius >= sw.maxRadius) {
          this.shockwaves.splice(i, 1);
        }
      }

      const ctx = this.ctx;

      this.drawAtmosphere(ctx);

      this.hitZones = [];
      this.specimens = [];

      this.renderSanctuary(ctx);

      // Render Floating In-World Plant Identification Badges
      if (this.plantTagsEnabled) {
        this.drawPlantTags(ctx);
      }

      // Render Rich Cursor-Tracking Glassmorphic Botanical Inspector Card
      if (this.hoveredDistrict && this.hoverPoint) {
        this.drawHoverHud(ctx, this.hoverPoint, this.hoveredDistrict);
      }

      this.drawFooterHud(ctx);

      this.animId = requestAnimationFrame(this._boundRender);
    }

    drawAtmosphere(ctx) {
      ctx.clearRect(0, 0, this.width, this.height);

      const cx = this.width / 2;
      const cy = this.height / 2 + 10;
      const r = Math.max(this.width, this.height) * 0.85;

      const grad = ctx.createRadialGradient(cx, cy, 20, cx, cy, r);

      if (this.camera.timeOfDay === "dawn") {
        grad.addColorStop(0, "rgba(254, 215, 170, 0.16)");
        grad.addColorStop(0.35, "rgba(244, 114, 182, 0.09)");
        grad.addColorStop(0.75, "#1e1b4b");
        grad.addColorStop(1, "#09090b");
      } else if (this.camera.timeOfDay === "daylight") {
        grad.addColorStop(0, "rgba(56, 189, 248, 0.15)");
        grad.addColorStop(0.35, "rgba(16, 185, 129, 0.08)");
        grad.addColorStop(0.75, "#0f172a");
        grad.addColorStop(1, "#020617");
      } else if (this.camera.timeOfDay === "midnight") {
        grad.addColorStop(0, "rgba(168, 85, 247, 0.08)");
        grad.addColorStop(0.4, "rgba(15, 23, 42, 0.95)");
        grad.addColorStop(1, "#020408");
      } else {
        grad.addColorStop(0, "rgba(244, 114, 182, 0.12)");
        grad.addColorStop(0.35, "rgba(16, 185, 129, 0.08)");
        grad.addColorStop(0.75, "rgba(15, 23, 20, 0.95)");
        grad.addColorStop(1, "#080c09");
      }

      ctx.fillStyle = grad;
      ctx.fillRect(0, 0, this.width, this.height);
    }

    renderSanctuary(ctx) {
      const voxels = [];

      // =======================================================================
      // SPECIMEN METADATA & HARDWARE MAPPINGS
      // =======================================================================
      const c0Load = Math.round(this.telemetry.cpuCores[0] || 0);
      const c1Load = Math.round(this.telemetry.cpuCores[1] || 0);
      const c2Load = Math.round(this.telemetry.cpuCores[2] || 0);
      const c3Load = Math.round(this.telemetry.cpuCores[3] || 0);

      // Specimen 0: Sakura Cherry Blossom (Core 0 — Top-Left Quadrant)
      const sakuraSpecimen = {
        id: "plant-sakura",
        tag: `🌸 Sakura (C0) • ${c0Load}%`,
        name: "🌸 Sakura Cherry Blossom",
        scientific: "Prunus serrulata 'Akebono'",
        component: "Intel® N100 Core 0 (Gracemont)",
        color: PALETTE.SAKURA_LIGHT,
        badgeColor: "#f472b6",
        load: c0Load,
        health: `${Math.max(1, 100 - c0Load)}% Headroom`,
        stat: `Load: ${c0Load}% • Freq: ${Math.round(this.telemetry.cpuFreqMhz)} MHz`,
        desc: "Primary system executive core & foreground UI compositor thread.",
        action: "Click to isolate Core 0 & trigger blossom burst",
        worldX: 5.5,
        worldY: 11.0,
        worldZ: 8.4,
      };

      // Specimen 1: Golden Ginkgo Tree (Core 1 — Top-Right Quadrant)
      const ginkgoSpecimen = {
        id: "plant-ginkgo",
        tag: `🍂 Ginkgo (C1) • ${c1Load}%`,
        name: "🍂 Golden Ginkgo Tree",
        scientific: "Ginkgo biloba 'Autumn Gold'",
        component: "Intel® N100 Core 1 (Gracemont)",
        color: PALETTE.GINKGO_GOLD,
        badgeColor: "#f59e0b",
        load: c1Load,
        health: `${Math.max(1, 100 - c1Load)}% Headroom`,
        stat: `Load: ${c1Load}% • Freq: ${Math.round(this.telemetry.cpuFreqMhz)} MHz`,
        desc: "High-throughput asynchronous computation & background IPC bus.",
        action: "Click to isolate Core 1 & trigger golden shower",
        worldX: 11.5,
        worldY: 5.5,
        worldZ: 8.8,
      };

      // Specimen 2: Emerald Jade Pine (Core 2 — Mid-Left Quadrant)
      const pineSpecimen = {
        id: "plant-pine",
        tag: `🌲 Jade Pine (C2) • ${c2Load}%`,
        name: "🌲 Emerald Jade Pine",
        scientific: "Pinus parviflora 'Matsu'",
        component: "Intel® N100 Core 2 (Gracemont)",
        color: PALETTE.PINE_EMERALD,
        badgeColor: "#10b981",
        load: c2Load,
        health: `${Math.max(1, 100 - c2Load)}% Headroom`,
        stat: `Load: ${c2Load}% • Freq: ${Math.round(this.telemetry.cpuFreqMhz)} MHz`,
        desc: "Reliable I/O coordinator, page cache manager & disk flush engine.",
        action: "Click to isolate Core 2 & trigger needle flurry",
        worldX: 6.5,
        worldY: 18.5,
        worldZ: 7.8,
      };

      // Specimen 3: Scarlet Autumn Maple (Core 3 — Mid-Right Quadrant)
      const mapleSpecimen = {
        id: "plant-maple",
        tag: `🍁 Scarlet Maple (C3) • ${c3Load}%`,
        name: "🍁 Scarlet Autumn Maple",
        scientific: "Acer palmatum 'Momiji'",
        component: "Intel® N100 Core 3 (Gracemont)",
        color: PALETTE.MAPLE_RUBY,
        badgeColor: "#ef4444",
        load: c3Load,
        health: `${Math.max(1, 100 - c3Load)}% Headroom`,
        stat: `Load: ${c3Load}% • Freq: ${Math.round(this.telemetry.cpuFreqMhz)} MHz`,
        desc: "Network packet dispatcher, WebSocket gateway & audio subsystem.",
        action: "Click to isolate Core 3 & trigger maple flutter",
        worldX: 19.5,
        worldY: 13.5,
        worldZ: 8.0,
      };

      // Specimen 4: Lotus Dew Basin (RAM — Center Sanctuary)
      const ramSpecimen = {
        id: "plant-ram",
        tag: `🪷 RAM Basin • ${Math.round(this.telemetry.ramUsedPct)}%`,
        name: "🪷 Azure Lotus Dew Basin",
        scientific: "Nelumbo nucifera 'Sanctuary'",
        component: "8GB LPDDR5 Physical Memory",
        color: PALETTE.WATER_SURFACE,
        badgeColor: "#38bdf8",
        load: Math.round(this.telemetry.ramUsedPct),
        health: `${Math.round(this.telemetry.ramFreeMb)} MB Free Headroom`,
        stat: `Used: ${Math.round(this.telemetry.ramUsedMb)} MB • Free: ${Math.round(this.telemetry.ramFreeMb)} MB`,
        desc: "Crystalline RAM dew pool with EmptyWorkingSet leaf flush hook.",
        action: "Click basin to flush idle leaf dew across processes",
        worldX: 13.5,
        worldY: 13.5,
        worldZ: 2.0,
      };

      // Specimen 5: Cedar Root Palisade (NVMe — Boundary)
      const nvmeSpecimen = {
        id: "plant-nvme",
        tag: `🎋 Drive C: Palisade • ${Math.round(this.telemetry.diskUsedPct)}%`,
        name: "🎋 Cedar Root Palisade",
        scientific: "Cryptomeria japonica 'Bedrock'",
        component: "NVMe SSD C: & Root Substratum",
        color: PALETTE.WOOD_POST,
        badgeColor: "#d97706",
        load: Math.round(this.telemetry.diskUsedPct),
        health: `${this.telemetry.diskFreeGb} GB Fertile Space`,
        stat: `Occupied: ${Math.round(this.telemetry.diskUsedPct)}% • Deadwood: ${this.telemetry.junkMb} MB`,
        desc: "Solid timber boundary fence with TRIM defrag.exe sunlight purge.",
        action: "Click fence to purge deadwood thorns and dispatch TRIM",
        worldX: 14.0,
        worldY: 2.8,
        worldZ: 3.5,
      };

      // Specimen 6: Meadow Flora Cluster (Active Processes — Fore-Left)
      const floraSpecimen = {
        id: "plant-flora",
        tag: "🌷 Meadow Flora: Active Apps",
        name: "🌷 Meadow Flora Cluster",
        scientific: "Tulipa & Taraxacum 'Processus'",
        component: "Windows Background Process Swarm",
        color: PALETTE.TULIP_LIGHT,
        badgeColor: "#a855f7",
        load: this.telemetry.agents.length,
        health: "Healthy Meadow Ecology",
        stat: `${this.telemetry.agents.length} Autonomous Guardian Spirits Active`,
        desc: "Vibrant flowerbed representing lightweight OS application threads.",
        action: "Click flowers to inspect process memory footprint",
        worldX: 8.5,
        worldY: 23.5,
        worldZ: 2.8,
      };

      // Specimen 7: White Voxel Bunny (Governor — Fore-Center)
      const bunnySpecimen = {
        id: "plant-bunny",
        tag: "🐇 Thread Governor: Bunny",
        name: "🐇 White Voxel Bunny Rabbit",
        scientific: "Lepus curagendae 'Governor'",
        component: "Quantum Thread Scheduler & Governor",
        color: PALETTE.BUNNY_WHITE,
        badgeColor: "#f472b6",
        load: Math.round(this.telemetry.smoothness),
        health: `${Math.round(this.telemetry.smoothness)}/100 Smoothness`,
        stat: "Active Scheduler • Low Latency Mode",
        desc: "Playful garden mascot keeping OS thread execution responsive.",
        action: "Click bunny to harmonize CPU thread priorities",
        worldX: 14.0,
        worldY: 21.0,
        worldZ: 2.6,
      };

      this.specimens = [
        sakuraSpecimen, ginkgoSpecimen, pineSpecimen, mapleSpecimen,
        ramSpecimen, nvmeSpecimen, floraSpecimen, bunnySpecimen
      ];

      // =======================================================================
      // A. BEDROCK & ISOMETRIC LAWN TURF (28x28 Square Plot)
      // =======================================================================
      // Deep Soil Bedrock Base
      voxels.push({ x: 0.5, y: 0.5, z: -1.2, w: 27.0, d: 27.0, h: 1.2, color: PALETTE.EARTH_MID, topColor: PALETTE.EARTH_RICH });
      voxels.push({ x: 0.0, y: 0.0, z: -0.3, w: 28.0, d: 28.0, h: 0.3, color: PALETTE.EARTH_DEEP });

      // Lush Lawn Turf Top
      voxels.push({ x: 0.5, y: 0.5, z: 0.0, w: 27.0, d: 27.0, h: 0.4, color: PALETTE.LAWN_SHADOW, topColor: PALETTE.LAWN_TOP, district: nvmeSpecimen });

      // Tactile Vertical Grass Blades
      this.grassBlades.forEach(gb => {
        voxels.push({
          x: gb.x,
          y: gb.y,
          z: 0.4,
          w: 0.35,
          d: 0.35,
          h: gb.h,
          color: gb.color,
          topColor: gb.topColor,
        });
      });

      // =======================================================================
      // B. PERIMETER WOODEN PICKET FENCE ALONG BACK (Y=2.4) & LEFT (X=2.4)
      // =======================================================================
      // Horizontal Rails along Back-Right (Y = 2.4, X: 2.2 to 26.0)
      voxels.push({ x: 2.2, y: 2.3, z: 1.0, w: 24.0, d: 0.28, h: 0.28, color: PALETTE.WOOD_BARK, district: nvmeSpecimen });
      voxels.push({ x: 2.2, y: 2.3, z: 2.0, w: 24.0, d: 0.28, h: 0.28, color: PALETTE.WOOD_BARK, district: nvmeSpecimen });

      // Horizontal Rails along Back-Left (X = 2.4, Y: 2.2 to 26.0)
      voxels.push({ x: 2.3, y: 2.2, z: 1.0, w: 0.28, d: 24.0, h: 0.28, color: PALETTE.WOOD_BARK, district: nvmeSpecimen });
      voxels.push({ x: 2.3, y: 2.2, z: 2.0, w: 0.28, d: 24.0, h: 0.28, color: PALETTE.WOOD_BARK, district: nvmeSpecimen });

      // Posts along Back-Right (Y = 2.4) with Capped Tops
      const postCoordsY2 = [2.4, 7.0, 11.6, 16.2, 20.8, 25.4];
      postCoordsY2.forEach(px => {
        voxels.push({ x: px - 0.42, y: 2.0, z: 0.4, w: 0.84, d: 0.84, h: 2.5, color: PALETTE.WOOD_POST, district: nvmeSpecimen });
        voxels.push({ x: px - 0.52, y: 1.9, z: 2.9, w: 1.04, d: 1.04, h: 0.35, color: PALETTE.WOOD_HIGHLIGHT, district: nvmeSpecimen });
        voxels.push({ x: px - 0.32, y: 2.1, z: 3.25, w: 0.64, d: 0.64, h: 0.25, color: PALETTE.WOOD_HIGHLIGHT, district: nvmeSpecimen });
      });

      // Pointed Pickets along Back-Right (Y = 2.4)
      for (let px = 3.6; px <= 25.0; px += 1.15) {
        if (postCoordsY2.some(x => Math.abs(x - px) < 0.6)) continue;
        voxels.push({ x: px - 0.2, y: 2.2, z: 0.4, w: 0.40, d: 0.22, h: 2.0, color: PALETTE.WOOD_BARK, district: nvmeSpecimen });
        voxels.push({ x: px - 0.15, y: 2.22, z: 2.4, w: 0.30, d: 0.18, h: 0.32, color: PALETTE.WOOD_HIGHLIGHT, topColor: "#ffffff", district: nvmeSpecimen });
      }

      // Posts along Back-Left (X = 2.4) with Capped Tops
      const postCoordsX2 = [2.4, 7.0, 11.6, 16.2, 20.8, 25.4];
      postCoordsX2.forEach(py => {
        if (py === 2.4) return;
        voxels.push({ x: 2.0, y: py - 0.42, z: 0.4, w: 0.84, d: 0.84, h: 2.5, color: PALETTE.WOOD_POST, district: nvmeSpecimen });
        voxels.push({ x: 1.9, y: py - 0.52, z: 2.9, w: 1.04, d: 1.04, h: 0.35, color: PALETTE.WOOD_HIGHLIGHT, district: nvmeSpecimen });
        voxels.push({ x: 2.1, y: py - 0.32, z: 3.25, w: 0.64, d: 0.64, h: 0.25, color: PALETTE.WOOD_HIGHLIGHT, district: nvmeSpecimen });
      });

      // Pointed Pickets along Back-Left (X = 2.4)
      for (let py = 3.6; py <= 25.0; py += 1.15) {
        if (postCoordsX2.some(y => Math.abs(y - py) < 0.6)) continue;
        voxels.push({ x: 2.2, y: py - 0.2, z: 0.4, w: 0.22, d: 0.40, h: 2.0, color: PALETTE.WOOD_BARK, district: nvmeSpecimen });
        voxels.push({ x: 2.22, y: py - 0.15, z: 2.4, w: 0.18, d: 0.30, h: 0.32, color: PALETTE.WOOD_HIGHLIGHT, topColor: "#ffffff", district: nvmeSpecimen });
      }

      // Forest Warden Owl perched on corner fence post
      this.addWardenOwl(voxels, 2.4, 2.4, 3.5, nvmeSpecimen);

      // =======================================================================
      // C. CURVING STEPPING STONE PATH
      // =======================================================================
      const pathSteps = [
        { x: 14.0, y: 25.8, r: 1.6 },
        { x: 14.2, y: 23.4, r: 1.5 },
        { x: 14.0, y: 20.8, r: 1.6 },
        { x: 13.8, y: 18.2, r: 1.5 },
        // Stepping stone spurs out to the trees
        { x: 10.5, y: 15.0, r: 1.3 },
        { x: 8.5,  y: 13.5, r: 1.3 },
        { x: 16.5, y: 15.0, r: 1.3 },
        { x: 18.2, y: 12.0, r: 1.3 },
      ];

      pathSteps.forEach(st => {
        voxels.push({
          x: st.x - st.r / 2,
          y: st.y - st.r / 2,
          z: 0.41,
          w: st.r,
          d: st.r,
          h: 0.12,
          color: PALETTE.STONE_SLATE,
          topColor: PALETTE.STONE_WHITE,
          district: nvmeSpecimen,
        });
        voxels.push({
          x: st.x + st.r / 2 + 0.1,
          y: st.y - 0.15,
          z: 0.41,
          w: 0.65,
          d: 0.65,
          h: 0.10,
          color: PALETTE.STONE_PEBBLE,
          topColor: PALETTE.STONE_LIGHT,
        });
      });

      // Scattered resting petals on turf
      const restingPetals = [
        { x: 5.2,  y: 12.8, c: PALETTE.SAKURA_LIGHT },
        { x: 6.4,  y: 14.2, c: PALETTE.SAKURA_PALE },
        { x: 11.6, y: 7.6,  c: PALETTE.GINKGO_GOLD },
        { x: 13.2, y: 8.8,  c: PALETTE.GINKGO_LIGHT },
        { x: 7.8,  y: 19.2, c: PALETTE.PINE_SPRING },
        { x: 19.8, y: 15.4, c: PALETTE.MAPLE_RUBY },
        { x: 14.5, y: 19.5, c: PALETTE.SAKURA_LIGHT },
        { x: 12.8, y: 22.6, c: PALETTE.GINKGO_GOLD },
      ];
      restingPetals.forEach(rp => {
        voxels.push({
          x: rp.x,
          y: rp.y,
          z: 0.42,
          w: 0.38,
          d: 0.38,
          h: 0.10,
          color: rp.c,
          topColor: "#ffffff",
        });
      });

      // =======================================================================
      // D. 🪷 CENTRAL AZURE LOTUS DEW BASIN (Physical 8GB RAM Sanctuary)
      // =======================================================================
      this.addLotusBasin(voxels, 13.5, 13.5, 0.4, ramSpecimen);
      this.addWoodenSignpost(voxels, 11.2, 16.0, 0.4, "RAM", ramSpecimen);

      // Deadwood brambles if storage bloat is present
      if (this.telemetry.junkMb > 0) {
        const thornCount = Math.min(6, Math.max(2, Math.round(this.telemetry.junkMb / 30)));
        for (let t = 0; t < thornCount; t++) {
          const tx = 23.5 - (t % 3) * 1.2;
          const ty = 4.2 + Math.floor(t / 3) * 1.2;
          voxels.push({
            x: tx,
            y: ty,
            z: 0.4,
            w: 0.70,
            d: 0.70,
            h: 1.1,
            color: PALETTE.THORN_CRIMSON,
            topColor: PALETTE.THORN_RED,
            pulse: true,
            district: nvmeSpecimen,
          });
        }
      }

      // =======================================================================
      // E. MULTI-PLANT BOTANICAL GROVE (4 DISTINCT SPECIMENS IN 4 QUADRANTS)
      // =======================================================================
      // Tree 0: 🌸 Sakura Cherry Blossom (Core 0 — Top-Left)
      this.addSakuraTree(voxels, 5.5, 11.0, 0.4, 0, sakuraSpecimen);
      this.addWoodenSignpost(voxels, 7.2, 12.8, 0.4, "C0", sakuraSpecimen);

      // Tree 1: 🍂 Golden Ginkgo Tree (Core 1 — Top-Right)
      this.addGinkgoTree(voxels, 11.5, 5.5, 0.4, 1, ginkgoSpecimen);
      this.addWoodenSignpost(voxels, 13.2, 7.2, 0.4, "C1", ginkgoSpecimen);

      // Tree 2: 🌲 Emerald Jade Pine (Core 2 — Mid-Left)
      this.addJadePineTree(voxels, 6.5, 18.5, 0.4, 2, pineSpecimen);
      this.addWoodenSignpost(voxels, 8.2, 20.2, 0.4, "C2", pineSpecimen);

      // Tree 3: 🍁 Scarlet Autumn Maple (Core 3 — Mid-Right)
      this.addMapleTree(voxels, 19.5, 13.5, 0.4, 3, mapleSpecimen);
      this.addWoodenSignpost(voxels, 18.0, 15.5, 0.4, "C3", mapleSpecimen);

      // =======================================================================
      // F. 🌷 MEADOW FLORA CLUSTER (Fore-Left Lawn Corner)
      // =======================================================================
      this.addTulip(voxels, 7.5, 23.0, 0.4, PALETTE.TULIP_RED, floraSpecimen);
      this.addTulip(voxels, 9.2, 23.5, 0.4, PALETTE.TULIP_CRIMSON, floraSpecimen);
      this.addTulip(voxels, 8.2, 24.8, 0.4, PALETTE.TULIP_RED, floraSpecimen);
      this.addDandelion(voxels, 6.5, 22.5, 0.4, floraSpecimen);
      this.addDandelion(voxels, 10.2, 24.0, 0.4, floraSpecimen);
      this.addLavender(voxels, 6.8, 24.5, 0.4, floraSpecimen);
      this.addWoodenSignpost(voxels, 5.8, 25.2, 0.4, "APPS", floraSpecimen);

      // =======================================================================
      // G. 🐇 ADORABLE WHITE VOXEL BUNNY RABBIT (Thread Governor)
      // =======================================================================
      this.addBunnyRabbit(voxels, 14.0, 21.0, 0.4, bunnySpecimen);

      // =======================================================================
      // H. 🦋 FLUTTERING 3D VOXEL BUTTERFLIES
      // =======================================================================
      this.butterflies.forEach(bf => {
        this.addButterfly(voxels, bf, this.time, floraSpecimen);
      });

      // Register Precision Interactive Hit Zones per Specimen
      this.registerSpecimenZone(sakuraSpecimen, 3.5, 8.5, 8.5, 14.0);
      this.registerSpecimenZone(ginkgoSpecimen, 9.0, 3.5, 14.5, 8.5);
      this.registerSpecimenZone(pineSpecimen,   4.5, 16.0, 9.5, 21.5);
      this.registerSpecimenZone(mapleSpecimen,  16.5, 10.5, 22.5, 16.5);
      this.registerSpecimenZone(ramSpecimen,    11.0, 11.0, 16.5, 16.5);
      this.registerSpecimenZone(floraSpecimen,  5.0, 21.5, 11.5, 26.5);
      this.registerSpecimenZone(bunnySpecimen,  12.5, 19.5, 15.5, 22.5);
      this.registerSpecimenZone(nvmeSpecimen,   0.0, 0.0, 28.0, 28.0);

      // =======================================================================
      // I. DEPTH SORT & RENDER ALL VOXELS (Painter's Algorithm)
      // =======================================================================
      voxels.forEach(v => {
        v.depth = this.calcDepth(v.x + (v.w || 1) / 2, v.y + (v.d || 1) / 2, v.z);
      });

      voxels.sort((a, b) => a.depth - b.depth);

      voxels.forEach(v => {
        this.drawVoxelBlock(ctx, v);
      });

      // =======================================================================
      // J. RENDER PARTICLES & SHOCKWAVES
      // =======================================================================
      this.fallingPetals.forEach(p => {
        const proj = this.project(p.x, p.y, p.z);
        ctx.save();
        ctx.translate(proj.x, proj.y);
        ctx.rotate(p.rot);
        ctx.fillStyle = p.color;
        ctx.fillRect(-p.size / 2, -p.size / 2, p.size, p.size * 0.7);
        ctx.restore();
      });

      this.physicsVoxels.forEach(pv => {
        const proj = this.project(pv.x, pv.y, pv.z);
        ctx.fillStyle = pv.color;
        ctx.globalAlpha = Math.max(0, pv.life);
        ctx.fillRect(proj.x - pv.size / 2, proj.y - pv.size / 2, pv.size, pv.size);
        ctx.globalAlpha = 1.0;
      });

      if (this.firefliesEnabled && this.packetFlowEnabled !== false) {
        this.fireflies.forEach(f => {
          const proj = this.project(f.x, f.y, f.z);
          ctx.beginPath();
          ctx.arc(proj.x, proj.y, 2.4, 0, Math.PI * 2);
          ctx.fillStyle = f.color;
          ctx.fill();

          ctx.beginPath();
          ctx.arc(proj.x, proj.y, 5.5, 0, Math.PI * 2);
          ctx.fillStyle = f.color === PALETTE.LANTERN_CORE ? "rgba(254, 240, 138, 0.25)" : "rgba(16, 185, 129, 0.2)";
          ctx.fill();
        });
      }

      this.shockwaves.forEach(sw => {
        const proj = this.project(sw.x, sw.y, 0.4);
        ctx.beginPath();
        ctx.ellipse(proj.x, proj.y, sw.radius * this.unit * 0.7, sw.radius * this.unit * 0.35, 0, 0, Math.PI * 2);
        ctx.strokeStyle = `rgba(244, 114, 182, ${sw.alpha})`;
        ctx.lineWidth = 2.0;
        ctx.stroke();
      });
    }

    // =========================================================================
    // 8. TRUE 3D VOXEL BLOCK RASTERIZER WITH DIRECTIONAL LIGHTING
    // =========================================================================
    drawVoxelBlock(ctx, v) {
      const { x, y, z, w = 1, d = 1, h = 1, color, pulse, district } = v;

      const v000 = this.project(x, y, z);
      const v100 = this.project(x + w, y, z);
      const v110 = this.project(x + w, y + d, z);
      const v010 = this.project(x, y + d, z);

      const v001 = this.project(x, y, z + h);
      const v101 = this.project(x + w, y, z + h);
      const v111 = this.project(x + w, y + d, z + h);
      const v011 = this.project(x, y + d, z + h);

      let topCol = getShade(v.topColor || color, 1.32);
      let leftCol = getShade(color, 0.94);
      let rightCol = getShade(color, 0.70);

      if (pulse) {
        const pulseMod = 1.0 + Math.sin(this.time * 5.5) * 0.25;
        topCol = getShade(v.topColor || color, 1.32 * pulseMod);
        leftCol = getShade(color, 0.94 * pulseMod);
        rightCol = getShade(color, 0.70 * pulseMod);
      }

      const isHovered = this.hoveredDistrict && district && this.hoveredDistrict.id === district.id;
      if (isHovered) {
        topCol = getShade(v.topColor || color, 1.62);
        leftCol = getShade(color, 1.25);
        rightCol = getShade(color, 0.96);
      }

      ctx.lineWidth = 0.5;
      ctx.strokeStyle = isHovered ? "rgba(255, 255, 255, 0.35)" : "rgba(0, 0, 0, 0.14)";

      // Top Face (+Z)
      ctx.beginPath();
      ctx.moveTo(v001.x, v001.y);
      ctx.lineTo(v101.x, v101.y);
      ctx.lineTo(v111.x, v111.y);
      ctx.lineTo(v011.x, v011.y);
      ctx.closePath();
      ctx.fillStyle = topCol;
      ctx.fill();
      ctx.stroke();

      // Left Face (+Y)
      ctx.beginPath();
      ctx.moveTo(v010.x, v010.y);
      ctx.lineTo(v011.x, v011.y);
      ctx.lineTo(v111.x, v111.y);
      ctx.lineTo(v110.x, v110.y);
      ctx.closePath();
      ctx.fillStyle = leftCol;
      ctx.fill();
      ctx.stroke();

      // Right Face (+X)
      ctx.beginPath();
      ctx.moveTo(v100.x, v100.y);
      ctx.lineTo(v110.x, v110.y);
      ctx.lineTo(v111.x, v111.y);
      ctx.lineTo(v101.x, v101.y);
      ctx.closePath();
      ctx.fillStyle = rightCol;
      ctx.fill();
      ctx.stroke();
    }

    // =========================================================================
    // 9. PROCEDURAL BOTANICAL GENERATORS (Distinct Silhouette & Color per Plant)
    // =========================================================================

    // 🌸 SPECIMEN 0: SAKURA CHERRY BLOSSOM (Core 0 — Pastel Spring Pink)
    addSakuraTree(voxels, x, y, z, coreIdx, district) {
      const windSway = Math.sin(this.time * 1.6) * 0.16;

      // Always maintain authentic Sakura blossom rose palette
      const cDark = PALETTE.SAKURA_DARK;
      const cMid = PALETTE.SAKURA_MID;
      const cLight = PALETTE.SAKURA_LIGHT;
      const cPale = PALETTE.SAKURA_PALE;

      // Buttress roots
      voxels.push({ x: x - 1.0, y: y - 0.4, z: z, w: 0.6, d: 0.8, h: 0.45, color: PALETTE.WOOD_DARK, district });
      voxels.push({ x: x + 0.4, y: y - 0.4, z: z, w: 0.6, d: 0.8, h: 0.45, color: PALETTE.WOOD_DARK, district });
      voxels.push({ x: x - 0.4, y: y - 1.0, z: z, w: 0.8, d: 0.6, h: 0.45, color: PALETTE.WOOD_DARK, district });
      voxels.push({ x: x - 0.4, y: y + 0.4, z: z, w: 0.8, d: 0.6, h: 0.45, color: PALETTE.WOOD_DARK, district });

      // Cedar trunk
      voxels.push({ x: x - 0.55, y: y - 0.55, z: z, w: 1.1, d: 1.1, h: 1.8, color: PALETTE.WOOD_DARK, district });
      voxels.push({ x: x - 0.45, y: y - 0.45, z: z + 1.8, w: 0.9, d: 0.9, h: 1.8, color: PALETTE.WOOD_BARK, district });
      voxels.push({ x: x - 0.35, y: y - 0.35, z: z + 3.6, w: 0.7, d: 0.7, h: 1.4, color: PALETTE.WOOD_MID, district });

      // Branch forks
      voxels.push({ x: x - 1.2, y: y - 0.3, z: z + 4.0, w: 1.0, d: 0.6, h: 0.6, color: PALETTE.WOOD_BRANCH, district });
      voxels.push({ x: x + 0.2, y: y - 1.2, z: z + 4.0, w: 0.6, d: 1.0, h: 0.6, color: PALETTE.WOOD_BRANCH, district });
      voxels.push({ x: x + 0.3, y: y + 0.2, z: z + 4.2, w: 1.0, d: 0.6, h: 0.6, color: PALETTE.WOOD_BRANCH, district });
      voxels.push({ x: x - 0.3, y: y + 0.3, z: z + 4.2, w: 0.6, d: 1.0, h: 0.6, color: PALETTE.WOOD_BRANCH, district });

      // Volumetric Rounded Blossom Cloud Canopy (Classic Sakura Dome)
      const sx = x + windSway;
      voxels.push({ x: sx - 2.0, y: y - 2.0, z: z + 4.6, w: 4.0, d: 4.0, h: 0.8, color: cDark, district });
      voxels.push({ x: sx - 2.4, y: y - 2.4, z: z + 5.4, w: 4.8, d: 4.8, h: 1.5, color: cMid, district });
      // Fluffy stepped perimeter lobes
      voxels.push({ x: sx - 2.8, y: y - 1.0, z: z + 5.6, w: 0.5, d: 2.0, h: 1.0, color: cMid, district });
      voxels.push({ x: sx + 2.3, y: y - 1.0, z: z + 5.6, w: 0.5, d: 2.0, h: 1.0, color: cMid, district });
      voxels.push({ x: sx - 1.0, y: y - 2.8, z: z + 5.6, w: 2.0, d: 0.5, h: 1.0, color: cMid, district });
      voxels.push({ x: sx - 1.0, y: y + 2.3, z: z + 5.6, w: 2.0, d: 0.5, h: 1.0, color: cMid, district });
      // Upper sunlight dome
      voxels.push({ x: sx - 1.8, y: y - 1.8, z: z + 6.9, w: 3.6, d: 3.6, h: 1.1, color: cLight, topColor: cPale, district });
      // Crown peak
      voxels.push({ x: sx - 1.0, y: y - 1.0, z: z + 8.0, w: 2.0, d: 2.0, h: 0.65, color: cPale, topColor: PALETTE.SAKURA_WHITE, district });
    }

    // 🍂 SPECIMEN 1: GOLDEN GINKGO TREE (Core 1 — Warm Amber Gold)
    addGinkgoTree(voxels, x, y, z, coreIdx, district) {
      const windSway = Math.sin(this.time * 1.5 + 1.0) * 0.15;

      const cDark = PALETTE.GINKGO_DARK;
      const cMid = PALETTE.GINKGO_MID;
      const cLight = PALETTE.GINKGO_LIGHT;
      const cGold = PALETTE.GINKGO_GOLD;
      const cPale = PALETTE.GINKGO_PALE;

      // Tall straight walnut trunk
      voxels.push({ x: x - 0.5, y: y - 0.5, z: z, w: 1.0, d: 1.0, h: 2.2, color: PALETTE.WOOD_DARK, district });
      voxels.push({ x: x - 0.4, y: y - 0.4, z: z + 2.2, w: 0.8, d: 0.8, h: 2.2, color: PALETTE.WOOD_BARK, district });
      voxels.push({ x: x - 0.3, y: y - 0.3, z: z + 4.4, w: 0.6, d: 0.6, h: 1.8, color: PALETTE.WOOD_MID, district });

      // Steep upward branch knuckles
      voxels.push({ x: x - 0.7, y: y - 0.7, z: z + 4.6, w: 0.5, d: 0.5, h: 1.1, color: PALETTE.WOOD_BRANCH, district });
      voxels.push({ x: x + 0.2, y: y + 0.2, z: z + 4.6, w: 0.5, d: 0.5, h: 1.1, color: PALETTE.WOOD_BRANCH, district });

      // Conical Fan-Shaped Ginkgo Foliage Spire
      const sx = x + windSway;
      voxels.push({ x: sx - 1.8, y: y - 1.8, z: z + 4.0, w: 3.6, d: 3.6, h: 1.0, color: cDark, district });
      voxels.push({ x: sx - 2.1, y: y - 0.8, z: z + 4.3, w: 4.2, d: 1.6, h: 0.8, color: cMid, district });
      voxels.push({ x: sx - 1.6, y: y - 1.6, z: z + 5.0, w: 3.2, d: 3.2, h: 1.5, color: cLight, topColor: cGold, district });
      voxels.push({ x: sx - 0.8, y: y - 2.0, z: z + 5.3, w: 1.6, d: 4.0, h: 0.9, color: cGold, district });
      voxels.push({ x: sx - 1.2, y: y - 1.2, z: z + 6.5, w: 2.4, d: 2.4, h: 1.4, color: cGold, topColor: cPale, district });
      voxels.push({ x: sx - 0.6, y: y - 0.6, z: z + 7.9, w: 1.2, d: 1.2, h: 1.0, color: cPale, topColor: "#ffffff", district });
      voxels.push({ x: sx - 0.3, y: y - 0.3, z: z + 8.9, w: 0.6, d: 0.6, h: 0.6, color: cPale, topColor: "#ffffff", district });
    }

    // 🌲 SPECIMEN 2: EMERALD JADE PINE / BONSAI (Core 2 — Rich Evergreen)
    addJadePineTree(voxels, x, y, z, coreIdx, district) {
      const windSway = Math.sin(this.time * 1.3 + 2.0) * 0.12;

      const cDark = PALETTE.PINE_DARK;
      const cMid = PALETTE.PINE_MID;
      const cLight = PALETTE.PINE_LIGHT;
      const cEmerald = PALETTE.PINE_EMERALD;
      const cSpring = PALETTE.PINE_SPRING;

      // Gnarled Bonsai Trunk with Elbow Bends
      voxels.push({ x: x - 0.55, y: y - 0.45, z: z, w: 1.1, d: 0.9, h: 1.5, color: PALETTE.WOOD_DARK, district });
      voxels.push({ x: x - 0.8, y: y - 0.35, z: z + 1.5, w: 1.0, d: 0.8, h: 1.4, color: PALETTE.WOOD_BARK, district });
      voxels.push({ x: x - 1.6, y: y - 0.25, z: z + 2.5, w: 1.1, d: 0.5, h: 0.5, color: PALETTE.WOOD_BRANCH, district });
      voxels.push({ x: x - 0.45, y: y - 0.25, z: z + 2.9, w: 0.8, d: 0.7, h: 1.5, color: PALETTE.WOOD_BARK, district });
      voxels.push({ x: x + 0.25, y: y - 0.25, z: z + 4.0, w: 1.1, d: 0.5, h: 0.5, color: PALETTE.WOOD_BRANCH, district });
      voxels.push({ x: x - 0.35, y: y - 0.25, z: z + 4.4, w: 0.6, d: 0.6, h: 1.3, color: PALETTE.WOOD_MID, district });

      const sx = x + windSway;

      // Terrace 1: Lower Horizontal Needle Plate
      voxels.push({ x: sx - 2.5, y: y - 1.3, z: z + 2.7, w: 2.2, d: 2.0, h: 0.45, color: cDark, district });
      voxels.push({ x: sx - 2.3, y: y - 1.1, z: z + 3.15, w: 1.8, d: 1.6, h: 0.55, color: cMid, topColor: cEmerald, district });
      voxels.push({ x: sx - 1.9, y: y - 0.8, z: z + 3.7, w: 1.1, d: 1.1, h: 0.35, color: cEmerald, topColor: cSpring, district });

      // Terrace 2: Mid Horizontal Needle Plate
      voxels.push({ x: sx + 0.3, y: y - 1.2, z: z + 4.2, w: 2.0, d: 1.8, h: 0.45, color: cDark, district });
      voxels.push({ x: sx + 0.5, y: y - 1.0, z: z + 4.65, w: 1.6, d: 1.4, h: 0.55, color: cMid, topColor: cEmerald, district });
      voxels.push({ x: sx + 0.8, y: y - 0.7, z: z + 5.2, w: 1.1, d: 0.9, h: 0.35, color: cEmerald, topColor: cSpring, district });

      // Terrace 3: Crown Pagoda Terrace
      voxels.push({ x: sx - 1.4, y: y - 1.4, z: z + 5.5, w: 2.4, d: 2.4, h: 0.5, color: cDark, district });
      voxels.push({ x: sx - 1.2, y: y - 1.2, z: z + 6.0, w: 2.0, d: 2.0, h: 0.7, color: cLight, topColor: cEmerald, district });
      voxels.push({ x: sx - 0.7, y: y - 0.7, z: z + 6.7, w: 1.3, d: 1.3, h: 0.45, color: cEmerald, topColor: cSpring, district });
    }

    // 🍁 SPECIMEN 3: SCARLET AUTUMN MAPLE (Core 3 — Fiery Japanese Momiji Crimson)
    addMapleTree(voxels, x, y, z, coreIdx, district) {
      const windSway = Math.sin(this.time * 1.4 + 3.0) * 0.16;

      const cDark = PALETTE.MAPLE_DARK;
      const cMid = PALETTE.MAPLE_MID;
      const cLight = PALETTE.MAPLE_LIGHT;
      const cRuby = PALETTE.MAPLE_RUBY;
      const cFlame = PALETTE.MAPLE_FLAME;

      // Charcoal Birch Trunk
      voxels.push({ x: x - 0.5, y: y - 0.5, z: z, w: 1.0, d: 1.0, h: 1.8, color: PALETTE.WOOD_DARK, district });
      voxels.push({ x: x - 0.45, y: y - 0.45, z: z + 1.8, w: 0.9, d: 0.9, h: 1.6, color: PALETTE.WOOD_BARK, district });

      // Spreading branch forks
      voxels.push({ x: x - 1.2, y: y - 0.7, z: z + 3.3, w: 1.0, d: 0.5, h: 0.5, color: PALETTE.WOOD_BRANCH, district });
      voxels.push({ x: x + 0.3, y: y - 0.7, z: z + 3.3, w: 1.0, d: 0.5, h: 0.5, color: PALETTE.WOOD_BRANCH, district });
      voxels.push({ x: x - 0.7, y: y + 0.3, z: z + 3.5, w: 0.5, d: 1.0, h: 0.5, color: PALETTE.WOOD_BRANCH, district });
      voxels.push({ x: x + 0.2, y: y + 0.3, z: z + 3.5, w: 0.5, d: 1.0, h: 0.5, color: PALETTE.WOOD_BRANCH, district });

      const sx = x + windSway;

      // Cascading Spreading Scarlet Umbrella Canopy
      voxels.push({ x: sx - 2.0, y: y - 2.0, z: z + 3.8, w: 4.0, d: 4.0, h: 0.7, color: cDark, district });
      voxels.push({ x: sx - 2.3, y: y - 2.3, z: z + 4.5, w: 4.6, d: 4.6, h: 1.4, color: cMid, district });
      // Drooping perimeter lobes
      voxels.push({ x: sx - 2.7, y: y - 1.4, z: z + 4.2, w: 0.5, d: 2.8, h: 0.9, color: cMid, district });
      voxels.push({ x: sx + 2.2, y: y - 1.4, z: z + 4.2, w: 0.5, d: 2.8, h: 0.9, color: cMid, district });
      voxels.push({ x: sx - 1.4, y: y - 2.7, z: z + 4.2, w: 2.8, d: 0.5, h: 0.9, color: cMid, district });
      voxels.push({ x: sx - 1.4, y: y + 2.2, z: z + 4.2, w: 2.8, d: 0.5, h: 0.9, color: cMid, district });
      // Upper vibrant scarlet layers
      voxels.push({ x: sx - 1.6, y: y - 1.6, z: z + 5.9, w: 3.2, d: 3.2, h: 1.1, color: cLight, topColor: cRuby, district });
      voxels.push({ x: sx - 0.9, y: y - 0.9, z: z + 7.0, w: 1.8, d: 1.8, h: 0.7, color: cRuby, topColor: cFlame, district });
    }

    // 🪷 SPECIMEN 4: AZURE LOTUS DEW BASIN (RAM)
    addLotusBasin(voxels, x, y, z, district) {
      // Outer carved stone rim (5.2 x 4.6)
      voxels.push({ x: x - 2.6, y: y - 2.3, z: z + 0.01, w: 5.2, d: 4.6, h: 0.16, color: PALETTE.STONE_MID, topColor: PALETTE.STONE_PEBBLE, district });
      voxels.push({ x: x - 2.3, y: y - 2.0, z: z + 0.03, w: 4.6, d: 4.0, h: 0.12, color: PALETTE.STONE_LIGHT, topColor: PALETTE.STONE_SLATE, district });

      // Shimmering Crystal Azure Water Surface
      voxels.push({
        x: x - 2.0,
        y: y - 1.7,
        z: z + 0.05,
        w: 4.0,
        d: 3.4,
        h: 0.08,
        color: PALETTE.WATER_MID,
        topColor: PALETTE.WATER_SURFACE,
        district
      });

      // Animated water ripples
      const ripAnim = Math.sin(this.time * 2.5) * 0.1;
      voxels.push({
        x: x - 1.0 + ripAnim,
        y: y - 0.7,
        z: z + 0.12,
        w: 1.6,
        d: 1.2,
        h: 0.04,
        color: PALETTE.WATER_RIPPLE,
        topColor: PALETTE.WATER_FOAM,
        district
      });

      // Floating Green Lily Pads
      voxels.push({ x: x - 1.4, y: y - 1.0, z: z + 0.14, w: 1.1, d: 1.1, h: 0.05, color: PALETTE.LILY_PAD, topColor: "#4ade80", district });
      voxels.push({ x: x + 0.7, y: y + 0.4, z: z + 0.14, w: 1.0, d: 1.0, h: 0.05, color: PALETTE.LILY_PAD, topColor: "#4ade80", district });
      voxels.push({ x: x - 0.5, y: y + 0.8, z: z + 0.14, w: 0.9, d: 0.9, h: 0.05, color: PALETTE.LILY_PAD, topColor: "#4ade80", district });

      // 3D Blooming Water Lotus 1 (North-East in Basin)
      this.addWaterLotusFlower(voxels, x + 0.8, y - 0.6, z + 0.15, district);

      // 3D Blooming Water Lotus 2 (South-West in Basin)
      this.addWaterLotusFlower(voxels, x - 1.0, y + 0.3, z + 0.15, district);

      // Drifting Petals in the water
      voxels.push({ x: x - 0.2, y: y - 1.2, z: z + 0.14, w: 0.38, d: 0.38, h: 0.04, color: PALETTE.SAKURA_LIGHT, topColor: PALETTE.SAKURA_PALE, district });
      voxels.push({ x: x + 1.1, y: y - 1.0, z: z + 0.14, w: 0.38, d: 0.38, h: 0.04, color: PALETTE.GINKGO_GOLD, topColor: "#ffffff", district });
    }

    addWaterLotusFlower(voxels, x, y, z, district) {
      voxels.push({ x: x - 0.4, y: y - 0.15, z: z, w: 0.3, d: 0.3, h: 0.25, color: PALETTE.LOTUS_WHITE, topColor: PALETTE.LOTUS_PINK, district });
      voxels.push({ x: x + 0.1, y: y - 0.15, z: z, w: 0.3, d: 0.3, h: 0.25, color: PALETTE.LOTUS_WHITE, topColor: PALETTE.LOTUS_PINK, district });
      voxels.push({ x: x - 0.15, y: y - 0.4, z: z, w: 0.3, d: 0.3, h: 0.25, color: PALETTE.LOTUS_WHITE, topColor: PALETTE.LOTUS_PINK, district });
      voxels.push({ x: x - 0.15, y: y + 0.1, z: z, w: 0.3, d: 0.3, h: 0.25, color: PALETTE.LOTUS_WHITE, topColor: PALETTE.LOTUS_PINK, district });
      // Golden Central Pistil
      voxels.push({ x: x - 0.15, y: y - 0.15, z: z + 0.1, w: 0.3, d: 0.3, h: 0.28, color: PALETTE.LOTUS_GOLD, topColor: "#ffffff", pulse: true, district });
    }

    // 🏷️ 3D VOXEL WOODEN SIGNPOST (Identification Tier 1)
    addWoodenSignpost(voxels, x, y, z, label, district) {
      // Vertical Cedar Stake
      voxels.push({ x: x - 0.14, y: y - 0.14, z: z, w: 0.28, d: 0.28, h: 1.1, color: PALETTE.SIGN_POST, district });
      // Carved Horizontal Timber Plaque
      voxels.push({
        x: x - 0.55,
        y: y - 0.12,
        z: z + 0.85,
        w: 1.1,
        d: 0.24,
        h: 0.55,
        color: PALETTE.SIGN_PLAQUE,
        topColor: PALETTE.SIGN_PLAQUE_LIGHT,
        district
      });
      // Carved Inscription Plate
      voxels.push({
        x: x - 0.45,
        y: y - 0.14,
        z: z + 0.95,
        w: 0.9,
        d: 0.08,
        h: 0.32,
        color: PALETTE.SIGN_TEXT,
        district
      });
    }

    // 🐇 ADORABLE WHITE VOXEL BUNNY (Governor)
    addBunnyRabbit(voxels, x, y, z, district) {
      const bob = Math.sin(this.time * 3.5) * 0.05;
      const earWiggle = Math.sin(this.time * 6.5) * 0.08;

      // Lower body / hind paws
      voxels.push({ x: x - 0.75, y: y - 0.65, z: z, w: 1.5, d: 1.4, h: 0.50, color: PALETTE.BUNNY_SHADOW, district });
      // Main rounded body
      voxels.push({ x: x - 0.65, y: y - 0.6, z: z + 0.45 + bob, w: 1.3, d: 1.3, h: 1.05, color: PALETTE.BUNNY_WHITE, district });
      // Front paws resting forward
      voxels.push({ x: x - 0.55, y: y + 0.55, z: z + 0.1, w: 0.42, d: 0.42, h: 0.40, color: PALETTE.BUNNY_WHITE, district });
      voxels.push({ x: x + 0.13, y: y + 0.55, z: z + 0.1, w: 0.42, d: 0.42, h: 0.40, color: PALETTE.BUNNY_WHITE, district });
      // Fluffy cotton tail
      voxels.push({ x: x - 0.25, y: y - 0.95, z: z + 0.5 + bob, w: 0.5, d: 0.45, h: 0.48, color: PALETTE.BUNNY_WHITE, district });

      // Head
      voxels.push({ x: x - 0.6, y: y + 0.25, z: z + 0.95 + bob, w: 1.2, d: 1.2, h: 1.1, color: PALETTE.BUNNY_WHITE, district });

      // Black voxel eyes
      voxels.push({ x: x - 0.48, y: y + 1.35, z: z + 1.4 + bob, w: 0.26, d: 0.12, h: 0.28, color: PALETTE.BUNNY_EYES, district });
      voxels.push({ x: x + 0.22, y: y + 1.35, z: z + 1.4 + bob, w: 0.26, d: 0.12, h: 0.28, color: PALETTE.BUNNY_EYES, district });

      // Pink nose
      voxels.push({ x: x - 0.14, y: y + 1.38, z: z + 1.15 + bob, w: 0.28, d: 0.12, h: 0.18, color: PALETTE.BUNNY_NOSE, district });

      // Rosy cheeks
      voxels.push({ x: x - 0.56, y: y + 1.15, z: z + 1.12 + bob, w: 0.20, d: 0.22, h: 0.22, color: PALETTE.BUNNY_EAR_PINK, district });
      voxels.push({ x: x + 0.36, y: y + 1.15, z: z + 1.12 + bob, w: 0.20, d: 0.22, h: 0.22, color: PALETTE.BUNNY_EAR_PINK, district });

      // Left upright ear
      voxels.push({ x: x - 0.50 + earWiggle, y: y + 0.5, z: z + 2.05 + bob, w: 0.40, d: 0.40, h: 1.55, color: PALETTE.BUNNY_WHITE, district });
      voxels.push({ x: x - 0.45 + earWiggle, y: y + 0.82, z: z + 2.15 + bob, w: 0.30, d: 0.10, h: 1.25, color: PALETTE.BUNNY_EAR_PINK, district });

      // Right upright ear
      voxels.push({ x: x + 0.10 - earWiggle, y: y + 0.5, z: z + 2.05 + bob, w: 0.40, d: 0.40, h: 1.55, color: PALETTE.BUNNY_WHITE, district });
      voxels.push({ x: x + 0.15 - earWiggle, y: y + 0.82, z: z + 2.15 + bob, w: 0.30, d: 0.10, h: 1.25, color: PALETTE.BUNNY_EAR_PINK, district });
    }

    // 🦋 FLUTTERING 3D BUTTERFLY
    addButterfly(voxels, bf, time, district) {
      const angle = time * bf.speed + bf.phase;
      const x = bf.baseX + Math.cos(angle) * bf.radius;
      const y = bf.baseY + Math.sin(angle * 1.3) * (bf.radius * 0.7);
      const z = bf.baseZ + Math.sin(time * 2.5 + bf.phase) * 0.5;

      voxels.push({ x: x - 0.15, y: y - 0.3, z: z, w: 0.3, d: 0.6, h: 0.25, color: PALETTE.BUTTERFLY_BODY, district });

      const flap = Math.sin(time * 16.0 + bf.phase) * 0.35;
      voxels.push({ x: x - 0.75, y: y - 0.4, z: z + 0.15 + flap, w: 0.6, d: 0.8, h: 0.08, color: bf.color, topColor: "#ffffff", district });
      voxels.push({ x: x + 0.15, y: y - 0.4, z: z + 0.15 + flap, w: 0.6, d: 0.8, h: 0.08, color: bf.color, topColor: "#ffffff", district });
    }

    addTulip(voxels, x, y, z, petalColor, district) {
      voxels.push({ x: x - 0.2, y: y - 0.2, z: z, w: 0.4, d: 0.4, h: 1.6, color: PALETTE.TULIP_STEM, district });
      voxels.push({ x: x - 0.6, y: y - 0.25, z: z + 0.4, w: 0.5, d: 0.45, h: 0.6, color: PALETTE.TULIP_STEM, district });
      voxels.push({ x: x + 0.15, y: y + 0.15, z: z + 0.5, w: 0.5, d: 0.45, h: 0.6, color: PALETTE.TULIP_STEM, district });
      voxels.push({ x: x - 0.55, y: y - 0.55, z: z + 1.6, w: 1.1, d: 1.1, h: 1.1, color: petalColor, topColor: PALETTE.TULIP_LIGHT, district });
      voxels.push({ x: x - 0.2, y: y - 0.2, z: z + 2.5, w: 0.4, d: 0.4, h: 0.25, color: PALETTE.DANDY_GOLD, district });
    }

    addDandelion(voxels, x, y, z, district) {
      voxels.push({ x: x - 0.15, y: y - 0.15, z: z, w: 0.3, d: 0.3, h: 1.0, color: PALETTE.TULIP_STEM, district });
      voxels.push({ x: x - 0.55, y: y - 0.55, z: z + 1.0, w: 1.1, d: 1.1, h: 0.9, color: PALETTE.DANDY_GOLD, topColor: PALETTE.DANDY_LIGHT, district });
      voxels.push({ x: x - 0.35, y: y - 0.35, z: z + 1.8, w: 0.7, d: 0.7, h: 0.3, color: PALETTE.DANDY_LIGHT, district });
    }

    addLavender(voxels, x, y, z, district) {
      voxels.push({ x: x - 0.15, y: y - 0.15, z: z, w: 0.3, d: 0.3, h: 1.8, color: PALETTE.TULIP_STEM, district });
      voxels.push({ x: x - 0.4, y: y - 0.4, z: z + 0.8, w: 0.8, d: 0.8, h: 1.2, color: PALETTE.LAVENDER_PURPLE, topColor: PALETTE.LAVENDER_LILAC, district });
      voxels.push({ x: x - 0.25, y: y - 0.25, z: z + 1.9, w: 0.5, d: 0.5, h: 0.5, color: PALETTE.LAVENDER_LILAC, district });
    }

    addWardenOwl(voxels, x, y, z, district) {
      const bobZ = z + Math.sin(this.time * 2.0) * 0.08;
      voxels.push({ x: x - 0.4, y: y - 0.4, z: bobZ, w: 0.8, d: 0.8, h: 1.1, color: PALETTE.WOOD_DARK, district });
      voxels.push({ x: x - 0.35, y: y - 0.35, z: bobZ + 1.1, w: 0.7, d: 0.7, h: 0.7, color: PALETTE.WOOD_BARK, district });
      voxels.push({ x: x - 0.25, y: y + 0.35, z: bobZ + 1.3, w: 0.2, d: 0.08, h: 0.22, color: PALETTE.LANTERN_CORE, pulse: true, district });
      voxels.push({ x: x + 0.08, y: y + 0.35, z: bobZ + 1.3, w: 0.2, d: 0.08, h: 0.22, color: PALETTE.LANTERN_CORE, pulse: true, district });
      voxels.push({ x: x - 0.08, y: y + 0.38, z: bobZ + 1.2, w: 0.16, d: 0.1, h: 0.16, color: PALETTE.OWL_BEAK, district });
    }

    // =========================================================================
    // 10. HIT DETECTION & INTERACTION ZONES
    // =========================================================================
    registerSpecimenZone(district, minX, minY, maxX, maxY) {
      const p1 = this.project(minX, minY, 0);
      const p2 = this.project(maxX, minY, 0);
      const p3 = this.project(maxX, maxY, 0);
      const p4 = this.project(minX, maxY, 0);

      this.hitZones.push({
        district,
        points: [p1, p2, p3, p4],
      });
    }

    checkHover(mx, my) {
      const prev = this.hoveredDistrict;
      this.hoveredDistrict = this.findHitDistrict(mx, my);
      if (this.hoveredDistrict) {
        this.hoverPoint = { x: mx, y: my };
      } else {
        this.hoverPoint = null;
      }
      if (prev !== this.hoveredDistrict && this.onDistrictHover) {
        this.onDistrictHover(this.hoveredDistrict);
      }
    }

    findHitDistrict(mx, my) {
      for (let i = 0; i < this.hitZones.length; i++) {
        const zone = this.hitZones[i];
        if (this.pointInPolygon(mx, my, zone.points)) {
          return zone.district;
        }
      }
      return null;
    }

    pointInPolygon(x, y, pts) {
      let inside = false;
      for (let i = 0, j = pts.length - 1; i < pts.length; j = i++) {
        const xi = pts[i].x, yi = pts[i].y;
        const xj = pts[j].x, yj = pts[j].y;
        const intersect = ((yi > y) !== (yj > y)) && (x < (xj - xi) * (y - yi) / (yj - yi) + xi);
        if (intersect) inside = !inside;
      }
      return inside;
    }

    // =========================================================================
    // 11. IN-WORLD FLOATING IDENTIFICATION BADGES (Identification Tier 2)
    // =========================================================================
    drawPlantTags(ctx) {
      if (!this.specimens) return;

      ctx.save();
      ctx.font = "bold 9px system-ui, -apple-system, sans-serif";

      this.specimens.forEach(sp => {
        if (sp.id === "plant-nvme") return;

        const proj = this.project(sp.worldX, sp.worldY, sp.worldZ);
        const text = sp.tag;
        const textW = ctx.measureText(text).width;
        const pillW = textW + 16;
        const pillH = 18;
        const pillX = proj.x - pillW / 2;
        const pillY = proj.y - pillH / 2;

        const isHovered = this.hoveredDistrict && this.hoveredDistrict.id === sp.id;

        // Anchor tick pointing down to the specimen canopy
        ctx.beginPath();
        ctx.moveTo(proj.x, pillY + pillH);
        ctx.lineTo(proj.x, pillY + pillH + 5);
        ctx.strokeStyle = isHovered ? sp.badgeColor : "rgba(255, 255, 255, 0.4)";
        ctx.lineWidth = 1;
        ctx.stroke();

        // Glassmorphic tag pill
        ctx.fillStyle = isHovered ? "rgba(10, 15, 12, 0.96)" : "rgba(15, 23, 20, 0.88)";
        ctx.strokeStyle = isHovered ? sp.badgeColor : "rgba(255, 255, 255, 0.28)";
        ctx.lineWidth = isHovered ? 1.5 : 1;

        ctx.beginPath();
        ctx.roundRect(pillX, pillY, pillW, pillH, 9);
        ctx.fill();
        ctx.stroke();

        // Tag label
        ctx.fillStyle = isHovered ? "#ffffff" : "rgba(240, 248, 245, 0.95)";
        ctx.fillText(text, pillX + 8, pillY + 12);
      });

      ctx.restore();
    }

    // =========================================================================
    // 12. RICH CURSOR-TRACKING BOTANICAL INSPECTOR CARD (Identification Tier 3)
    // =========================================================================
    drawHoverHud(ctx, pt, d) {
      const bw = 290, bh = 86, pad = 12;
      const px = Math.min(this.width - bw - pad, Math.max(pad, pt.x + 14));
      const py = Math.min(this.height - bh - pad, Math.max(pad, pt.y - bh - 8));

      ctx.save();

      // Deep dark glassmorphism card
      ctx.shadowColor = "rgba(0, 0, 0, 0.85)";
      ctx.shadowBlur = 24;
      ctx.fillStyle = "rgba(11, 16, 14, 0.97)";
      ctx.strokeStyle = d.badgeColor || "rgba(244, 114, 182, 0.6)";
      ctx.lineWidth = 1.5;

      ctx.beginPath();
      ctx.roundRect(px, py, bw, bh, 8);
      ctx.fill();
      ctx.stroke();
      ctx.restore();

      // Header: Specimen Common Name
      ctx.fillStyle = "#ffffff";
      ctx.font = "bold 11px system-ui, -apple-system, sans-serif";
      ctx.fillText(d.name, px + 12, py + 18);

      // Subtitle: Scientific Name & Hardware Component
      ctx.fillStyle = d.badgeColor || PALETTE.SAKURA_LIGHT;
      ctx.font = "9px monospace";
      const sub = d.component || d.scientific || "";
      ctx.fillText(sub, px + 12, py + 33);

      // Metric & Health Bar
      ctx.fillStyle = "#94a3b8";
      ctx.font = "9px system-ui, -apple-system, sans-serif";
      ctx.fillText(d.stat || "", px + 12, py + 48);

      // Botanical Ecological Description
      ctx.fillStyle = "#cbd5e1";
      ctx.font = "8.5px system-ui, -apple-system, sans-serif";
      ctx.fillText(d.desc || "", px + 12, py + 63);

      // Interactive Click Prompt
      ctx.fillStyle = "rgba(148, 163, 184, 0.75)";
      ctx.font = "italic 8px system-ui, -apple-system, sans-serif";
      ctx.fillText(d.action || "Click plant to inspect telemetry in deck", px + 12, py + 77);
    }

    drawFooterHud(ctx) {
      ctx.save();

      const blText = "🌸 SAKURA (C0) • 🍂 GINKGO (C1) • 🌲 PINE (C2) • 🍁 MAPLE (C3) • 🪷 8GB DEW BASIN";
      ctx.font = "9px monospace";
      const blW = ctx.measureText(blText).width + 22;
      const pillY = this.height - 28;

      ctx.fillStyle = "rgba(16, 24, 20, 0.88)";
      ctx.strokeStyle = "rgba(244, 114, 182, 0.25)";
      ctx.lineWidth = 1;

      ctx.beginPath();
      ctx.roundRect(16, pillY, blW, 20, 10);
      ctx.fill();
      ctx.stroke();

      ctx.fillStyle = PALETTE.SAKURA_LIGHT;
      ctx.fillText(blText, 27, pillY + 13);

      const brText = "ORBIT: DRAG • ZOOM: WHEEL • HOVER: IDENTIFY • CLICK: ISOLATE";
      const brW = ctx.measureText(brText).width + 22;
      const brX = this.width - brW - 16;

      ctx.beginPath();
      ctx.roundRect(brX, pillY, brW, 20, 10);
      ctx.fill();
      ctx.stroke();

      ctx.fillStyle = "rgba(203, 213, 225, 0.85)";
      ctx.fillText(brText, brX + 11, pillY + 13);

      ctx.restore();
    }
  }

  window.VoxelMotherboardEngine = VoxelMotherboardEngine;

})(window);
