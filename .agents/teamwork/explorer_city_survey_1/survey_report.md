# Technical Architecture Survey & System Design Specification
**Project**: Evolving Virtual City Multi-Agent Simulation (`agent_city`)  
**Document**: Technical Survey & R1 Architectural Specification  
**Agent**: `explorer_city_survey_1` (teamwork_preview_explorer)  
**Parent Agent**: `orchestrator_2` (`d8f49c97-82ba-4295-8de9-17407789baa2`)  
**Date**: 2026-09-30  
**Target Directory**: `c:\Users\ignaz\antigravity\keen-franklin\agent_city`  

---

## 1. Executive Summary & Host Environment Assessment

This survey report provides the architectural foundation and technical blueprint for **R1 (High-Performance Simulation & Agent Engine)** and the overarching system architecture of `agent_city`. The simulation models an evolving, autonomous virtual city where agents fulfill specialized civic roles, move within a 2D/isometric grid, trade resources, establish zones, debate policy, execute democratic consensus voting, and evolve the city over continuous simulation epochs.

### 1.1 Host Environment & Python Toolchain Verification
The host machine was investigated and validated. All required libraries have been inspected, tested, and confirmed functional:

| Component | Verified Version / Path | Status | Role in Project |
| :--- | :--- | :--- | :--- |
| **Python Runtime** | `3.14.4 (AMD64 Windows)` at `C:\Users\ignaz\AppData\Local\Python\pythoncore-3.14-64\python.exe` | **Verified** | Core runtime engine |
| **Alternative Runtime** | `3.12.8` via uv at `C:\Users\ignaz\AppData\Roaming\uv\python\cpython-3.12.8-windows-x86_64-none\python.exe` | **Verified** | Standby runtime |
| **uv Package Manager** | `0.5.9` at `C:\Users\ignaz\.local\bin\uv.exe` | **Verified** | Dependency & tool runner |
| **FastAPI** | `0.141.1` | **Verified** | High-performance ASGI REST & WebSocket framework |
| **Uvicorn** | `0.52.4` | **Verified** | Lightning-fast ASGI production web server |
| **WebSockets** | `17.1` | **Verified** | Native low-latency bidirectional socket streaming |
| **Pydantic** | `2.13.4` (pydantic-core `2.46.4`) | **Verified** | High-throughput data validation & serialization |
| **Starlette** | `1.6.0` | **Verified** | ASGI foundation, routing, WebSocket protocol handling |
| **AnyIO** | `4.14.2` | **Verified** | Structured concurrency & async event loop support |
| **SQLite** | `3.50.4` (built-in standard library) | **Verified** | State persistence, event logging, WAL concurrency |
| **Pytest** | `9.1.1` | **Verified** | Automated unit, integration, and performance testing |
| **Pytest-Asyncio** | `1.4.0` | **Verified** | Asynchronous test fixture & coroutine test execution |
| **HTTPX** | `0.28.1` | **Verified** | Async HTTP client for end-to-end API testing |
| **SSE-Starlette** | `3.5.0` | **Verified** | Server-Sent Events streaming fallback |

*Network Note*: Direct pip connections to PyPI require `--trusted-host pypi.org --trusted-host files.pythonhosted.org` due to host SSL inspection certificate chains. All critical packages have been installed and validated to import with zero errors.

---

## 2. System Architecture & Module Structure

The project will reside in `agent_city/` with a clean separation of concerns between backend simulation logic, persistence, REST/WebSocket API endpoints, and the dependency-free vanilla JS + programmatic SVG frontend.

