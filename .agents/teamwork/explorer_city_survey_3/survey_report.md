# Technical Architecture & Specification Report: Frontend Visualizer, Real-Time Streaming, Persistence & Tooling (R3, R4, AC)

**Author**: `explorer_city_survey_3` (teamwork_preview_explorer)  
**Parent Orchestrator**: `orchestrator_2` (`d8f49c97-82ba-4295-8de9-17407789baa2`)  
**Target Project**: `c:\Users\ignaz\antigravity\keen-franklin\agent_city`  
**Timestamp**: 2026-09-30T16:49:00Z  
**Status**: Complete Architectural Specification  

---

## 1. Executive Summary & Problem Boundary

### 1.1 Objective & Scope
This report establishes the complete technical specification and architectural blueprint for the presentation, real-time streaming, state persistence, and operational tooling layers of **AgentCity** — an evolving virtual city multi-agent simulation. Specifically, this report covers:
- **Requirement 3 (R3)**: Expressive Adaptive SVG & Vanilla JS Visualizer.
- **Requirement 4 (R4)**: Real-Time Streaming & State Persistence.
- **Acceptance Criteria (AC)**: Interactive user controls, live streaming dialogue and events, automated testing hooks, and cross-platform one-click launcher scripts.

### 1.2 Core Architectural Principles
1. **Zero External Frontend Dependencies**: The entire web dashboard operates with **zero npm packages, zero build tools (Webpack/Vite), and zero CDN imports** (no React, no Vue, no D3.js, no Chart.js, no Tailwind, no external icon sets). It leverages 100% native Web standards: HTML5 semantic elements, modern CSS3 (Custom Properties, Flexbox, Grid, Glassmorphic backdrop filters), ES6+ JavaScript modules, and programmatic inline SVG / Canvas rendering.
2. **Low-Latency Differential Streaming**: State updates between the Python backend and connected web clients stream over WebSockets (`/ws`) utilizing a differential delta protocol (`TICK_DELTA`). Only changed agent coordinates, evolving buildings, new dialogue messages, and macro metrics are broadcast each tick, keeping payloads under 1.5 KB and CPU utilization minimal.
3. **Hardware Agility & 60 FPS Animation**: Simulation tick logic (1-2 Hz) is strictly decoupled from browser presentation (60 Hz). A custom Linear Interpolation (LERP) motion engine smoothly slides agents across grid coordinates using `requestAnimationFrame`, ensuring fluid visual feedback even on low-TDP quad-core processors (e.g., Intel N100 / 8GB RAM).
4. **Dual Projection Flexibility**: The visualizer incorporates a dual projection engine: a rich 2.5D Isometric view with depth sorting (`x + y`), and a crisp Orthographic 2D Top-Down view, toggled instantly via user controls.
5. **Deterministic State Persistence**: Full simulation state is preserved via SQLite with Write-Ahead Logging (WAL) and portable JSON snapshots, enabling seamless pause, resume, snapshot loading, and headless execution.

---

## 2. Dependency-Free Web Dashboard Architecture

### 2.1 File Organization & Modular Structure
All frontend assets reside in `agent_city/static/` and are served directly by FastAPI's static file handler (`app.mount("/", StaticFiles(directory="agent_city/static", html=True))`):

```
agent_city/static/
├── index.html              # Semantic HTML5 single-page application structure
├── css/
│   └── style.css           # Glassmorphic cyber-civic design system, layout, animations
└── js/
    ├── app.js              # Application coordinator, WebSocket/REST client, state cache, UI events
    ├── renderer.js         # Programmatic SVG visualizer (grid, zoning, roads, buildings, lighting)
    ├── agent_view.js       # Agent avatars, LERP movement interpolator, badges, dialogue bubbles, halos
    └── charts.js           # Pure SVG & Canvas real-time demographic, economic, and vitals time-series
```

### 2.2 UI Layout & Visual Wireframe
The dashboard employs a 3-column responsive layout framed by an upper HUD and an interactive slide-out inspector drawer:

```
+---------------------------------------------------------------------------------------------------------+
| [LOGO: AGENT CITY] | Tick: 0142 | Epoch: 2 | ☀️ 14:30 | 👥 Pop: 14 (8+6) | 💰 $18,450 | [⏸ Play/Pause] [⏩ 2x] |
+------------------------------------+------------------------------------+-------------------------------+
| LEFT PANEL: VITALS & CHARTS        | CENTER VIEWPORT: LIVING CITY MAP   | RIGHT PANEL: LIVE FEED        |
| - Population & Subagents (Canvas)  |                                    | - Filter: [All] [Chat] [Build]|
| - Treasury & Energy Sparklines     |  [ Isometric / Top-Down Toggle ]   | ----------------------------- |
| - Zoning Distribution Donut (SVG)  |  [ Zoom + / - ] [ Reset View ]     | 14:30 [Mayor]: Zoning dist 3! |
| - Public vs Private Wealth Bar     |                                    | 14:29 [Builder-2]: Roof done! |
|                                    |    <svg id="city-viewport">        | 14:28 [Merchant]: Trade deal! |
| QUICK EVENTS:                      |      - Ground & Zone Layer         | 14:27 [Council]: Tax approved |
| [ ⚡ Windfall ] [ 🏗 Rezone ]       |      - Road Network Layer          | ----------------------------- |
| [ 🎉 Festival ] [ ⚠️ Crisis ]      |      - Dynamic Buildings Layer     | [x] Auto-scroll lock          |
|                                    |      - Day/Night Lighting Filter   |                               |
|                                    |      - Agent Avatars & Halos       |                               |
|                                    |      - Active Speech Bubbles       |                               |
+------------------------------------+------------------------------------+-------------------------------+
| SLIDE-OUT AGENT INSPECTOR DRAWER (Activated on clicking any agent)                                      |
| [Avatar] Name: Architect_1 | Role: Lead Architect | Vitals: Energy [85%] Funds [$320] Morale [92%]       |
| Active Goal: "Construct Solar Skyscraper at (14, 8)" | Utility: 0.94                                    |
| Thoughts: "Materials delivered on schedule. Transitioning subagent crew to structural framing."         |
| Subagents Spawned: [Surveyor-1 (active)], [Builder-2 (working)] | Inventory: [Steel: 12, Blueprints: 2]   |
+---------------------------------------------------------------------------------------------------------+
```