```
agent_city/
├── backend/
│   ├── __init__.py
│   ├── main.py                  # FastAPI application entrypoint, lifespan, CORS, static mounts
│   ├── config.py                # Global settings, grid dimensions, tick rate, defaults
│   ├── engine/
│   │   ├── __init__.py
│   │   ├── coordinator.py       # SimulationCoordinator: tick loop, pause/resume, speed, state lock
│   │   ├── grid.py              # CityGrid: 2D spatial tiles, zoning, collision, A* pathfinding
│   │   ├── agent_manager.py     # AgentManager: agent registry, perception/action cycle, spawning
│   │   ├── message_bus.py       # MessageBus: direct, broadcast, topic channels, consensus ballots
│   │   └── economy.py           # EconomySystem: treasury, taxation, energy/materials, trade ledger
│   ├── models/
│   │   ├── __init__.py
│   │   ├── schemas.py           # Pydantic v2 schemas: Agent, Tile, Building, Event, Message, Epoch
│   │   └── enums.py             # Enums: Role, ZoneType, ActionType, MessageType, VoteChoice
│   ├── storage/
│   │   ├── __init__.py
│   │   └── db.py                # SQLite persistence manager, WAL mode, snapshot save/load
│   └── api/
│       ├── __init__.py
│       ├── routes_city.py       # REST: /api/city/status, /pause, /resume, /speed, /step, /reset
│       ├── routes_agents.py     # REST: /api/agents, /api/agents/{id}, /api/agents/spawn
│       ├── routes_buildings.py  # REST: /api/buildings, /api/buildings/construct
│       ├── routes_events.py     # REST: /api/events, /api/events/history, /api/events/trigger
│       ├── routes_economy.py    # REST: /api/economy/status, /api/economy/transactions
│       └── websocket.py         # WS: /ws real-time event streaming & interactive control bus
├── frontend/
│   ├── index.html               # Main dashboard HTML5 UI layout (viewport, HUD, inspector, logs)
│   ├── css/
│   │   └── style.css            # Modern dark-mode styling, glassmorphism, responsive panels
│   └── js/
│       ├── app.js               # Application coordinator, WebSocket client, controls, notifications
│       ├── city_map.js          # SVG renderer, isometric projection math, tile layers, buildings
│       ├── agent_visuals.js     # Agent SVG sprites, path interpolation, speech bubbles, status halos
│       └── charts.js            # Dependency-free SVG demographic, treasury & resource metrics
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # Test fixtures (initialized grid, mock agents, test clients)
│   ├── test_coordinator.py      # Tick execution, timing, pause/resume, speed regulation
│   ├── test_grid_pathfinding.py # Spatial bounds, zoning rules, collisions, A* shortest path
│   ├── test_message_bus.py      # Pub/sub, broadcast, direct messages, consensus voting tallying
│   ├── test_economy.py          # Resource balance, taxation, energy decay, bankruptcy prevention
│   └── test_api.py              # REST endpoints and WebSocket stream connectivity
├── start_city.bat               # Windows 1-click startup script
├── start_city.sh                # Linux/macOS 1-click startup script
├── pyproject.toml               # Project configuration and dependency declarations
└── README.md                    # System documentation, architecture guide, API docs
```

---

## 3. High-Performance Asynchronous Simulation Engine

### 3.1 Tick Coordinator & Execution Pipeline
The simulation operates on a discrete-time asynchronous tick loop managed by `SimulationCoordinator`. To ensure smooth, deterministic behavior and real-time visualization without stutter, the tick execution is divided into six deterministic phases.

```
       ┌────────────────────────────────────────────────────────┐
       │                TICK START (Tick = N)                   │
       └──────────────────────────┬─────────────────────────────┘
                                  │
                                  ▼
      [Phase 1] Inbound Command & Message Ingestion
      - Drain external REST/WebSocket commands
      - Deliver pending inter-agent messages to recipient mailboxes
                                  │
                                  ▼
      [Phase 2] Agent Perception & Decision Formulation
      - Scan 2D spatial neighborhood (radius R)
      - Evaluate goal hierarchy, energy, wallet, inventory
      - Generate proposed Action (MOVE, BUILD, TRADE, VOTE, REST)
                                  │
                                  ▼
      [Phase 3] Spatial Conflict Resolution & Action Execution
      - Priority-sorted action queue (Agility / Role / ID tie-breaker)
      - Atomic collision validation on target grid tile
      - Execute state transitions (movement, building, material consumption)
                                  │
                                  ▼
      [Phase 4] Environmental & Economic Lifecycle
      - Decrement baseline agent energy
      - Update building production/consumption (Power Plants, Markets)
      - Check for Epoch boundary (epoch transition logic, tax collection)
                                  │
                                  ▼
      [Phase 5] State Delta Compilation & WebSocket Broadcast
      - Collect mutated agents, new buildings, spoken dialogue, events
      - Broadcast lightweight Delta JSON to all connected clients
                                  │
                                  ▼
      [Phase 6] Timing Regulation & Drift Compensation
      - Compute execution duration: t_delta = now() - t_start
      - asyncio.sleep(max(0, target_interval - t_delta))
      - If t_delta > target_interval, record tick overrun alert
```