### 2.3 Cyber-Civic Design System (`style.css`)
- **Color Palette & CSS Custom Properties**:
  ```css
  :root {
    --bg-primary: #0b0f19;
    --bg-secondary: #131d31;
    --bg-glass: rgba(19, 29, 49, 0.75);
    --border-glass: rgba(255, 255, 255, 0.08);
    --text-primary: #f8fafc;
    --text-secondary: #94a3b8;
    --text-muted: #64748b;
    --accent-cyan: #06b6d4;
    --accent-gold: #f59e0b;
    --accent-emerald: #10b981;
    --accent-purple: #8b5cf6;
    --accent-rose: #f43f5e;
    --accent-orange: #ea580c;
    
    /* Zone Colors */
    --zone-residential: #10b981;
    --zone-commercial: #06b6d4;
    --zone-industrial: #f59e0b;
    --zone-civic: #8b5cf6;
    --zone-parks: #22c55e;
    --zone-roads: #334155;
  }
  ```
- **Glassmorphism & Crisp Rendering**:
  All panels utilize `backdrop-filter: blur(12px); border: 1px solid var(--border-glass); border-radius: 10px;`.
  SVG vector graphics use `shape-rendering: geometricPrecision; text-rendering: optimizeLegibility;`.

---

## 3. Programmatic SVG City Visualizer Technical Design

### 3.1 Dual Projection Geometry & Mathematics

#### A. Isometric Projection Engine (2.5D)
Isometric projection provides rich visual depth while remaining mathematically lightweight.
- **Grid Configuration**:
  - City Grid: $N \times M$ parcels (default: $24 \times 24$ tiles).
  - Isometric Diamond Tile Dimensions: `TILE_WIDTH = 64` px, `TILE_HEIGHT = 32` px.
- **Coordinate Transformation Formula**:
  Given grid parcel coordinates $(g_x, g_y)$ where $0 \le g_x < N$ and $0 \le g_y < M$:
  $$\begin{aligned}
  s_x &= (g_x - g_y) \times \frac{\text{TILE\_WIDTH}}{2} + X_{\text{origin}} \\
  s_y &= (g_x + g_y) \times \frac{\text{TILE\_HEIGHT}}{2} + Y_{\text{origin}}
  \end{aligned}$$
- **Isometric Diamond Polygon Vertex Calculations**:
  ```javascript
  function getIsoDiamondPoints(gx, gy, originX, originY) {
    const sx = (gx - gy) * (TILE_WIDTH / 2) + originX;
    const sy = (gx + gy) * (TILE_HEIGHT / 2) + originY;
    const top    = `${sx},${sy}`;
    const right  = `${sx + TILE_WIDTH / 2},${sy + TILE_HEIGHT / 2}`;
    const bottom = `${sx},${sy + TILE_HEIGHT}`;
    const left   = `${sx - TILE_WIDTH / 2},${sy + TILE_HEIGHT / 2}`;
    return `${top} ${right} ${bottom} ${left}`;
  }
  ```
- **Depth Sorting Algorithm**:
  In isometric projection, objects located at higher $(g_x + g_y)$ values must be rendered in front of objects with lower $(g_x + g_y)$ values. All buildings, structures, and agent avatars are sorted by the depth key:
  $$\text{DepthKey} = g_x + g_y + \text{subLayerBias}$$
  where $\text{subLayerBias} = 0.0$ for ground tiles, $0.2$ for roads, $0.5$ for buildings, and $0.8$ for dynamic agents.

#### B. Orthographic Top-Down Projection Engine (2D)
For users desiring an analytical CAD/zoning view:
$$\begin{aligned}
s_x &= g_x \times \text{CELL\_SIZE} + X_{\text{origin}} \\
s_y &= g_y \times \text{CELL\_SIZE} + Y_{\text{origin}}
\end{aligned}$$
where `CELL_SIZE = 40` px. Toggled via a single button in `renderer.js`.

#### C. Pan & Zoom Camera System
- Handled directly on the root `<svg id="city-viewport">` via `viewBox`:
  ```javascript
  class Camera {
    constructor(svgElement) {
      this.svg = svgElement;
      this.x = 0;
      this.y = 0;
      this.zoom = 1.0;
      this.isDragging = false;
      this.dragStart = { x: 0, y: 0 };
    }
    updateViewBox() {
      const w = this.svg.clientWidth / this.zoom;
      const h = this.svg.clientHeight / this.zoom;
      this.svg.setAttribute('viewBox', `${this.x} ${this.y} ${w} ${h}`);
    }
    pan(dx, dy) {
      this.x -= dx / this.zoom;
      this.y -= dy / this.zoom;
      this.updateViewBox();
    }
    zoomAt(factor, clientX, clientY) {
      const newZoom = Math.min(Math.max(this.zoom * factor, 0.4), 3.0);
      this.zoom = newZoom;
      this.updateViewBox();
    }
  }
  ```

---

### 3.2 Dynamic Zoning Overlays
Each parcel has a assigned zone type that dynamically tints the ground polygon:
- **Residential (`residential`)**: Fill `#10b981`, fill-opacity `0.22`, stroke `#10b981`, stroke-width `1px`.
- **Commercial (`commercial`)**: Fill `#06b6d4`, fill-opacity `0.22`, stroke `#06b6d4`, stroke-width `1px`.
- **Industrial (`industrial`)**: Fill `#f59e0b`, fill-opacity `0.22`, stroke `#f59e0b`, stroke-width `1px`.
- **Civic (`civic`)**: Fill `#8b5cf6`, fill-opacity `0.25`, stroke `#8b5cf6`, stroke-width `1px`.
- **Parks (`park`)**: Fill `#22c55e`, fill-opacity `0.30`, with decorative SVG foliage icons (small pines and bushes).
- **Road (`road`)**: Fill `#1e293b`, fill-opacity `0.85`, stroke `#475569`, stroke-width `1px`.

---

### 3.3 Dynamic Building Evolution Stages (Programmatic SVG Art)
Buildings develop across 5 distinct evolutionary stages based on agent investment and construction:

| Stage | Name | Visual Components & SVG Structure | Zone Specifics |
|---|---|---|---|
| **0** | **Zoned Plot** | Ground diamond outline, corner peg markers, translucent zone fill. | N/A |
| **1** | **Groundwork & Foundation** | Low concrete isometric slab, hazard-striped boundary, mini dirt mound, surveyor tripod icon. | Excavation pit depth tailored to zone. |
| **2** | **Framing & Scaffolding** | Steel girder isometric skeleton, yellow construction crane silhouette (`#eab308`), safety netting (`#ea580c`). | Taller frame for commercial/civic zones. |
| **3** | **Operational Structure** | Solid isometric prism walls, shaded isometric roof, entrance doorway, glowing windows. | - **Res**: Modern apartments with balconies.<br>- **Com**: Glass boutique/market hall.<br>- **Ind**: Brick warehouse with smokestack.<br>- **Civ**: Classical colonnade & clock tower. |
| **4** | **Advanced Cyber Structure** | Multi-tiered isometric skyscraper, rooftop solar panels, glowing neon signs, rooftop antenna with blinking red light beacon (`#ef4444`). | - **Res**: Eco-arcology with vertical trees.<br>- **Com**: Holographic corporate tower.<br>- **Ind**: Automated fusion energy hub.<br>- **Civ**: Grand glass-domed capitol. |

#### Programmatic Building Generation Code Example (Stage 3 Isometric House/Building):
```javascript
function renderIsometricBuilding(gx, gy, zone, level, originX, originY) {
  const sx = (gx - gy) * (TILE_WIDTH / 2) + originX;
  const sy = (gx + gy) * (TILE_HEIGHT / 2) + originY;
  const height = 20 + level * 16; // Building height grows with level
  
  // Left wall, right wall, roof polygons
  const leftWall = `
    ${sx - TILE_WIDTH/2},${sy + TILE_HEIGHT/2}
    ${sx},${sy + TILE_HEIGHT}
    ${sx},${sy + TILE_HEIGHT - height}
    ${sx - TILE_WIDTH/2},${sy + TILE_HEIGHT/2 - height}
  `;
  const rightWall = `
    ${sx},${sy + TILE_HEIGHT}
    ${sx + TILE_WIDTH/2},${sy + TILE_HEIGHT/2}
    ${sx + TILE_WIDTH/2},${sy + TILE_HEIGHT/2 - height}
    ${sx},${sy + TILE_HEIGHT - height}
  `;
  const roof = `
    ${sx},${sy - height}
    ${sx + TILE_WIDTH/2},${sy + TILE_HEIGHT/2 - height}
    ${sx},${sy + TILE_HEIGHT - height}
    ${sx - TILE_WIDTH/2},${sy + TILE_HEIGHT/2 - height}
  `;
  
  return `
    <g class="building-entity" data-parcel="${gx}_${gy}">
      <!-- Left Wall (Shadowed) -->
      <polygon points="${leftWall}" fill="var(--wall-dark, #1e293b)" stroke="#0f172a" stroke-width="0.5"/>
      <!-- Right Wall (Lit) -->
      <polygon points="${rightWall}" fill="var(--wall-light, #334155)" stroke="#0f172a" stroke-width="0.5"/>
      <!-- Roof Top -->
      <polygon points="${roof}" fill="var(--roof-color, #475569)" stroke="#0f172a" stroke-width="0.5"/>
      <!-- Windows / Details -->
      ${renderWindows(sx, sy, height, level)}
    </g>
  `;
}
```

---

### 3.4 Connected Road Network Rendering
Roads automatically compute neighbor connectivity via a 4-bit adjacency bitmask:
$$\text{Bitmask} = (\text{North} \times 1) + (\text{East} \times 2) + (\text{South} \times 4) + (\text{West} \times 8)$$

The renderer matches the 16 combinations:
- `0`: Isolated cul-de-sac.
- `1` or `4` or `5`: Straight North-South road.
- `2` or `8` or `10`: Straight East-West road.
- `3`, `6`, `9`, `12`: 90-degree curved corners.
- `7`, `11`, `13`, `14`: 3-way T-junctions.
- `15`: 4-way crossroad intersection with zebra crossings.
The asphalt path is rendered with dark slate `#1e293b`, kerb edging `#475569`, and dashed yellow centerlines `#eab308`.

---

### 3.5 Day/Night Lighting Filter & Atmospheric Glow
The city operates on a continuous 24-hour cycle where 1 simulated day = 120 ticks (1 hour = 5 ticks).
The lighting filter is implemented as an SVG overlay `<rect id="ambient-light">` covering the entire viewport, paired with an SVG `<filter id="city-bloom">`:

| Simulated Time | Phase | Overlay Fill Color | Fill Opacity | Streetlights / Window Glow |
|---|---|---|---|---|
| **05:00 - 07:00** | Dawn / Sunrise | `#ffb7b2` (Rose Gold) | `0.20` | Dimming off |
| **07:00 - 17:00** | Daylight / Noon | `#ffffff` | `0.00` (Transparent) | Off |
| **17:00 - 19:30** | Dusk / Sunset | `#f97316` (Amber Orange) | `0.30` | Activating |
| **19:30 - 05:00** | Midnight / Night | `#070b19` (Deep Navy) | `0.65` | **Full Night Bloom** |

- **Night Bloom Elements**:
  - Streetlamps at road intersections activate SVG `<circle>` nodes with radial gradient fills (`#fef08a` at center fading to transparent).
  - Building windows toggle from dark charcoal `#0f172a` to warm glowing yellow `#fde047` or cyber-cyan `#22d3ee`, creating an authentic living nocturnal cityscape.

---

## 4. Dynamic Agent Visualization & Animation

### 4.1 Smooth Movement Interpolation (LERP Engine)
To eliminate jarring grid-stepping, the agent view controller implements a continuous 60 FPS animation loop decoupling tick events from display rendering.