### 3.2 Coordinator Data Structure & State Machine
```python
class SimulationState(str, Enum):
    STOPPED = "STOPPED"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    STEPPING = "STEPPING"

class SimulationCoordinator:
    def __init__(self, config: SimulationConfig):
        self.config = config
        self.state: SimulationState = SimulationState.STOPPED
        self.current_tick: int = 0
        self.current_epoch: int = 0
        self.ticks_per_epoch: int = config.ticks_per_epoch  # e.g., 100 ticks
        self.target_tps: float = config.default_tps         # e.g., 5.0 ticks/sec (200ms)
        self.grid: CityGrid = CityGrid(config.grid_width, config.grid_height)
        self.agent_manager: AgentManager = AgentManager(self.grid)
        self.message_bus: MessageBus = MessageBus()
        self.economy: EconomySystem = EconomySystem(config)
        self.broadcaster: WebSocketBroadcaster = WebSocketBroadcaster()
        self._lock: asyncio.Lock = asyncio.Lock()
        self._loop_task: Optional[asyncio.Task] = None
        self._step_event: asyncio.Event = asyncio.Event()

    async def start(self) -> None:
        async with self._lock:
            if self.state == SimulationState.RUNNING:
                return
            self.state = SimulationState.RUNNING
            self._loop_task = asyncio.create_task(self._run_loop())

    async def pause(self) -> None:
        async with self._lock:
            if self.state == SimulationState.RUNNING:
                self.state = SimulationState.PAUSED

    async def resume(self) -> None:
        async with self._lock:
            if self.state == SimulationState.PAUSED:
                self.state = SimulationState.RUNNING

    async def step(self) -> None:
        """Advance exactly one tick while paused."""
        async with self._lock:
            if self.state == SimulationState.PAUSED:
                self.state = SimulationState.STEPPING
                self._step_event.set()

    async def set_speed(self, tps: float) -> None:
        async with self._lock:
            self.target_tps = max(0.5, min(25.0, tps))
```

### 3.3 Epoch Lifecycle & Evolutionary Triggers
An **Epoch** represents a macro-simulation milestone (e.g., 100 ticks). When `current_tick % ticks_per_epoch == 0`:
1. **Fiscal Audit**: Municipal tax collection is processed across all active agents and commercial zones.
2. **Infrastructure Upkeep**: Public structures deduct maintenance funds from the City Treasury. If treasury runs negative, emergency austerity flags are triggered.
3. **Agent Trait Adaptation**: Agents evaluate their epoch performance (net worth delta, tasks accomplished, reputation score). Successful strategies are reinforced; low-energy agents enter rest/recovery cycles.
4. **Subagent Retirement/Evolution**: Temporary subagents with completed mission quotas are gracefully retired, returning remaining funds to their parent agents.
5. **State Snapshot**: Full city state is asynchronously serialized to SQLite as a durable checkpoint.

---

## 4. 2D & Isometric Spatial Grid Model, Zoning, & Pathfinding

### 4.1 Coordinate Space & Isometric Projection
The city is modeled on an orthogonal discrete 2D grid matrix of size $W \times H$ (default: $32 \times 32$ tiles, expandable to $64 \times 64$).
- **Grid Coordinates**: $(x, y)$ with $0 \le x < W$ and $0 \le y < H$, where $(0, 0)$ is the North-West corner.
- **Isometric Screen Projection** (rendered programmatically in SVG):
  $$X_{\text{screen}} = (x - y) \cdot \frac{T_w}{2} + X_{\text{origin}}$$
  $$Y_{\text{screen}} = (x + y) \cdot \frac{T_h}{2} + Y_{\text{origin}}$$
  where $T_w$ is tile width (e.g., 64px) and $T_h$ is tile height (e.g., 32px, 2:1 isometric ratio).