```javascript
class AgentAnimator {
  constructor() {
    this.agents = new Map(); // id -> { renderX, renderY, startX, startY, targetX, targetY, startTime, duration }
    this.requestFrameId = null;
  }

  onAgentMoved(agentId, newGridX, newGridY, tickDurationMs) {
    const targetScreen = gridToScreen(newGridX, newGridY);
    let state = this.agents.get(agentId);
    if (!state) {
      state = {
        renderX: targetScreen.x,
        renderY: targetScreen.y,
        startX: targetScreen.x,
        startY: targetScreen.y,
        targetX: targetScreen.x,
        targetY: targetScreen.y,
        startTime: performance.now(),
        duration: tickDurationMs
      };
      this.agents.set(agentId, state);
    } else {
      state.startX = state.renderX;
      state.startY = state.renderY;
      state.targetX = targetScreen.x;
      state.targetY = targetScreen.y;
      state.startTime = performance.now();
      state.duration = tickDurationMs;
    }
  }

  animate(now) {
    for (const [id, state] of this.agents.entries()) {
      const elapsed = now - state.startTime;
      const progress = Math.min(1.0, elapsed / state.duration);
      // Ease-in-out quadratic smoothing
      const ease = progress < 0.5 
        ? 2 * progress * progress 
        : -1 + (4 - 2 * progress) * progress;

      state.renderX = state.startX + (state.targetX - state.startX) * ease;
      state.renderY = state.startY + (state.targetY - state.startY) * ease;

      // Update DOM transform directly for maximum GPU acceleration
      const elem = document.getElementById(`agent-${id}`);
      if (elem) {
        elem.setAttribute('transform', `translate(${state.renderX}, ${state.renderY})`);
      }
    }
    requestAnimationFrame((t) => this.animate(t));
  }
}
```

### 4.2 Role Badges, Color Codes & Subagent Styling
Each autonomous agent possesses a unique visual identity and role badge:

| Role | Hex Color | Badge Icon (Pure SVG) | Description |
|---|---|---|---|
| **Mayor** | `#f59e0b` (Gold) | Crown / Star (`polygon points="12,2 15,9..."`) | Civic governance, zoning decrees, speeches. |
| **Architect** | `#06b6d4` (Cyan) | Drafting Compass / Blueprint | Building design, site planning, delegating. |
| **Engineer** | `#ea580c` (Orange) | Interlocking Gears / Wrench | Infrastructure maintenance, power grid. |
| **Merchant** | `#10b981` (Emerald) | Scales of Commerce / Gold Coin | Material trading, market transactions. |
| **Scholar** | `#8b5cf6` (Purple) | Open Tome / Atomic Ring | Research, innovation, evolutionary records. |
| **Observer** | `#f8fafc` (Ice White) | Omnipresent Eye (`ellipse + circle`) | Civic sentiment, demographic census. |

- **Subagent Visual Differentiation**:
  - Subagents are rendered at **75% scale** (`transform="scale(0.75)"`).
  - Outlined with a **dashed circular border** (`stroke-dasharray="3,2"`).
  - Archetypes:
    - *Surveyor*: Cyan dashed ring, tripod badge.
    - *ConstructionCrew*: Safety-orange dashed ring, hardhat badge.
    - *ResearchAssistant*: Purple dashed ring, quill badge.
    - *Courier*: Lime-green dashed ring, winged sneaker badge.
- **Parent-Child Lineage Tether**:
  Hovering over any parent agent or subagent draws an animated SVG connection line (`<line stroke-dasharray="4" class="tether-line">`) directly between parent and child coordinates, visually confirming hierarchical delegation.

### 4.3 Speech Bubbles for Live Dialogue
When agents communicate, an ephemeral speech bubble appears above their avatar:
- **Structure**:
  ```xml
  <g class="speech-bubble" transform="translate(0, -38)">
    <!-- Bubble Background with Bottom Tail -->
    <path d="M -60 -24 h 120 a 8 8 0 0 1 8 8 v 16 a 8 8 0 0 1 -8 8 h -52 l -8 8 l -8 -8 h -52 a 8 8 0 0 1 -8 -8 v -16 a 8 8 0 0 1 8 -8 z"
          fill="rgba(15, 23, 42, 0.92)" stroke="var(--agent-role-color)" stroke-width="1.5" filter="drop-shadow(0 4px 6px rgba(0,0,0,0.4))"/>
    <!-- Speaker & Message Text -->
    <text x="0" y="-12" text-anchor="middle" font-size="10" font-weight="bold" fill="#f8fafc">Mayor Augustus</text>
    <text x="0" y="2" text-anchor="middle" font-size="9" fill="#94a3b8">"Approving district rezone!"</text>
  </g>
  ```
- **Lifecycle Animation**:
  1. Instantly pops up with a spring scale animation (`scale(0.8) -> scale(1.0)` over 150ms).
  2. Stays fully readable for 3.5 seconds.
  3. Fades to `opacity: 0` over 600ms via CSS transitions before being unmounted from the DOM.

### 4.4 Emotion & Status Halos
Beneath each agent's avatar is an animated SVG status ring reflecting real-time physiological & psychological state:
- **Vital Ring (Energy Level)**:
  - `> 75%`: Solid emerald circle (`#10b981`).
  - `30% - 75%`: Amber arc (`#f59e0b`).
  - `< 30%`: Pulsing crimson warning ring (`#ef4444` with CSS `@keyframes pulse`).
- **Psychological Mood Aura**:
  - *Inspired/Productive*: Glowing warm gold halo.
  - *Deliberating/Pathfinding*: Rotating segmented cyan ring.
  - *Socializing/Trading*: Shimmering green halo.
  - *Resting/Recharging*: Soft lavender glow with floating "z Z" SVG particles.

---

## 5. Real-Time HUD, Pure Canvas/SVG Charts & Inspector Drawer

### 5.1 Real-Time Demographic & Economic Charts (`charts.js`)
Zero external charting libraries. All charts render directly via native HTML5 `<canvas>` (for high-frequency time series) or programmatic SVG (for distribution donuts).

#### A. Time-Series Sparklines & Vitals Graph (`<canvas id="vitals-chart">`)
- **Capacity**: Rolling circular buffer of 100 simulation ticks.
- **Metrics Tracked**:
  1. Primary Population (Blue line `#38bdf8`) & Subagent Count (Dashed Cyan `#06b6d4`).
  2. City Treasury (Gold line `#f59e0b`).
  3. Total Energy Output (Emerald line `#10b981`).
  4. Innovation & Civic Happiness (Purple line `#8b5cf6`).