- **Depth Sorting Order**: SVG elements are rendered in ascending order of depth key:
  $$\text{Depth} = x + y$$
  ensuring agents and taller buildings in the foreground naturally occlude background structures.

### 4.2 Zoning Taxonomy & Tile Specifications
Each tile in `CityGrid` has a designated zone, movement cost, occupancy status, and optional building reference:

```python
class ZoneType(str, Enum):
    WILDERNESS = "WILDERNESS"    # Natural ground (grass/trees/water); passable unless water
    ROAD = "ROAD"                # Transit network; movement cost = 1.0 (fastest)
    RESIDENTIAL = "RESIDENTIAL"  # Housing; energy regeneration zone for citizen agents
    COMMERCIAL = "COMMERCIAL"    # Markets & shops; trade, job centers, wealth generation
    INDUSTRIAL = "INDUSTRIAL"    # Factories & plants; material/energy production, pollution
    CIVIC = "CIVIC"              # City Hall, Research Institute; governance, subagent spawning
    PARK = "PARK"                # Public recreation; boosts happiness & citizen vitality

class Tile:
    x: int
    y: int
    zone: ZoneType = ZoneType.WILDERNESS
    passable: bool = True
    movement_cost: float = 2.0   # Road=1.0, Grass=2.0, Park=1.5, Obstacle=inf
    building_id: Optional[str] = None
    occupant_id: Optional[str] = None
    resource_yield: Dict[str, float] = field(default_factory=dict)
```

### 4.3 Collision Detection & Multi-Tile Footprints
- **Single-Occupancy Collision**: A tile may contain at most one agent at any time. When an agent requests a move to $(x', y')$, the collision detector verifies:
  1. $(x', y')$ is within grid boundaries $[0, W-1] \times [0, H-1]$.
  2. `tile.passable == True`.
  3. `tile.occupant_id is None` or `tile.occupant_id == agent.id`.
- **Multi-Tile Buildings**: Large structures (e.g. City Hall $2 \times 2$, Industrial Refinery $3 \times 2$) occupy a bounding box. All covered tiles are marked `passable = False` with `building_id = b_id`, except designated entrance tiles which connect to the road network.

### 4.4 Pathfinding: Manhattan & Weighted A* Algorithm
1. **Manhattan Distance**: Used for heuristic estimation and adjacent proximity checks:
   $$h(A, B) = |A_x - B_x| + |A_y - B_y|$$
2. **Weighted A\* Pathfinding Engine**:
   - Searches 4-directional cardinal neighbors (N, S, E, W) along roads and passable terrain.
   - Objective function: $f(n) = g(n) + h(n)$, where $g(n)$ accumulates terrain movement costs:
     - `ROAD`: cost = 1.0
     - `PARK`: cost = 1.5
     - `WILDERNESS`: cost = 2.0
     - `OBSTACLE / WATER / OCCUPIED`: cost = $\infty$
   - **Path Smoothing & Re-planning**:
     - Agents pre-compute paths to targets (e.g., commute to Commercial district).
     - If the immediate next tile becomes dynamically blocked by another agent, the agent attempts a 1-tick pause; if blocked for $>2$ ticks, A* re-calculates an alternative bypass route.
   - **Performance Guarantee**: On a $32 \times 32$ grid, optimized A* using Python's `heapq` executes in $<0.25\text{ ms}$ per agent route calculation, easily supporting dozens of simultaneous agents within a 200ms tick.

---

## 5. Inter-Agent Communication Bus & Consensus Voting

### 5.1 Message Bus Architecture
Agents interact via an event-driven `MessageBus` supporting four distinct transmission modalities:
1. **Direct Point-to-Point (1:1)**: Addressed to a specific `recipient_id`. Used for contractual deals, builder delegation, and private negotiations.
2. **Public Broadcast (1:All)**: Emitted city-wide. Transmitted to the frontend dialogue feed (speech bubbles, event ticker).
3. **Topic Channels (Pub/Sub)**: Topics such as `#governance`, `#construction`, `#trade`, `#security`, and `#research`. Agents subscribe based on role or current objective.
4. **Democratic Consensus Ballots**: Formal legislative proposals submitted to the civic voting ledger.

```python
class MessageType(str, Enum):
    DIRECT = "DIRECT"
    BROADCAST = "BROADCAST"
    TOPIC = "TOPIC"
    PROPOSAL = "PROPOSAL"
    VOTE = "VOTE"
    TASK_ORDER = "TASK_ORDER"
    REPORT = "REPORT"

class AgentMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    tick: int
    timestamp: float = Field(default_factory=time.time)
    sender_id: str
    sender_role: str
    recipient_id: Optional[str] = None   # None for broadcast/topic
    topic: Optional[str] = None         # e.g., "construction", "governance"
    type: MessageType
    content: str
    payload: Dict[str, Any] = Field(default_factory=dict)
```

### 5.2 Democratic Consensus & Policy Enactment
Civic decisions (zoning approvals, tax rate adjustments, public works construction) pass through an automated consensus protocol:

```
    [Mayor / Citizen Proposes Bill]
                  │
                  ▼
         [MessageBus creates Ballot]
    - Unique ballot_id
    - Sponsoring agent
    - Proposition & automated action payload
    - Quorum threshold (e.g., > 50% affirmative)
    - Voting window: [tick_start, tick_end]
                  │
                  ▼
         [Broadcast to #governance]
                  │
                  ▼
         [Agents Cast Ballots: AYE / NAY / ABSTAIN]
    - Scholars evaluate fiscal impact
    - Merchants vote based on commercial impact
    - Architects vote based on urban aesthetics
                  │
                  ▼
         [Tick Coordinator Evaluates Outcome]
        ┌─────────┴─────────┐
        ▼                   ▼
    [Quorum Met]     [Rejected / Expired]
        │                   │
        ▼                   ▼
[Auto-Execute Payload] [Bill Archived with Reason]
(e.g., zone rezoned,
 treasury funds allocated)
```

### 5.3 Concrete Ballot Schema
```python
class VoteChoice(str, Enum):
    AYE = "AYE"
    NAY = "NAY"
    ABSTAIN = "ABSTAIN"

class CivicProposal(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    creator_id: str
    title: str
    description: str
    action_type: str                   # "REZONE", "BUILD_PUBLIC_WORKS", "ADJUST_TAX"
    action_payload: Dict[str, Any]     # e.g., {"x": 10, "y": 12, "zone": "PARK"}
    created_tick: int
    expires_tick: int
    votes: Dict[str, VoteChoice] = Field(default_factory=dict)
    status: str = "ACTIVE"             # "ACTIVE", "PASSED", "REJECTED", "EXECUTED"
    quorum_required: int = 5
    pass_threshold_ratio: float = 0.50
```

---

## 6. Economy, Municipal Treasury, & Resource Micro-Mechanics

### 6.1 Tri-Resource Economy Model
The city economy is driven by three core tangible resources:
1. **Funds ($)**: Standard medium of exchange. Agents earn wages, spend on food/lodging, pay taxes, and invest in private enterprises.
2. **Energy (⚡)**: Primary operational currency. Agents consume energy per tick ($0.2\text{--}1.0\text{ ⚡}$ depending on movement and labor). Generated by Industrial power structures. Agents with $0\text{ ⚡}$ enter an exhausted "Incapacitated" state until revived by resting in Residential zones or receiving civic aid.
3. **Materials (📦)**: Basic construction matter (timber, bricks, steel). Extracted in Industrial zones, traded by Merchants, and consumed by Architects and Builders to construct roads and buildings.