- **Rendering Logic**:
  Clears canvas, draws semi-transparent grid lines, normalizes data bounds with auto-ranging Y-axis, draws smoothed Bezier polylines, and renders a dynamic tooltip on hover.

#### B. Zoning Distribution Donut Chart (Pure SVG)
- Utilizes SVG `<circle>` with `stroke-dasharray` and `stroke-dashoffset`:
  ```javascript
  function updateDonutChart(zoneCounts) {
    const total = Object.values(zoneCounts).reduce((a, b) => a + b, 0);
    const radius = 40;
    const circumference = 2 * Math.PI * radius; // ~251.32
    let accumulatedOffset = 0;
    
    for (const [zone, count] of Object.entries(zoneCounts)) {
      const sliceLength = (count / total) * circumference;
      const circle = document.getElementById(`donut-slice-${zone}`);
      if (circle) {
        circle.setAttribute('stroke-dasharray', `${sliceLength} ${circumference}`);
        circle.setAttribute('stroke-dashoffset', -accumulatedOffset);
      }
      accumulatedOffset += sliceLength;
    }
  }
  ```

### 5.2 Live Action & Dialogue Feed
Located on the right panel, split into two tabs:
1. **City Action Log**:
   - Displays events: building level-ups, zoning mandates, tax collections, subagent spawns, resource discoveries.
   - Categorized by badge: `[BUILD]`, `[GOV]`, `[ECON]`, `[SPAWN]`, `[CRISIS]`.
2. **Dialogue Feed**:
   - Full transcript of agent conversations: public speeches, direct trades, and subagent work reports.
   - Clickable agent names: clicking any speaker immediately centers the viewport camera on that agent and opens their Inspector Drawer!
3. **Features**:
   - Virtualized ring buffer (capped at 200 DOM nodes to maintain low memory).
   - "Auto-Scroll Lock" toggle: auto-scrolls down when new messages arrive unless the user scrolls up to inspect history.

### 5.3 Agent Thought & Inventory Inspection Drawer
Clicking any agent opens a glassmorphic inspection drawer sliding in from the right:
- **Agent Identity**: Portrait avatar, full name, role badge, generation, spawn tick.
- **Real-Time Vitals**:
  - Energy Gauge (0-100% with consumption rate per tick).
  - Personal Treasury ($) and Civic Reputation score.
- **Cognitive State**:
  - Current Goal: e.g., *"Survey Commercial parcel at (14, 8) for structural upgrade"*.
  - Goal Hierarchy Utility Matrix: Utility score of active goal vs discarded alternatives.
  - Inner Monologue / Reflection: Live stream of the agent's internal thought deliberation.
- **Hierarchical Lineage**:
  - If Parent: List of active spawned subagents with current tasks and lifespan remaining.
  - If Subagent: Link to parent agent, reason for creation, and retirement countdown.
- **Inventory & Resources**:
  - Grid of carried resources: Wood, Steel, Concrete, Blueprints, Energy Cells, Currency.
- **Genetic Trait DNA (5-Factor Radar/Bar Chart)**:
  - Diligence, Sociability, RiskTolerance, Frugality, Innovation.

---

## 6. Real-Time Streaming Protocol (`/ws`) & REST API Specification

### 6.1 WebSocket Architecture & Streaming Protocol (`/ws`)
- **Endpoint**: `ws://localhost:8000/ws`
- **Protocol Flow**:
  1. **Connection & Handshake**: Client connects. Server immediately replies with `INIT_STATE`.
  2. **Tick Stream**: On every simulation cycle, server broadcasts a compact differential `TICK_DELTA`.
  3. **Bi-directional Heartbeat**: Client sends `PING` every 15s; server replies `PONG`.

#### A. Initial State Message (`INIT_STATE`):
Sent once upon client connection:
```json
{
  "type": "INIT_STATE",
  "tick": 142,
  "epoch": 2,
  "grid": {
    "width": 24,
    "height": 24,
    "parcels": [
      {"x": 0, "y": 0, "zone": "residential", "building": {"type": "apartment", "level": 2, "health": 100}},
      {"x": 0, "y": 1, "zone": "road", "building": null}
    ]
  },
  "agents": [
    {
      "id": "agent_mayor_1",
      "name": "Augustus",
      "role": "Mayor",
      "is_subagent": false,
      "parent_id": null,
      "x": 12,
      "y": 12,
      "energy": 90,
      "funds": 1200,
      "active_goal": "Balance City Budget",
      "traits": {"diligence": 0.85, "sociability": 0.9}
    }
  ],
  "economy": {
    "treasury": 18450,
    "total_energy": 4200,
    "tax_rate": 0.08
  },
  "sim_status": {
    "is_paused": false,
    "tick_rate_hz": 1.0,
    "time_of_day_hours": 14.5,
    "weather": "clear"
  }
}
```

#### B. Differential Delta Message (`TICK_DELTA`):
Broadcast every tick (under 1.5 KB payload):
```json
{
  "type": "TICK_DELTA",
  "seq": 143,
  "tick": 143,
  "epoch": 2,
  "time_of_day_hours": 14.7,
  "weather": "clear",
  "economy": {
    "treasury": 18510,
    "total_energy": 4180
  },
  "agents_moved": [
    {"id": "agent_architect_1", "x": 14, "y": 8, "status": "walking", "energy": 84},
    {"id": "sub_surveyor_101", "x": 14, "y": 9, "status": "surveying", "energy": 91}
  ],
  "agents_spawned": [
    {
      "id": "sub_builder_102",
      "name": "Crew-Beta",
      "role": "ConstructionCrew",
      "is_subagent": true,
      "parent_id": "agent_architect_1",
      "x": 14,
      "y": 8,
      "energy": 100
    }
  ],
  "agents_retired": ["sub_surveyor_99"],
  "buildings_updated": [
    {"x": 14, "y": 8, "level": 3, "progress": 1.0, "status": "completed"}
  ],
  "dialogues": [
    {
      "id": "msg_892",
      "speaker_id": "agent_architect_1",
      "speaker_name": "Leonardo",
      "recipient_id": "all",
      "content": "Phase 2 structural framing initiated at parcel (14, 8).",
      "tick": 143
    }
  ],
  "events": [
    {
      "id": "evt_451",
      "category": "construction",
      "title": "Solar Hub Upgraded",
      "tick": 143,
      "severity": "success"
    }
  ]
}
```