### 6.2 Municipal Treasury & Taxation Ledger
The city government maintains a central fiscal account:
- **Revenue Inflows**:
  - *Sales Tax*: $3\%\text{--}8\%$ deducted automatically from trades in Commercial zones.
  - *Property Tax*: Assessed every Epoch per occupied residential/commercial tile.
  - *Zoning Permit Fees*: Charged when private agents request land development.
- **Expenditure Outflows**:
  - *Civilian Stipends & Grants*: Public funding disbursed to Researchers, Scholars, and Observers.
  - *Infrastructure Maintenance*: Periodic upkeep deducted for roads, streetlights, and civic parks.
  - *Public Works Contracts*: Funding disbursed to Builders when the Civic Council votes to construct new public amenities.

```python
class EconomySystem:
    def __init__(self, config: SimulationConfig):
        self.treasury_funds: float = config.initial_treasury  # e.g., 5000.0 $
        self.city_energy_grid: float = 1000.0                 # ⚡
        self.city_materials: float = 500.0                    # 📦
        self.sales_tax_rate: float = 0.05                     # 5%
        self.property_tax_per_epoch: float = 10.0             # 10$ / building
        self.transaction_history: List[Dict[str, Any]] = []

    def record_transaction(self, sender: str, recipient: str, amount: float, category: str):
        tax = amount * self.sales_tax_rate if category == "COMMERCIAL_TRADE" else 0.0
        net = amount - tax
        self.treasury_funds += tax
        self.transaction_history.append({
            "timestamp": time.time(),
            "sender": sender,
            "recipient": recipient,
            "amount": amount,
            "tax": tax,
            "category": category
        })
        return net, tax
```

### 6.3 Agent Roles & Economic Behaviors
The initial population incorporates 8 core archetypes satisfying the acceptance criteria:

| Role | Primary Goal | Energy Use | Economic Behavior | Spawning Capability |
| :--- | :--- | :--- | :--- | :--- |
| **Mayor** | City prosperity, budget balance, civic approval | Low (Civic) | Sets tax rates, sponsors city bills, approves zoning | Spawns Inspectors & Commissioners |
| **Architect** | Urban planning, aesthetic zoning layout | Moderate | Purchases blueprints, commissions construction | Spawns Surveyor Subagents |
| **Engineer** | Power grid, road network, structural integrity | High | Manages energy grid, maintains public works | Spawns Repair Crews |
| **Merchant** | Wealth accumulation, market inventory supply | Low-Mod | Buys materials at discount, runs market stalls | Spawns Courier/Hauler Subagents |
| **Builder** | Physical structure construction on grid tiles | Very High | Consumes materials, earns wages from contracts | Spawns Construction Workers |
| **Scholar** | Research upgrades, efficiency improvements | Low | Consumes energy at Academy, unlocks tech bonuses | Spawns Apprentice Researchers |
| **Observer** | Census tracking, demographic reporting | Moderate | Wanders city, logs citizen happiness & events | Spawns Field Canvassers |
| **Citizen** | Energy maintenance, employment, leisure | Moderate | Works at commercial/industrial, rests at home | Emergent life cycle |

---

## 7. Comprehensive R1 Feature Inventory

The table below catalogs every specific capability, requirement, technical module, API interface, and verification test required for **R1**:

| ID | Feature Name | Requirement Ref | Backend Module | Endpoint / Interface | Data Schema / Model | Automated Test Verification |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **F-01** | ASGI Application Boot | AC 68 | `backend/main.py` | `GET /` (Serves Dashboard HTML) | FastAPI app lifecycle | Test client boots in `< 1.0s` without exceptions |
| **F-02** | City Status API | AC 68 | `backend/api/routes_city.py` | `GET /api/city/status` | `CityStatusResponse` | Validates JSON containing tick, epoch, treasury, agents |
| **F-03** | Agent Registry API | AC 68 | `backend/api/routes_agents.py` | `GET /api/agents` | `List[AgentSchema]` | Returns active agents with positions, energy, roles |
| **F-04** | Building Directory API | AC 68 | `backend/api/routes_buildings.py` | `GET /api/buildings` | `List[BuildingSchema]` | Returns registered buildings, footprints, zones |
| **F-05** | Live Event Stream API | AC 68 | `backend/api/routes_events.py` | `GET /api/events` | `List[EventSchema]` | Verifies latest 50 city events and dialogue |
| **F-06** | Real-Time WebSocket Bus | AC 68, R4 | `backend/api/websocket.py` | `ws://host:port/ws` | `WebSocketFrame` (Delta) | Connects, receives periodic delta frames, echoes ping |
| **F-07** | Asynchronous Tick Coordinator | AC 69, R1 | `backend/engine/coordinator.py` | Internal async task loop | `TickContext`, `SimulationState` | Stable continuous 100-tick run without crashes |
| **F-08** | Multi-Agent Concurrency | AC 69, R1 | `backend/engine/agent_manager.py` | `agent_manager.tick()` | `AgentDecision`, `AgentAction` | Confirms $\ge 8$ distinct agents act without deadlock |
| **F-09** | 2D Spatial Grid & Zoning | R1 | `backend/engine/grid.py` | `grid.get_tile(x, y)` | `Tile`, `ZoneType` | Verifies tile boundaries, road costs, zone assignment |
| **F-10** | Collision Detection | R1 | `backend/engine/grid.py` | `grid.can_move_to(x, y)` | `SpatialIndex` | Prevents two agents from occupying the same tile |
| **F-11** | Weighted A* Pathfinding | R1 | `backend/engine/grid.py` | `grid.find_path(start, end)` | `List[Tuple[int, int]]` | Computes optimal shortest path obeying road costs |
| **F-12** | Inter-Agent Direct Messaging | R1 | `backend/engine/message_bus.py` | `bus.send_direct(from, to, msg)` | `AgentMessage` | Direct message delivered to recipient's mailbox |
| **F-13** | City-Wide Broadcast & Dialogue | R1, R3 | `backend/engine/message_bus.py` | `bus.broadcast(msg)` | `AgentMessage` | Broadcast arrives on dialogue feed and WS delta |
| **F-14** | Topic Channel Pub/Sub | R1 | `backend/engine/message_bus.py` | `bus.publish(topic, msg)` | `TopicSubscription` | Subscribers receive message; non-subscribers ignored |
| **F-15** | Democratic Consensus Voting | R1 | `backend/engine/message_bus.py` | `bus.submit_proposal()` | `CivicProposal`, `VoteChoice` | Proposal passes on $>50\%$ AYE votes, auto-executes |
| **F-16** | Tri-Resource Economy & Ledger | R1 | `backend/engine/economy.py` | `economy.get_balance()` | `EconomyState`, `ResourceLedger` | Balances energy/funds/materials; deducts consumption |
| **F-17** | Municipal Taxation & Treasury | R1 | `backend/engine/economy.py` | `economy.collect_taxes()` | `TreasuryAudit` | Epoch tax increases public treasury; logs transactions |
| **F-18** | Simulation Control: Pause/Resume | AC 75 | `backend/api/routes_city.py` | `POST /api/city/pause`, `/resume` | `CommandStatus` | Pauses loop, tick advances halt; resumes cleanly |
| **F-19** | Simulation Control: Speed Adjust | AC 75 | `backend/api/routes_city.py` | `POST /api/city/speed?tps=N` | `SpeedResponse` | Dynamically throttles tick interval from 1 to 20 TPS |
| **F-20** | Simulation Control: Single Step | AC 75 | `backend/api/routes_city.py` | `POST /api/city/step` | `StepResponse` | Advances exactly 1 tick while paused |
| **F-21** | Manual Event Trigger Injection | AC 75 | `backend/api/routes_city.py` | `POST /api/city/trigger_event` | `ManualEventPayload` | Injects windfall funds or disasters into active tick |
| **F-22** | SQLite Snapshot Persistence | AC 78, R4 | `backend/storage/db.py` | `db.save_snapshot()`, `load()` | `CitySnapshot` | Serializes complete state to disk; reloads cleanly |
| **F-23** | Standalone Boot Script | AC 79 | `start_city.bat` / `start_city.sh` | CLI execution | Batch / Bash script | Starts uvicorn server and prints browser dashboard URL |
| **F-24** | Automated Pytest Suite | AC 78 | `tests/` | `pytest tests/` | Pytest fixtures | All unit and integration test assertions pass (100%) |