#### C. Client-to-Server Control Message (`CONTROL_ACTION`):
```json
{
  "type": "CONTROL_ACTION",
  "action": "pause" | "resume" | "step" | "set_speed" | "trigger_event",
  "payload": {
    "tick_rate": 2.5,
    "event_name": "resource_windfall",
    "params": {"amount": 5000}
  }
}
```

---

### 6.2 REST API Specification

| Endpoint | Method | Query / Body Params | Response Schema | Description |
|---|---|---|---|---|
| `/api/city/status` | `GET` | None | `{ tick, epoch, is_paused, tick_rate, population, subagents, treasury, weather, daylight_hours }` | Comprehensive city macro vitals and simulation status. |
| `/api/agents` | `GET` | `?role=architect&include_subagents=true` | `[ { id, name, role, is_subagent, parent_id, x, y, energy, funds, active_goal } ]` | List of all currently living agents and subagents. |
| `/api/agents/{id}` | `GET` | None | `{ id, name, role, x, y, vitals, active_goal, thoughts, lineage, inventory, traits }` | Deep inspection details of a specific agent. |
| `/api/buildings` | `GET` | `?zone=commercial&min_level=2` | `[ { x, y, zone, type, level, health, owner_id } ]` | Spatial parcel map and building evolution states. |
| `/api/events` | `GET` | `?limit=50&category=construction` | `[ { id, tick, category, title, description, severity } ]` | Chronological simulation event log. |
| `/api/controls` | `POST` | `{"action": "pause" \| "resume" \| "step" \| "set_speed" \| "trigger_event"}` | `{ "success": true, "new_state": { ... } }` | Interactive control of simulation lifecycle and custom event dispatching. |
| `/api/snapshot/save`| `POST` | `{"filename": "snap_epoch2.json"}` | `{ "success": true, "path": "...", "size_bytes": 104520 }` | Persist current simulation state to SQLite / JSON. |
| `/api/snapshot/load`| `POST` | `{"filename": "snap_epoch2.json"}` | `{ "success": true, "restored_tick": 142 }` | Restore simulation state from a snapshot. |

---

## 7. State Persistence & Snapshotting Architecture

### 7.1 SQLite Relational Persistence Schema (`engine/persistence.py`)
To ensure zero corruption and high-concurrency read/write capability, the simulation uses standard Python `sqlite3` configured with Write-Ahead Logging:
```python
conn.execute("PRAGMA journal_mode=WAL;")
conn.execute("PRAGMA synchronous=NORMAL;")
```

```sql
-- 1. Simulation Metadata & Run State
CREATE TABLE IF NOT EXISTS simulation_meta (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    city_name TEXT NOT NULL DEFAULT 'AgentCity',
    current_tick INTEGER NOT NULL,
    current_epoch INTEGER NOT NULL DEFAULT 1,
    is_paused INTEGER NOT NULL DEFAULT 0,
    tick_rate REAL NOT NULL DEFAULT 1.0,
    weather TEXT NOT NULL DEFAULT 'clear',
    time_of_day REAL NOT NULL DEFAULT 12.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. City Spatial Parcels & Buildings
CREATE TABLE IF NOT EXISTS parcels (
    x INTEGER NOT NULL,
    y INTEGER NOT NULL,
    zone_type TEXT NOT NULL,
    building_type TEXT,
    building_level INTEGER DEFAULT 0,
    building_health INTEGER DEFAULT 100,
    owner_agent_id TEXT,
    PRIMARY KEY (x, y)
);

-- 3. Living Autonomous Agents & Subagents
CREATE TABLE IF NOT EXISTS agents (
    agent_id TEXT PRIMARY KEY,
    parent_id TEXT,
    name TEXT NOT NULL,
    role TEXT NOT NULL,
    is_subagent INTEGER NOT NULL DEFAULT 0,
    x INTEGER NOT NULL,
    y INTEGER NOT NULL,
    energy INTEGER NOT NULL DEFAULT 100,
    funds INTEGER NOT NULL DEFAULT 500,
    status TEXT NOT NULL DEFAULT 'idle',
    active_goal TEXT,
    traits_json TEXT NOT NULL,
    inventory_json TEXT NOT NULL,
    memory_json TEXT,
    created_at_tick INTEGER NOT NULL,
    retired_at_tick INTEGER
);

-- 4. Macro Economic & Demographic History
CREATE TABLE IF NOT EXISTS economy_history (
    tick INTEGER PRIMARY KEY,
    treasury INTEGER NOT NULL,
    total_energy INTEGER NOT NULL,
    materials INTEGER NOT NULL,
    population_count INTEGER NOT NULL,
    subagent_count INTEGER NOT NULL,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. Event Audit Log
CREATE TABLE IF NOT EXISTS event_log (
    event_id TEXT PRIMARY KEY,
    tick INTEGER NOT NULL,
    category TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    severity TEXT NOT NULL DEFAULT 'info',
    data_json TEXT
);

-- 6. Inter-Agent Dialogue & Messages
CREATE TABLE IF NOT EXISTS dialogue_messages (
    message_id TEXT PRIMARY KEY,
    tick INTEGER NOT NULL,
    speaker_id TEXT NOT NULL,
    recipient_id TEXT NOT NULL,
    topic TEXT,
    content TEXT NOT NULL
);
```

### 7.2 Portable JSON Snapshotting Format
In addition to SQLite, AgentCity supports single-file portable JSON snapshots (`.json`) containing the full simulation state, facilitating cross-machine transfer, testing regression, and visual replay.
- **Snapshot Contents**:
  - `metadata`: Engine version, timestamp, tick, epoch, random seed, weather, time of day.
  - `grid`: Parcel layout, zoning classifications, building levels.
  - `agents`: All active agents, goals, memories, subagent trees, trait genes.
  - `economy`: Macro treasury, taxes, resource reserves.
  - `recent_events`: Last 100 historical logs.