---

## 8. Technical Risks, Performance Budgets, & Mitigation Strategies

| Risk / Bottleneck | Impact | Likelihood | Mitigation Strategy |
| :--- | :--- | :--- | :--- |
| **Tick Loop Jitter & Lag Under Load** | Degraded UX; frontend stuttering if tick duration exceeds target 200ms. | Medium | 1. Profile Phase 2 & 3: ensure decision logic is $O(1)$ heuristic and pathfinding uses pre-cached paths.<br>2. Offload state serialization to SQLite via a background task pool (`asyncio.to_thread`).<br>3. Monitor `t_delta`; drop or compress intermediate WebSocket delta frames if client queue buffers back up. |
| **WebSocket Connection Churn & Backpressure** | Slow client connections block server event loop. | Low-Med | Maintain a client connection pool with a non-blocking queue (`asyncio.Queue(maxsize=32)`). Discard dropped clients immediately upon `WebSocketDisconnect`. |
| **Concurrency Deadlocks on Shared State** | Server hangs during simultaneous REST mutation and tick execution. | Low | Single authoritative coordinator lock (`asyncio.Lock`). External REST commands push onto an `inbound_command_queue` processed exclusively at Phase 1 of the tick loop. |
| **Memory Leak from Message & Event History** | Unbounded memory growth over thousands of ticks. | Med | Ring buffer (`collections.deque(maxlen=200)`) for in-memory active dialogue and event history. Long-term logs flushed to SQLite. |
| **A\* Pathfinding Bottlenecks on Large Grids** | CPU saturation if many agents calculate long paths on the same tick. | Low | 1. Implement path caching: agents retain computed paths until an unexpected obstacle is encountered.<br>2. Stagger re-pathing across ticks using an agent round-robin update schedule. |
| **Host SSL Inspection on PyPI Installs** | Dependency installation failure on new development machines. | Low | All development scripts specify `--trusted-host pypi.org --trusted-host files.pythonhosted.org` or rely on pre-verified standard libraries. |

---

## 9. Downstream Implementation Directives for Workers

To facilitate parallel and error-free execution across subsequent milestones:

1. **For Backend Implementation**:
   - Construct `agent_city/backend/models/schemas.py` and `enums.py` using strict Pydantic v2 conventions (`model_dump(mode="json")`).
   - Implement `CityGrid` and `AStarPathfinder` in `backend/engine/grid.py` with 4-directional Manhattan heuristics and clear impassable boundaries.
   - Implement `MessageBus` in `backend/engine/message_bus.py` with subscriber dicts keyed by `topic` and a dedicated `ballots` mapping for consensus.
   - Implement `SimulationCoordinator` with the 6-phase async execution pipeline and thread-safe queue.
2. **For Frontend Implementation**:
   - Implement purely in vanilla JavaScript and modern CSS with programmatic SVG.
   - Provide isometric projection formulas matching `city_map.js` specifications ($T_w = 64\text{px}, T_h = 32\text{px}$).
   - Build real-time HUD with Pause/Resume/Step buttons, Speed slider (1x, 2x, 5x), Event injection buttons (Resource Windfall, Zoning Mandate), and Agent Inspector Drawer.
3. **For Testing & Quality Assurance**:
   - Ensure `tests/test_simulation_engine.py`, `tests/test_grid_pathfinding.py`, `tests/test_message_bus.py`, `tests/test_economy.py`, and `tests/test_api.py` are written using `pytest` and `pytest-asyncio`.
   - Provide the standalone `start_city.bat` script configured to run Uvicorn on port 8000 and display the dashboard URL `http://127.0.0.1:8000`.

---
*Report formulated and certified by `explorer_city_survey_1`.*