- **Save/Load Guarantee**: Loading a snapshot creates a byte-for-byte reconstructed simulation state; the engine resumes ticking from that exact coordinate and tick number without delta spikes.

### 7.3 Headless Simulation Execution Mode
AgentCity supports running without GUI or WebSocket streaming for automated benchmarking, CI testing, and evolutionary fitness experiments:
```bash
python -m agent_city.server --headless --ticks 500 --snapshot-interval 100 --output-db city_simulation.db
```
In headless mode:
- WebSocket broadcasting and UI asset serving are disabled.
- Simulation runs at maximum CPU throughput (~200-500 ticks/sec on low-spec hardware).
- Dumps benchmark statistics upon completion (agent tasks completed, structures built, GDP growth, subagents spawned/retired).

---

## 8. Cross-Platform Quick-Start Launcher Scripts

### 8.1 Windows Launcher Script (`start_city.bat`)
Location: `agent_city/start_city.bat`
```bat
@echo off
setlocal enabledelayedexpansion
title AgentCity - Autonomous Multi-Agent Simulation

echo =======================================================
echo          AGENT CITY - AUTONOMOUS SIMULATION
echo =======================================================
echo.

:: 1. Locate Python executable
set "PYTHON_CMD="
if exist "%LOCALAPPDATA%\hermes\hermes-agent\venv\Scripts\python.exe" (
    set "PYTHON_CMD=%LOCALAPPDATA%\hermes\hermes-agent\venv\Scripts\python.exe"
) else (
    where python >nul 2>nul
    if !errorlevel! equ 0 (
        set "PYTHON_CMD=python"
    ) else (
        where py >nul 2>nul
        if !errorlevel! equ 0 (
            set "PYTHON_CMD=py -3"
        )
    )
)

if "%PYTHON_CMD%"=="" (
    echo [ERROR] Python 3 was not detected in PATH or virtual environments.
    echo Please install Python 3.9+ or run within a configured environment.
    pause
    exit /b 1
)

echo [OK] Using Python: %PYTHON_CMD%

:: 2. Check dependencies
echo [INFO] Verifying backend dependencies...
%PYTHON_CMD% -c "import fastapi, uvicorn, websockets, pydantic" >nul 2>nul
if !errorlevel! neq 0 (
    echo [WARN] Missing required packages. Installing from requirements.txt...
    %PYTHON_CMD% -m pip install -r requirements.txt
    if !errorlevel! neq 0 (
        echo [ERROR] Failed to install dependencies.
        pause
        exit /b 1
    )
)
echo [OK] All dependencies verified.

:: 3. Launch Server and open browser
echo.
echo [INFO] Starting AgentCity server on http://localhost:8000 ...
echo [INFO] Launching default web browser in 3 seconds...

start "" /b cmd /c "timeout /t 3 /nobreak >nul & start http://localhost:8000"

%PYTHON_CMD% -m uvicorn agent_city.server:app --host 127.0.0.1 --port 8000 --reload

pause
```

### 8.2 Unix / Linux / macOS Launcher Script (`start_city.sh`)
Location: `agent_city/start_city.sh`
```bash
#!/usr/bin/env bash
set -e

echo "======================================================="
echo "         AGENT CITY - AUTONOMOUS SIMULATION           "
echo "======================================================="
echo ""

# 1. Locate Python 3
PYTHON_BIN=""
if command -v python3 &>/dev/null; then
    PYTHON_BIN="python3"
elif command -v python &>/dev/null; then
    PYTHON_BIN="python"
else
    echo "[ERROR] Python 3 is required but was not found on PATH." >&2
    exit 1
fi

echo "[OK] Using Python: $($PYTHON_BIN --version)"

# 2. Check and install dependencies
if ! $PYTHON_BIN -c "import fastapi, uvicorn, websockets, pydantic" &>/dev/null; then
    echo "[WARN] Missing dependencies. Installing from requirements.txt..."
    $PYTHON_BIN -m pip install -r requirements.txt
fi
echo "[OK] Dependencies verified."

# 3. Open browser function
open_browser() {
    sleep 2
    URL="http://localhost:8000"
    if command -v xdg-open &>/dev/null; then
        xdg-open "$URL"
    elif command -v open &>/dev/null; then
        open "$URL"
    else
        echo "[INFO] Please navigate your browser to: $URL"
    fi
}

open_browser &

echo "[INFO] Launching AgentCity FastAPI server..."
exec $PYTHON_BIN -m uvicorn agent_city.server:app --host 127.0.0.1 --port 8000 --reload
```

---

## 9. Comprehensive Feature Inventory Matrix (R3, R4, Acceptance Criteria)

| Feature ID | Feature Name | Requirement Mapping | Implementing Component | Key Constraints & Technical Specs | Verification Method |
|---|---|---|---|---|---|
| **F-R3-01** | Zero-Dependency Web Dashboard | R3 | `agent_city/static/index.html`, `style.css`, `app.js` | Zero npm/CDN dependencies; pure HTML5/CSS3/ES6+; glassmorphic UI. | Browser visual test, network tab inspection confirms zero external HTTP requests. |
| **F-R3-02** | Programmatic SVG Isometric Visualizer | R3 | `agent_city/static/js/renderer.js` | Diamond polygon math; depth sorting by `x+y`; responsive camera pan & zoom. | Map renders correctly with depth ordering; zoom/pan tested with wheel/drag. |
| **F-R3-03** | Dual Projection Engine | R3 | `agent_city/static/js/renderer.js` | Toggle between 2.5D Isometric and 2D Orthographic top-down views. | UI button switch immediately toggles projection without reload. |
| **F-R3-04** | Dynamic Zoning Overlays | R3 | `agent_city/static/js/renderer.js` | 6 color-coded zones (Res, Com, Ind, Civ, Park, Road); translucent fills. | Visual verification of colored zone polygons across grid coordinates. |
| **F-R3-05** | Animated Building Evolution | R3 | `agent_city/static/js/renderer.js` | 5 evolutionary stages (Plot, Foundation, Scaffold, Operational, Skyscraper). | Building evolves as simulation ticks proceed; level changes update SVG sprites. |
| **F-R3-06** | Connected Road Network Solver | R3 | `agent_city/static/js/renderer.js` | 4-bit neighbor adjacency mask; 16 road intersection variants. | Continuous connected road paths render correctly with markings. |
| **F-R3-07** | Day/Night Lighting Filter | R3 | `agent_city/static/js/renderer.js`, `style.css` | 120-tick day/night cycle; SVG ambient overlay; nocturnal streetlights. | Ticking causes ambient overlay to cycle dawn->day->dusk->night with window glow. |
| **F-R3-08** | Smooth Agent LERP Movement | R3 | `agent_city/static/js/agent_view.js` | 60 FPS `requestAnimationFrame` interpolation; quadratic easing. | Agents glide smoothly across tiles instead of teleporting. |
| **F-R3-09** | Role Badges & Visual Identities | R3 | `agent_city/static/js/agent_view.js` | 6 distinct role badges; subagents at 75% scale with dashed rings. | Inspect agents on map; icons and colors match defined role taxonomy. |
| **F-R3-10** | Live Dialogue Speech Bubbles | R3 | `agent_city/static/js/agent_view.js` | SVG speech bubbles with tail; auto-wrap; pop-in and fade-out timer. | Dialogue events trigger floating speech bubbles that auto-fade after 3.5s. |
| **F-R3-11** | Status Rings & Emotion Halos | R3 | `agent_city/static/js/agent_view.js` | Concentric status rings for energy; mood glowing auras; sleeping particles. | Altering agent energy shifts ring color (green->amber->pulsing red). |
| **F-R3-12** | Parent-Child Lineage Tethers | R3, R2 | `agent_city/static/js/agent_view.js` | Animated dashed SVG line connecting parent agent to spawned subagents. | Hovering over subagent renders direct line to parent agent. |
| **F-R3-13** | Pure Canvas/SVG Demographic Charts | R3 | `agent_city/static/js/charts.js` | Multi-line time series (Pop, Subagents, Treasury, Energy) on HTML5 canvas. | Charts update live each tick without flicker or memory leaks. |
| **F-R3-14** | Live Dialogue & Event Feed | R3, AC | `agent_city/static/js/app.js` | Dual-tabbed stream; 200-message virtualized ring buffer; auto-scroll lock. | Stream continuously appends events; agent names clickable to focus. |
| **F-R3-15** | Agent Inspection Drawer | R3, AC | `agent_city/static/js/app.js` | Slide-out panel; live vitals, goal utility, inner thoughts, inventory, DNA. | Clicking agent opens drawer populated with real-time agent parameters. |
| **F-R4-01** | Real-Time WebSocket Streaming | R4, AC | `agent_city/api/websocket.py`, `app.js` | `/ws` endpoint; `INIT_STATE` handshake; differential `TICK_DELTA` broadcast. | WebSocket client connects and receives stream; delta size < 1.5 KB. |
| **F-R4-02** | Comprehensive REST API | R4, AC | `agent_city/api/routes.py` | `/api/city/status`, `/api/agents`, `/api/buildings`, `/api/events`, `/api/controls`. | Automated pytest verifying HTTP status codes and JSON schema validation. |
| **F-R4-03** | Interactive User Controls | AC | `agent_city/api/routes.py`, `app.js` | Pause, resume, step, tick rate adjustment, trigger custom city events. | Clicking Pause stops tick loop; Windfall increases treasury by $5,000. |
| **F-R4-04** | SQLite State Persistence | R4 | `agent_city/engine/persistence.py` | WAL mode SQLite database; tables for metadata, parcels, agents, economy. | Unit test verifying simulation saves state to DB and recovers on restart. |
| **F-R4-05** | Portable JSON Snapshotting | R4 | `agent_city/engine/persistence.py` | Export/import full simulation snapshot; deterministic resume. | `test_snapshot_roundtrip` verifies identical state before export and after import. |
| **F-R4-06** | Headless Execution Mode | R4, AC | `agent_city/server.py` | `--headless --ticks N` CLI flag; high-throughput execution for CI. | CLI execution runs 500 ticks in headless mode and outputs summary DB. |
| **F-R4-07** | Windows Quick-Start Launcher | AC | `agent_city/start_city.bat` | Detects Python, validates dependencies, launches server, opens browser. | Running `start_city.bat` opens browser to `http://localhost:8000`. |
| **F-R4-08** | Unix/macOS Quick-Start Launcher | AC | `agent_city/start_city.sh` | Bash script with dependency check, server boot, and browser opening. | Shell script execution launches server and confirms URL printed. |

---

## 10. Automated Verification Strategy

### 10.1 Automated Pytest Verification Suite
The implementation must be backed by automated test suites in `agent_city/tests/`:
1. `test_api.py`:
   - `test_get_city_status()`: Verifies HTTP 200, valid schema, positive population and treasury.
   - `test_get_agents()`: Validates filtering by role and subagent status.
   - `test_get_buildings()`: Asserts all returned parcels have valid coordinate bounds and levels.
   - `test_post_controls_pause_resume()`: Tests toggling pause state via REST.
   - `test_post_controls_trigger_windfall()`: Asserts treasury increases following a windfall event.
2. `test_websocket.py`:
   - `test_ws_init_state()`: Tests that connecting to `/ws` receives `INIT_STATE` within 500ms.
   - `test_ws_tick_delta()`: Validates that advancing the simulation emits a valid `TICK_DELTA` message.
3. `test_persistence.py`:
   - `test_sqlite_save_and_load()`: Inserts test agents and parcels, saves to SQLite, verifies recovery.
   - `test_json_snapshot_roundtrip()`: Serializes state to JSON, creates fresh engine, loads JSON, and asserts parity.
4. `test_headless.py`:
   - Runs headless simulation for 100 ticks and asserts zero deadlocks or unhandled exceptions.

### 10.2 Frontend Dependency & Performance Verification
- **Zero-Dependency Linting**: Automated check in tests scanning `agent_city/static/` to ensure no `cdn.jsdelivr.net`, `unpkg.com`, `cdnjs.cloudflare.com`, or external `<script src="...">` tags exist.
- **Rendering Performance**: LERP loop profiled under Chrome DevTools performance tab targeting steady 60 FPS with frame times < 16.6ms.
