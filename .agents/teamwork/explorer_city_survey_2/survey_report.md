# Technical Survey & Architectural Specification: Autonomous Agents, Civic Roles, Hierarchical Subagents & Generative Evolution

**Agent**: `explorer_city_survey_2`  
**Milestone**: M1 Survey / M2 Planning  
**Target Module**: `agent_city/agents/`  
**Target Specification**: R2 & Agent Decision Engine of `ORIGINAL_REQUEST.md` (2026-09-30T16:39:54Z)  
**Date**: 2026-09-30  

---

## 1. Executive Summary & Problem Scope

The `agent_city` simulation requires an autonomous, resilient, and life-like multi-agent system where agents are not mere rigid automata or simple random-walkers, but self-directed civic actors possessing:
1. **Homeostatic drives & economic constraints**: Energy depletion, resting needs, monetary budgets, material inventories, and tax obligations.
2. **Distinct civic roles & specialized agendas**: At least six core civic roles (Mayor, Architect, Engineer, Merchant, Scholar, Observer) with unique goal priorities, action vocabularies, communication templates, and inter-role dependencies.
3. **Hierarchical subagent spawning & task delegation**: The ability for senior agents to instantiate temporary task-bound subagents (e.g. Surveyors, Construction Crews, Research Assistants, Couriers) or permanent district officials, manage delegation contracts, track lineage, and cleanly retire/terminate them upon task completion without resource or memory leaks.
4. **Generative evolution & behavioral adaptation**: A 7-dimensional continuous trait genome (Diligence, Innovation, Sociability, Thriftiness, Altruism, Adaptability, Risk Tolerance) influencing decision utility, subject to epochal fitness scoring, elitism, guided mutation, and generational inheritance.

This survey establishes the complete technical blueprint, data structures, state machines, utility formulations, protocols, and feature inventories required to implement Milestone 2.

---

## 2. Autonomous Agent Lifecycle & Decision Engine

### 2.1 BaseAgent Architecture & Data Models

All agents in `agent_city` inherit from `BaseAgent`, structured as a strongly typed Pydantic v2 model supporting zero-overhead serialization into JSON and SQLite.

```python
# agent_city/agents/base.py
from __future__ import annotations
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any
from pydantic import BaseModel, Field

class AgentState(str, Enum):
    IDLE = "IDLE"                    # Awaiting stimulus or next decision cycle
    PERCEIVING = "PERCEIVING"        # Gathering sensory input from grid & inbox
    DELIBERATING = "DELIBERATING"    # Evaluating goal utilities & ranking candidate actions
    MOVING = "MOVING"                # Traversing path towards target coordinate
    EXECUTING = "EXECUTING"          # Actively performing work (building, trading, etc.)
    COMMUNICATING = "COMMUNICATING"  # Sending message, proposal, or vote
    RESTING = "RESTING"              # Recovering energy in residential zone or park
    RETIRED = "RETIRED"              # Task complete / decommissioned (subagents & expired)

class CivicRole(str, Enum):
    MAYOR = "MAYOR"
    ARCHITECT = "ARCHITECT"
    ENGINEER = "ENGINEER"
    MERCHANT = "MERCHANT"
    SCHOLAR = "SCHOLAR"
    OBSERVER = "OBSERVER"
    # Subagent Roles:
    SURVEYOR = "SURVEYOR"
    CONSTRUCTION_CREW = "CONSTRUCTION_CREW"
    RESEARCH_ASSISTANT = "RESEARCH_ASSISTANT"
    COURIER = "COURIER"
    DISTRICT_SUPERVISOR = "DISTRICT_SUPERVISOR"

class ResourceType(str, Enum):
    FUNDS = "FUNDS"                  # Standard currency tokens
    WOOD = "WOOD"                    # Basic construction material
    STONE = "STONE"                  # Medium construction material
    STEEL = "STEEL"                  # Heavy construction & infrastructure
    TECH_PARTS = "TECH_PARTS"        # Advanced research & civic efficiency

class TraitVector(BaseModel):
    diligence: float = Field(0.5, ge=0.0, le=1.0)       # Focus vs task abandonment
    innovation: float = Field(0.5, ge=0.0, le=1.0)      # Novelty vs conventional blueprints
    sociability: float = Field(0.5, ge=0.0, le=1.0)     # Frequency of communication & voting
    thriftiness: float = Field(0.5, ge=0.0, le=1.0)     # Capital preservation vs spending
    altruism: float = Field(0.5, ge=0.0, le=1.0)        # Public good vs private enrichment
    adaptability: float = Field(0.5, ge=0.0, le=1.0)    # Speed of strategy realignment
    risk_tolerance: float = Field(0.5, ge=0.0, le=1.0)  # Speculation vs safe actions

class AgentMemory(BaseModel):
    recent_actions: List[Dict[str, Any]] = Field(default_factory=list)
    known_agents: Dict[str, float] = Field(default_factory=dict) # agent_id -> trust_score [-1.0, 1.0]
    visited_parcels: List[Tuple[int, int]] = Field(default_factory=list)
    active_contracts: List[str] = Field(default_factory=list)
    historical_contributions: float = 0.0

class BaseAgent(BaseModel):
    agent_id: str
    name: str
    role: CivicRole
    state: AgentState = AgentState.IDLE
    
    # Spatial Positioning
    position: Tuple[int, int] = (0, 0)
    target_position: Optional[Tuple[int, int]] = None
    current_path: List[Tuple[int, int]] = Field(default_factory=list)
    vision_radius: int = 5
    
    # Homeostatic & Economic Energy
    energy: float = Field(100.0, ge=0.0, le=100.0)
    max_energy: float = 100.0
    energy_burn_rate: float = 0.5            # Base metabolic cost per tick
    funds: float = Field(100.0, ge=0.0)
    materials: Dict[ResourceType, int] = Field(default_factory=lambda: {
        ResourceType.WOOD: 10,
        ResourceType.STONE: 5,
        ResourceType.STEEL: 2,
        ResourceType.TECH_PARTS: 0
    })
    
    # Behavioral Traits & Evolution
    traits: TraitVector = Field(default_factory=TraitVector)
    generation: int = 1
    birth_epoch: int = 1
    fitness_score: float = 0.0
    
    # Hierarchical Subagent Linkage
    parent_id: Optional[str] = None
    child_ids: List[str] = Field(default_factory=list)
    is_temporary: bool = False
    lifespan_ticks: Optional[int] = None     # Max ticks before forced retirement
    ticks_alive: int = 0
    
    # Cognitive & Memory Stores
    memory: AgentMemory = Field(default_factory=AgentMemory)
    current_goal: Optional[str] = None
    current_action: Optional[Dict[str, Any]] = None
    action_ticks_remaining: int = 0
```

---

### 2.2 Finite State Machine (FSM) Specification

The agent lifecycle obeys a deterministic, event-driven state machine ensuring consistency, preventing deadlocks, and supporting async tick synchronization.

```
       +--------------------------------------------------------+
       |                                                        |
       v                                                        | (Energy < 15)
   [ IDLE ] ----------> [ PERCEIVING ] ----------> [ DELIBERATING ] 
       ^                     |                            |
       |                     | (No valid action)          |
       |                     +----------------------------+
       |                                                  |
       |           +--------------------------------------+
       |           |                |                     |
       |           v                v                     v
       |      [ MOVING ]       [ EXECUTING ]       [ COMMUNICATING ]
       |           |                |                     |
       |           | (Arrived)      | (Finished work)     | (Message sent)
       |           +----------------+---------------------+
       |                            |
       |                            v
       +----------------------- [ RESTING ] <--- (Exhausted / Homeostasis)
                                    |
                                    | (Task complete / Lifespan expired)
                                    v
                               [ RETIRED ]
```

#### State Transition Matrix & Guard Conditions

| Source State | Event / Trigger | Guard Condition | Target State | Action / Side Effect |
|---|---|---|---|---|
| `IDLE` | Tick start | `energy > 15.0` and not retired | `PERCEIVING` | Scan vision radius, fetch unread messages |
| `IDLE` | Low energy | `energy <= 15.0` | `RESTING` | Find nearest Residential or Park parcel |
| `PERCEIVING` | Perception complete | Target parcel / need identified | `DELIBERATING` | Populate perception buffer, score candidate actions |
| `DELIBERATING` | Action chosen | Target requires travel (`dist > 0`) | `MOVING` | Compute A* path, set `current_path` |
| `DELIBERATING` | Action chosen | Agent is already at target (`dist == 0`) | `EXECUTING` | Deduct initial energy/cost, set `action_ticks_remaining` |
| `DELIBERATING` | Communication chosen | Dialogue / voting action | `COMMUNICATING` | Post message to bus, emit speech bubble |
| `DELIBERATING` | No feasible action | Utility scores all below threshold | `IDLE` | Increment idle ticks, small energy recovery |
| `MOVING` | Step taken | Path remaining > 0 | `MOVING` | Update `(x, y)`, deduct move energy cost |
| `MOVING` | Destination reached | Path empty | `EXECUTING` | Transition to target action execution |
| `EXECUTING` | Action progressing | `action_ticks_remaining > 0` | `EXECUTING` | Decrement ticks, apply intermediate labor |
| `EXECUTING` | Action finished | `action_ticks_remaining == 0` | `IDLE` | Commit building/trade/research effect, award fitness |
| `COMMUNICATING` | Message posted | Bus acknowledged | `IDLE` | Log social interaction, record in memory |
| `RESTING` | Rest tick | `energy < max_energy` | `RESTING` | Add +5 energy (Residential) or +7.5 (Park) |
| `RESTING` | Restored | `energy >= max_energy` | `IDLE` | Return to active civic duty |
| Any State | Subagent finished | `contract.status == COMPLETED` | `RETIRED` | Transfer surplus assets to parent, remove from active pool |
| Any State | Timeout reached | `ticks_alive >= lifespan_ticks` | `RETIRED` | Decommission agent, trigger parent recovery protocol |

---

### 2.3 Perception Subsystem

Agents perceive the simulation environment through a multi-modal perceptual filter:
1. **Spatial Grid Scan**:
   - Radius $r = \text{vision\_radius}$ (default 5 tiles Chebyshev distance).
   - Perceived elements: Tile zoning (Residential, Commercial, Industrial, Civic, Park, Road), building structures, construction progress, vacancy status, and neighboring agent coordinates.
2. **Message Bus Inbox**:
   - Direct messages addressed to `agent_id`.
   - Role-specific broadcast channels (e.g. `channel:engineers`, `channel:civic_council`).
   - Public proclamations and zoning referendums from the Mayor.
3. **Internal Physiological & Economic Telemetry**:
   - Current energy level, funds balance, material counts.
   - Active subagent statuses, pending contracts, and epoch tick countdown.

---

### 2.4 4-Tier Goal Hierarchy

To guarantee behavioral coherence and avoid erratic or destructive decisions, agent objectives are organized in a strict 4-Tier Goal Hierarchy:

```
+-------------------------------------------------------+
|  Tier 4: Self-Actualization & Strategic Expansion     |  (Subagent Spawning, Legacy Projects,
|                                                       |   Monument Construction, Academic Papers)
+-------------------------------------------------------+
|  Tier 3: Socio-Economic Exchange & Civic Consensus    |  (Market Trading, Material Arbitrage,
|                                                       |   Council Voting, Coalition Building)
+-------------------------------------------------------+
|  Tier 2: Civic Role Mandates                          |  (Zoning, Blueprinting, Construction,
|                                                       |   Repairs, Tax Collection, Auditing)
+-------------------------------------------------------+
|  Tier 1: Homeostasis & Physiological Survival         |  (Energy Replenishment, Shelter Seeking,
|                                                       |   Emergency Rest, Upkeep Solvency)
+-------------------------------------------------------+
```

When a Tier 1 condition is violated (e.g. `energy < 15.0`), lower-tier goals override all higher-tier civic duties. When homeostatic needs are satisfied, agents prioritize Tier 2 (their primary civic job), followed by opportunistic Tier 3 exchanges and Tier 4 expansion.

---

### 2.5 Multi-Criteria Utility Scoring Formulation

Decision deliberation evaluates candidate actions $\mathcal{A} = \{a_1, a_2, \dots, a_m\}$ using a normalized multi-factor utility function:

$$U(a) = w_{\text{need}} \cdot \mathcal{N}(a) + w_{\text{role}} \cdot \mathcal{R}(a) + w_{\text{trait}} \cdot \mathcal{T}(a) + w_{\text{feas}} \cdot \mathcal{F}(a) - \mathcal{P}_{\text{risk}}(a)$$

Where:

1. **Need Urgency** $\mathcal{N}(a) \in [0.0, 1.0]$:
   $$\mathcal{N}(a) = \begin{cases} 
   1.0 - \left(\frac{\text{energy}}{\text{max\_energy}}\right)^2 & \text{if } a = \text{REST} \\
   \frac{\text{energy}}{\text{max\_energy}} & \text{otherwise}
   \end{cases}$$

2. **Role Alignment** $\mathcal{R}(a) \in [0.0, 1.0]$:
   A static matrix weighting how centrally action $a$ fulfills the agent's core `CivicRole`.
   *(e.g. for Architect: $\mathcal{R}(\text{DRAFT\_BLUEPRINT}) = 1.0$, $\mathcal{R}(\text{TRADE\_GOODS}) = 0.2$)*.

3. **Trait Affinity** $\mathcal{T}(a) \in [0.0, 1.0]$:
   Calculated as the normalized cosine similarity between the agent's trait vector $\vec{T}$ and the action's inherent behavioral profile $\vec{A}_{\text{profile}}$:
   $$\mathcal{T}(a) = \frac{\vec{T} \cdot \vec{A}_{\text{profile}}}{\|\vec{T}\| \|\vec{A}_{\text{profile}}\|}$$
   *(e.g., an action `SPAWN_INNOVATIVE_SURVEYOR` has high innovation and risk-tolerance profile; agents with matching traits score high $\mathcal{T}$)*.

4. **Resource Feasibility** $\mathcal{F}(a) \in [0.0, 1.0]$:
   Verifies whether the agent possesses the required funds, materials, and path availability:
   $$\mathcal{F}(a) = \min\left(1.0, \frac{\text{funds}}{\text{cost}_{\text{funds}}}, \min_{k} \left(\frac{\text{materials}[k]}{\text{cost}_{\text{materials}}[k]}\right)\right)$$
   If essential resources are missing, $\mathcal{F}(a) = 0.0$, invalidating the action.

5. **Risk & Congestion Penalty** $\mathcal{P}_{\text{risk}}(a) \ge 0.0$:
   Penalizes traveling through congested parcels, working near hazard zones, or actions with high variance:
   $$\mathcal{P}_{\text{risk}}(a) = (1.0 - \text{traits.risk\_tolerance}) \cdot \text{CongestionFactor}(\text{target})$$

#### Action Selection
The agent selects action $a^* = \arg\max_{a \in \mathcal{A}} U(a)$, or applies Boltzmann exploration (Softmax) with temperature $\tau = 0.1$ when multiple actions have comparable utility.

---

### 2.6 Energy Expenditure, Fatigue & Economic Budgeting

| Activity / State | Energy Delta per Tick | Financial / Material Delta | Condition / Limits |
|---|---|---|---|
| `IDLE` | -0.2 energy | 0 | Passive metabolic decay |
| `MOVING` (Road tile) | -0.5 energy | 0 | Paved road reduces transit fatigue |
| `MOVING` (Unpaved/Rough) | -1.0 energy | 0 | Unimproved terrain fatigue |
| `RESTING` (Residential) | +5.0 energy | -$0.5 housing upkeep | Up to `max_energy` |
| `RESTING` (Park tile) | +7.5 energy | $0 (Public Good) | Recharges faster, zero cost |
| `EXECUTING` (Construct) | -2.5 energy | Consumes Stone/Wood/Steel | Earns construction fee |
| `EXECUTING` (Drafting) | -1.5 energy | -$2.0 drafting supplies | Produces Blueprint artifact |
| `EXECUTING` (Trading) | -1.0 energy | Cash flow delta | Market transaction fee paid to city |
| `EXECUTING` (Research) | -1.8 energy | -$5.0 lab reagents | Yields Research Points |
| `COMMUNICATING` | -0.3 energy | 0 | Low overhead |
| **Civic Upkeep Tax** | 0 | -$2.0 / 20 ticks | Collected by Mayor into City Treasury |

---

## 3. Distinct Civic Roles Specification

At least six core civic roles are specified, each possessing unique agendas, behavioral traits, action repertoires, and interaction dynamics.

```
       +-------------------------------------------------------------------------+
       |                                MAYOR                                    |
       |                 (City Treasury, Zoning Referendums)                     |
       +------------------------------------+------------------------------------+
                                            |
                         +------------------+------------------+
                         |                                     |
                         v                                     v
                 [ ARCHITECT ]                           [ OBSERVER ]
             (Blueprints, Layouts)                   (Census, Audits)
                         |                                     |
                         v                                     |
                 [ ENGINEER ] <--------------------------------+
             (Construction, Repairs)
                         ^
                         | (Buys materials)
                         v
                 [ MERCHANT ] <--------------------------> [ SCHOLAR ]
             (Markets, Logistics)                    (Tech Upgrades)
```

---

### 3.1 Mayor (Executive & Governance)
- **Agenda**: Citywide fiscal solvency, municipal balance, zoning expansion, citizen happiness, consensus arbitration.
- **Default Traits**: Diligence: 0.8, Innovation: 0.4, Sociability: 0.9, Thriftiness: 0.7, Altruism: 0.8, Adaptability: 0.6, Risk Tolerance: 0.3.
- **Action Set**:
  1. `issue_zoning_decree(area_bounds, target_zone)`: Re-zones parcels to balance housing vs commercial vs industrial needs.
  2. `allocate_civic_funds(recipient_id, amount, grant_type)`: Disburses treasury grants to Engineers for public works or Scholars for research.
  3. `sponsor_referendum(proposal_id, topic, options)`: Broadcasts citywide consensus vote to all agents.
  4. `collect_civic_taxes()`: Sweeps municipal taxes from all solvent agents to fund the city treasury.
- **Goal Priorities**: Solvency > Public Infrastructure > Civic Happiness > Population Growth.
- **Speech Templates**:
  - *"Treasury reserves healthy at ${amount}. Re-zoning Sector {sector} for commercial growth."*
  - *"Calling council referendum on public park expansion in district {district}."*

---

### 3.2 Architect (Urban Design & Zoning)
- **Agenda**: Spatial optimization, architectural symmetry, structural harmony, structural density balance.
- **Default Traits**: Diligence: 0.7, Innovation: 0.9, Sociability: 0.5, Thriftiness: 0.4, Altruism: 0.6, Adaptability: 0.7, Risk Tolerance: 0.6.
- **Action Set**:
  1. `draft_blueprint(building_type, parcel_id, required_materials)`: Designs a formal blueprint and registers it on the civic exchange.
  2. `inspect_parcel(parcel_id)`: Analyzes parcel soil, neighboring zones, and utility proximity.
  3. `spawn_surveyor(target_bounds)`: Spawns a temporary `Surveyor` subagent to map terrain and building potential.
  4. `propose_urban_redevelopment(sector_id)`: Submits structural re-zoning proposals to the Mayor.
- **Goal Priorities**: Blueprint Quality > Aesthetic Harmony > Parcel Suitability > Efficient Road Access.
- **Speech Templates**:
  - *"Drafted blueprint for Level 2 Commercial Hub at ({x}, {y}). Seeking construction crew."*
  - *"Dispatching Surveyor subagent to assess eastern perimeter topography."*

---

### 3.3 Engineer (Construction & Infrastructure Maintenance)
- **Agenda**: Physical construction, road laying, structural durability, utility connectivity, swift repair of decayed buildings.
- **Default Traits**: Diligence: 0.9, Innovation: 0.5, Sociability: 0.4, Thriftiness: 0.6, Altruism: 0.7, Adaptability: 0.5, Risk Tolerance: 0.4.
- **Action Set**:
  1. `construct_building(blueprint_id, parcel_id)`: Applies physical labor and materials to advance building construction.
  2. `pave_road(start_coord, end_coord)`: Converts unpaved tiles into high-speed transit roads.
  3. `repair_decayed_structure(building_id)`: Restores structural integrity of aging city assets.
  4. `spawn_construction_crew(blueprint_id, parcel_id, size)`: Instantiates a temporary `ConstructionCrew` subagent to multiply labor output.
- **Goal Priorities**: Emergency Structural Repairs > Active Construction Blueprints > Road Paving > Inventory Stocking.
- **Speech Templates**:
  - *"Beginning foundation pour at ({x}, {y}). Consuming 20 stone, 10 steel."*
  - *"Spawned Construction Crew to accelerate municipal hospital completion."*

---

### 3.4 Merchant (Commerce, Logistics & Markets)
- **Agenda**: Commodity liquidity, supply-demand arbitrage, market stall operation, profit maximization, logistics pipelines.
- **Default Traits**: Diligence: 0.8, Innovation: 0.6, Sociability: 0.8, Thriftiness: 0.8, Altruism: 0.3, Adaptability: 0.8, Risk Tolerance: 0.7.
- **Action Set**:
  1. `establish_market_stall(parcel_id)`: Opens a commercial trading depot on a Commercial parcel.
  2. `buy_resource(seller_id, resource_type, quantity, max_unit_price)`: Acquires raw resources from suppliers or other merchants.
  3. `sell_resource(buyer_id, resource_type, quantity, unit_price)`: Sells materials to Engineers and Architects.
  4. `adjust_market_prices(resource_type, new_price)`: Adjusts bid/ask prices based on local scarcity.
  5. `spawn_courier(cargo, destination)`: Instantiates a temporary `Courier` subagent for high-speed inter-district delivery.
- **Goal Priorities**: Profit Margins > Inventory Liquidity > Supply Shortage Mitigation > Low Overhead.
- **Speech Templates**:
  - *"Market stall ({x}, {y}) open: Buying Stone at $4, Selling Steel at $18."*
  - *"Dispatched Courier with 15 wood to Engineer site ({x}, {y})."*

---

### 3.5 Scholar (Research, Education & Innovation)
- **Agenda**: Knowledge accumulation, technology tree progression, efficiency enhancements, civic sentiment polling, historical archiving.
- **Default Traits**: Diligence: 0.8, Innovation: 0.95, Sociability: 0.6, Thriftiness: 0.5, Altruism: 0.8, Adaptability: 0.7, Risk Tolerance: 0.5.
- **Action Set**:
  1. `conduct_research(tech_id)`: Expends energy and reagents to unlock city upgrades (e.g. *Solar Pavement*, *Reinforced Masonry*, *Automated Logistics*).
  2. `publish_civic_study(tech_id)`: Broadcasts completed technology boost to all relevant agents (e.g., reduces Engineer construction cost by 15%).
  3. `spawn_research_assistant(topic, duration)`: Instantiates a temporary `ResearchAssistant` to survey agent sentiment and gather district metrics.
  4. `archive_epoch_annals(epoch_number)`: Compiles historical chronicle into persistent archives.
- **Goal Priorities**: Technology Breakthroughs > Sentiment Diagnostics > Archival Completeness > Educational Seminars.
- **Speech Templates**:
  - *"Research breakthrough: 'Reinforced Masonry' complete! Construction durability +25%."*
  - *"Deploying Research Assistant to poll civic happiness across Southern residential wards."*

---

### 3.6 Observer (Auditing, Census & System Diagnostics)
- **Agenda**: Impartial census tracking, economic inequality auditing (Gini index), bottleneck identification, anomaly & deadlock detection.
- **Default Traits**: Diligence: 0.95, Innovation: 0.3, Sociability: 0.5, Thriftiness: 0.9, Altruism: 0.9, Adaptability: 0.6, Risk Tolerance: 0.1.
- **Action Set**:
  1. `conduct_demographic_census()`: Computes total population, role distributions, average energy, and mortality/retirement rates.
  2. `audit_wealth_distribution()`: Calculates citywide Gini coefficient and flags extreme monopolistic wealth hoarding.
  3. `profile_transit_congestion()`: Identifies bottlenecked road intersections and alerts the Mayor/Engineer.
  4. `flag_system_anomaly(anomaly_type, payload)`: Reports idle agents, deadlocked negotiations, or resource starvation events to the event log.
- **Goal Priorities**: Data Accuracy > Anomaly Detection > Impartial Reporting > Historical Documentation.
- **Speech Templates**:
  - *"Census Update: 14 active agents, 4 subagents. Wealth Gini coefficient at 0.32."*
  - *"Transit Warning: High pedestrian congestion at intersection ({x}, {y}). Engineer intervention advised."*

---

### 3.7 Cross-Role Interaction & Dependency Matrix

| Interacting Roles | Primary Interaction Protocol | Resource / Message Flow | Failure / Bottleneck Consequence |
|---|---|---|---|
| **Mayor $\leftrightarrow$ Architect** | Zoning decrees & redevelopment requests | Mayor funds blueprints; Architect submits zoning advice | Chaotic unzoned construction or lack of building plots |
| **Mayor $\leftrightarrow$ Engineer** | Municipal infrastructure contracts | Mayor disburses public funds; Engineer builds roads/civic centers | Infrastructure decay; transit grid gridlock |
| **Architect $\leftrightarrow$ Engineer** | Blueprint delivery & construction contracts | Architect issues blueprint; Engineer constructs it | Blueprints sit idle; uncoordinated building attempts |
| **Engineer $\leftrightarrow$ Merchant** | Material supply procurement | Engineer pays funds; Merchant delivers stone/steel/wood | Construction stalls due to material shortages |
| **Scholar $\leftrightarrow$ All Roles** | Technology upgrades & efficiency buffs | Scholar unlocks tech; Engineers/Merchants gain cost/speed boosts | Stagnant economy; high resource burn rates |
| **Observer $\leftrightarrow$ Mayor/City** | Audit reports & congestion warnings | Observer flags anomalies; Mayor adjusts taxes or mandates | System imbalances, wealth disparity, unnoticed deadlocks |

---

## 4. Hierarchical Subagent Spawning System

### 4.1 Parent-Child Relationship Model & Delegation Contract

Subagents allow primary civic agents to parallelize complex or time-intensive urban tasks without stalling their own primary decision cycles.

```python
# agent_city/agents/subagents.py
from enum import Enum
from typing import Dict, Optional, Any, Tuple
from pydantic import BaseModel, Field

class DelegationStatus(str, Enum):
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    TIMED_OUT = "TIMED_OUT"

class DelegationContract(BaseModel):
    contract_id: str
    parent_id: str
    child_id: str
    task_name: str
    target_coordinates: Optional[Tuple[int, int]] = None
    allocated_funds: float = 0.0
    allocated_materials: Dict[str, int] = Field(default_factory=dict)
    max_duration_ticks: int = 30
    created_at_tick: int = 0
    status: DelegationStatus = DelegationStatus.PENDING
    result_payload: Optional[Dict[str, Any]] = None
```

#### Authority & Safety Constraints
1. **Strict Recursion Limit**: Subagents are forbidden from spawning second-order subagents (`max_depth = 1`). This permanently prevents runaway exponential agent population explosions.
2. **Parent Concurrency Caps**:
   - Mayor: Max 1 Deputy/Supervisor
   - Architect: Max 2 Surveyors
   - Engineer: Max 3 Construction Crews
   - Merchant: Max 3 Couriers
   - Scholar: Max 2 Research Assistants
   - Observer: Max 1 Census Drone
3. **Escrow Guarantee**: The parent agent's funds and materials are escrowed into the child's inventory at birth. Upon completion or retirement, all unspent resources are automatically refunded to the parent.
4. **Hard Timeout Safeguard**: Every temporary subagent has an immutable `lifespan_ticks` (e.g. 20–40 ticks). If the task is incomplete when the lifespan timer expires, the contract status transitions to `TIMED_OUT` and forced decommissioning occurs, preventing memory leaks.

---

### 4.2 Temporary vs. Permanent Subagent Archetypes

```
                     +---------------------------------------+
                     |         SUBAGENT TAXONOMY             |
                     +-------------------+-------------------+
                                         |
            +----------------------------+----------------------------+
            |                                                         |
            v                                                         v
   [ TEMPORARY SUBAGENTS ]                                   [ PERMANENT SUBAGENTS ]
   - Task-bounded lifespan                                   - Indefinite lifespan
   - Single contract execution                               - Autonomous regional governance
   - Auto-retire upon completion                             - Persists across epochs
   -------------------------------                           -------------------------------
   * Surveyor (Architect)                                    * District Supervisor (Mayor)
   * Construction Crew (Engineer)                            * Chief Guildmaster (Merchant)
   * Research Assistant (Scholar)
   * Courier (Merchant)
```

#### Detailed Archetype Specifications

1. **Surveyor (Temporary, Parent: Architect)**:
   - **Task**: Inspects a designated $K \times K$ quadrant, analyzes soil suitability, utility access, and road distance, and produces a structured `SurveyReport`.
   - **Lifespan**: 20 ticks.
   - **Seed Budget**: $15 funds, 30 energy.
   - **Retirement Trigger**: Completing inspection of target parcels or reaching 20 ticks. Emits `SURVEY_REPORT_DELIVERED` to parent Architect.

2. **ConstructionCrew (Temporary, Parent: Engineer)**:
   - **Task**: Provides 3x construction labor per tick to an active blueprint parcel, rapidly advancing the build progress bar.
   - **Lifespan**: Duration of the build (max 35 ticks).
   - **Seed Budget**: $30 funds, 50 energy, required building materials.
   - **Retirement Trigger**: Building reaches 100% completion. Emits `CONSTRUCTION_COMPLETE` to Engineer, returns remaining materials, and disbands.

3. **ResearchAssistant (Temporary, Parent: Scholar)**:
   - **Task**: Traverses city wards to poll individual agents on civic satisfaction and collect environmental readings (noise, pollution, aesthetic beauty).
   - **Lifespan**: 25 ticks.
   - **Seed Budget**: $20 funds, 40 energy.
   - **Retirement Trigger**: 5 agent interviews conducted or 25 ticks reached. Transmits `DATASET_READY` to Scholar and retires.

4. **Courier (Temporary, Parent: Merchant)**:
   - **Task**: High-speed transit (2 tiles per tick on roads) carrying heavy cargo from warehouse or market stall to a client agent's location.
   - **Lifespan**: 15 ticks.
   - **Seed Budget**: $10 funds, 35 energy.
   - **Retirement Trigger**: Cargo successfully transferred to recipient. Collects receipt, refunds profit to Merchant parent, and retires.

5. **DistrictSupervisor (Permanent, Parent: Mayor)**:
   - **Task**: Regional administration over an expanded city sector ($20 \times 20$ grid extension). Manages local traffic issues and forwards tax revenue to City Hall.
   - **Lifespan**: Indefinite (survives across epochs unless recalled by Mayor).

---

### 4.3 Spawning & Retirement Protocol Flow

```
Parent Agent                       Simulation Engine                       Subagent
     |                                     |                                   |
     | 1. check_spawn_eligibility()        |                                   |
     |    (concurrency & funds ok)         |                                   |
     |------------------------------------>|                                   |
     |                                     |                                   |
     | 2. spawn_subagent(archetype, task)  |                                   |
     |------------------------------------>| 3. Instantiate BaseAgent          |
     |                                     |    (parent_id, escrow budget)     |
     |                                     |---------------------------------->|
     | 4. Return child_id & register       |                                   |
     |<------------------------------------|                                   |
     |                                     |                                   |
     |                                     |         [ Active Work Ticks ]     |
     |                                     | <--- 5. Heartbeat & Progress ---- |
     |                                     |                                   |
     |                                     | 6. Task Complete or Timeout       |
     |                                     | <---------------------------------|
     | 7. Receive final payload & refund   | 8. Transfer unspent resources     |
     |<------------------------------------|<----------------------------------|
     |                                     | 9. Set state = RETIRED            |
     |                                     | 10. Purge from active tick queue  |
     v                                     v                                   x (Decommissioned)
```

---

## 5. Generative Evolution & Trait Adaptation

### 5.1 7-Dimensional Behavioral Trait Genome

Every agent possesses a continuous behavioral genome normalized in the range $[0.0, 1.0]$:

$$\vec{T} = \left[ T_{\text{diligence}}, T_{\text{innovation}}, T_{\text{sociability}}, T_{\text{thriftiness}}, T_{\text{altruism}}, T_{\text{adaptability}}, T_{\text{risk\_tolerance}} \right]$$

These traits directly shape decisions by modulating utility scoring $\mathcal{T}(a)$:
- High **Diligence** suppresses premature task switching.
- High **Innovation** favors high-tier blueprints, rare tech nodes, and exploratory surveying.
- High **Sociability** increases message bus participation and referendum voting frequency.
- High **Thriftiness** penalizes expensive luxury actions and prioritizes cash buffers.
- High **Altruism** boosts utility for constructing public parks, hospitals, and low-margin trade with struggling peers.
- High **Adaptability** dynamically scales utility weights when urban crises or shortages emerge.
- High **Risk Tolerance** reduces distance/congestion penalties for adventurous expeditions.

---

### 5.2 Epoch Transitions & Generational Timeline

- **Tick Duration**: 1 Simulation Tick $\approx$ 100ms–200ms real-time (configurable).
- **Epoch Duration**: 1 Epoch = 100 Ticks.
- **At Every Epoch Boundary ($t = 100, 200, 300, \dots$)**:
  1. The simulation loop suspends action execution for 1 tick to execute the **Generative Epoch Transition**.
  2. The `GenerativeEvolutionEngine` gathers performance telemetry across all active agents.
  3. Fitness scores are computed and ranked.
  4. Top performers (Elites) are preserved and designated as Exemplars.
  5. Low performers undergo guided behavioral adaptation (mutation towards exemplar centroids).
  6. Newly spawned civic agents inherit traits through exemplar crossover with stochastic mutation.

---

### 5.3 Multi-Objective Generational Fitness Function

The fitness $F_i$ of agent $i$ over the elapsed epoch is determined by four normalized pillars:

$$F_i = w_{\text{civic}} \cdot C_{\text{civic}}(i) + w_{\text{econ}} \cdot W_{\text{econ}}(i) + w_{\text{energy}} \cdot E_{\text{energy}}(i) + w_{\text{collab}} \cdot S_{\text{collab}}(i)$$

Default weights: $w_{\text{civic}} = 0.40, w_{\text{econ}} = 0.25, w_{\text{energy}} = 0.15, w_{\text{collab}} = 0.20$.

1. **Civic Duty Contribution** ($C_{\text{civic}}$):
   - **Mayor**: Balanced municipal budget, citizen satisfaction index, successful referendums.
   - **Architect**: Completed blueprints built to completion, road connectivity score.
   - **Engineer**: Total construction points delivered, structures repaired before collapse.
   - **Merchant**: Volume of goods traded, fulfillment of material requests, supply uptime.
   - **Scholar**: Technologies unlocked, academic papers published, sentiment surveys delivered.
   - **Observer**: Anomaly detection precision, census timeliness, audit reports filed.

2. **Economic Solvency** ($W_{\text{econ}}$):
   $$W_{\text{econ}} = \text{clamp}\left(\frac{\text{funds} + \sum \text{material\_value} - \text{upkeep\_debt}}{\text{target\_wealth}}, 0.0, 1.0\right)$$

3. **Energy & Survival Efficiency** ($E_{\text{energy}}$):
   Ratio of productive work ticks to total ticks, penalized by ticks spent in deep exhaustion:
   $$E_{\text{energy}} = \frac{\text{ticks}_{\text{executing}} + \text{ticks}_{\text{moving}}}{\text{ticks}_{\text{total}} + 2 \cdot \text{ticks}_{\text{exhausted}}}$$

4. **Collaborative Impact** ($S_{\text{collab}}$):
   Successful subagent delegations, trade transactions completed with peers, votes cast in referendums.

---

### 5.4 Trait Adaptation, Mutation & Crossover Mechanics

```python
# agent_city/agents/evolution.py
import random
import math
from typing import List, Tuple
from agent_city.agents.base import BaseAgent, TraitVector

class GenerativeEvolutionEngine:
    def __init__(
        self,
        mutation_rate: float = 0.15,
        mutation_scale: float = 0.08,
        breakthrough_rate: float = 0.02,
        elite_fraction: float = 0.25
    ):
        self.mutation_rate = mutation_rate
        self.mutation_scale = mutation_scale
        self.breakthrough_rate = breakthrough_rate
        self.elite_fraction = elite_fraction

    def evaluate_epoch(self, agents: List[BaseAgent], epoch: int) -> List[BaseAgent]:
        # Filter primary permanent agents
        primary_agents = [a for a in agents if not a.is_temporary and a.state != "RETIRED"]
        if not primary_agents:
            return agents

        # Sort agents by fitness score descending
        primary_agents.sort(key=lambda a: a.fitness_score, reverse=True)
        elite_count = max(1, int(len(primary_agents) * self.elite_fraction))
        elites = primary_agents[:elite_count]
        exemplar = self._compute_exemplar_centroid(elites)

        # Adapt underperforming agents
        for agent in primary_agents[elite_count:]:
            agent.traits = self._adapt_towards_exemplar(agent.traits, exemplar)
            agent.generation += 1

        return agents

    def _compute_exemplar_centroid(self, elites: List[BaseAgent]) -> TraitVector:
        avg_traits = {}
        fields = ["diligence", "innovation", "sociability", "thriftiness", "altruism", "adaptability", "risk_tolerance"]
        for field in fields:
            avg_traits[field] = sum(getattr(e.traits, field) for e in elites) / len(elites)
        return TraitVector(**avg_traits)

    def _adapt_towards_exemplar(self, current: TraitVector, exemplar: TraitVector) -> TraitVector:
        adapted = {}
        fields = ["diligence", "innovation", "sociability", "thriftiness", "altruism", "adaptability", "risk_tolerance"]
        for field in fields:
            curr_val = getattr(current, field)
            ex_val = getattr(exemplar, field)
            
            # Drift 30% towards exemplar + Gaussian perturbation
            drift = 0.3 * (ex_val - curr_val)
            noise = random.gauss(0, self.mutation_scale) if random.random() < self.mutation_rate else 0.0
            
            # Rare breakthrough / radical mutation
            if random.random() < self.breakthrough_rate:
                noise += random.choice([-0.3, 0.3])
                
            val = max(0.0, min(1.0, curr_val + drift + noise))
            adapted[field] = round(val, 3)
        return TraitVector(**adapted)

    def breed_traits(self, parent_a: TraitVector, parent_b: TraitVector) -> TraitVector:
        """Crossover & mutation for new offspring or subagent trait initialization."""
        child_dict = {}
        fields = ["diligence", "innovation", "sociability", "thriftiness", "altruism", "adaptability", "risk_tolerance"]
        for field in fields:
            # Uniform crossover with random interpolation
            alpha = random.uniform(0.3, 0.7)
            val = alpha * getattr(parent_a, field) + (1 - alpha) * getattr(parent_b, field)
            if random.random() < self.mutation_rate:
                val += random.gauss(0, self.mutation_scale)
            child_dict[field] = round(max(0.0, min(1.0, val)), 3)
        return TraitVector(**child_dict)
```

---

## 6. Comprehensive Feature Inventory for R2

| Feature ID | Feature Name | Requirement Ref | Description & Scope | Acceptance Verification Criteria | Dependencies | Risk & Mitigation |
|---|---|---|---|---|---|---|
| **FEAT-R2-01** | `BaseAgent` Model & Serialization | R1, R2 | Core Pydantic dataclass holding ID, role, position, energy, funds, materials, traits, memory, and lifecycle state. | Instantiates cleanly, serializes to/from JSON dict, enforces bounds ($0 \le \text{energy} \le 100$). | Python 3.11, Pydantic v2 | Risk: Serialization overhead on tick broadcast. *Mitigation: Exclude immutable fields from differential diffs.* |
| **FEAT-R2-02** | Agent Lifecycle State Machine | R1, R2 | FSM managing states `IDLE`, `PERCEIVING`, `DELIBERATING`, `MOVING`, `EXECUTING`, `COMMUNICATING`, `RESTING`, `RETIRED`. | Verified deterministic transitions, exhaustion forces `RESTING`, invalid actions yield fallback to `IDLE`. | Simulation Tick Engine | Risk: State deadlocks. *Mitigation: Hard action timeouts and default fallback transitions.* |
| **FEAT-R2-03** | Perception & Vision Scanner | R1, R2 | Spatial Chebyshev radius scanner returning visible parcels, buildings, neighbor agents, and unread inbox messages. | Correctly filters entities within radius $r=5$, ignores occluded/out-of-bound entities. | Spatial Grid (M1) | Risk: $O(N \cdot M)$ spatial query costs. *Mitigation: Spatial grid bucket indexing.* |
| **FEAT-R2-04** | 4-Tier Goal Hierarchy & Deliberation | R1, R2 | Hierarchical prioritization: Homeostasis > Civic Mandate > Socio-Economic > Self-Actualization. | Starved agent always prioritizes rest/food; solvent agent pursues civic duty. | `BaseAgent` | Risk: Priority thrashing. *Mitigation: Hysteresis margin before switching primary goal.* |
| **FEAT-R2-05** | Multi-Criteria Utility Engine | R1, R2 | Mathematical scoring function $U(a)$ combining need, role, trait cosine similarity, feasibility, and risk penalty. | Action with highest utility selected; unfeasible actions receive 0 score. | Python `math` | Risk: Floating-point tiebreaks. *Mitigation: Deterministic tiebreaker by action ID.* |
| **FEAT-R2-06** | Energy & Economic Balance Engine | R1, R2 | Metabolic decay per tick, rest regeneration in residential/parks, upkeep taxes, and transaction fees. | Agent energy drops with movement/work, recharges when resting, bankrupt agents incur penalties. | Simulation Engine | Risk: Premature extinction of all agents. *Mitigation: Public park free resting and municipal welfare floor.* |
| **FEAT-R2-07** | Civic Role: Mayor | R1, R2 | Executive leader managing city treasury, zoning decrees, fund allocation, and referendums. | Successfully re-zones parcels, disburses funds, triggers public votes. | Message Bus (M1), Grid (M1) | Risk: Monopolistic treasury hoarding. *Mitigation: Automatic public welfare grants when treasury exceeds cap.* |
| **FEAT-R2-08** | Civic Role: Architect | R1, R2 | Urban designer creating blueprints, inspecting parcels, commissioning surveyors, optimizing layout. | Generates valid blueprints on unzoned/vacant land, registers them for construction. | Grid (M1) | Risk: Blueprints placed on invalid tiles. *Mitigation: Grid collision & zoning checks before registration.* |
| **FEAT-R2-09** | Civic Role: Engineer | R1, R2 | Builder and maintenance specialist constructing buildings, paving roads, repairing structural decay. | Advances blueprint construction progress bar, consumes materials, restores building health. | Economy (M1), Grid (M1) | Risk: Material starvation halts construction. *Mitigation: Requests materials from Merchants via Message Bus.* |
| **FEAT-R2-10** | Civic Role: Merchant | R1, R2 | Commercial trader operating market stalls, adjusting bid/ask prices, trading materials, spawning Couriers. | Buys/sells materials, maintains inventory balance, profits from market arbitrage. | Economy (M1) | Risk: Price inflation runaway. *Mitigation: Municipal price ceilings set by Mayor.* |
| **FEAT-R2-11** | Civic Role: Scholar | R1, R2 | Researcher and educator unlocking tech tree nodes, conducting sentiment polls, publishing city boosts. | Researches tech nodes, broadcasts efficiency buffs, archives historical chronicles. | Message Bus (M1) | Risk: Irrelevant research path. *Mitigation: Prioritizes techs corresponding to current city bottlenecks.* |
| **FEAT-R2-12** | Civic Role: Observer | R1, R2 | Impartial auditor conducting censuses, measuring Gini coefficient, profiling bottlenecks, alerting Mayor. | Computes accurate population & wealth statistics, logs anomalies to event stream. | Simulation Store | Risk: Passive observer consuming ticks without value. *Mitigation: Ultra-low energy burn rate.* |
| **FEAT-R2-13** | Subagent Spawning & Delegation | R2 | Parent agents instantiate specialized subagents with delegation contracts, escrow funds, and lifespan caps. | Architect spawns Surveyor; Engineer spawns ConstructionCrew; parent-child relationship tracked. | Simulation Coordinator | Risk: Exponential subagent cascading. *Mitigation: Strict `max_depth = 1` and role concurrency caps.* |
| **FEAT-R2-14** | Subagent Retirement & Reclamation | R2 | Automatic retirement lifecycle upon task completion or lifespan timeout; escrow refund to parent. | Subagent enters `RETIRED`, unspent funds returned to parent, cleanly removed from active tick queue. | Simulation Engine | Risk: Dangling subagent references. *Mitigation: Simulation coordinator garbage collection hook.* |
| **FEAT-R2-15** | Behavioral Trait Genome (7-D) | R2 | Continuous normalized trait vector (Diligence, Innovation, Sociability, Thriftiness, Altruism, Adaptability, Risk). | Traits demonstrably bias action selection (e.g. high-thrift agent hoards cash). | Decision Engine | Risk: Degenerate extreme trait values. *Mitigation: Bounded clamping in $[0.05, 0.95]$.* |
| **FEAT-R2-16** | Generative Epoch Evolution Engine | R2 | Multi-objective fitness assessment every 100 ticks; elitism; guided adaptation towards exemplar centroids; mutation. | Epoch boundary triggers fitness calculation, low performers drift towards top performers, lineages updated. | `BaseAgent` | Risk: Premature convergence to monoculture. *Mitigation: Stochastic Gaussian noise + breakthrough mutation rate.* |

---

## 7. Recommended File Structure & Implementation Blueprint

```
agent_city/
└── agents/
    ├── __init__.py           # Package exports (BaseAgent, CivicRole, AgentState, etc.)
    ├── base.py               # BaseAgent dataclass, AgentState, TraitVector, AgentMemory
    ├── decision.py           # 4-tier goal evaluation, utility scoring formulation, FSM dispatcher
    ├── roles.py              # Concrete implementations of Mayor, Architect, Engineer, Merchant, Scholar, Observer
    ├── subagents.py          # DelegationContract, Surveyor, ConstructionCrew, ResearchAssistant, Courier
    └── evolution.py          # GenerativeEvolutionEngine, fitness calculation, trait adaptation & crossover
```

### 7.1 Class & Function Signature Blueprint

```python
# agents/decision.py
class DecisionEngine:
    @staticmethod
    def evaluate_perception(agent: BaseAgent, grid_view: Any, inbox: List[Any]) -> None:
        """Updates agent memory, sensory buffer, and current needs."""
        ...

    @staticmethod
    def select_action(agent: BaseAgent, candidate_actions: List[AgentAction]) -> AgentAction:
        """Computes U(a) for all candidate actions and returns best action."""
        ...

    @staticmethod
    def step_fsm(agent: BaseAgent, simulation_context: Any) -> None:
        """Executes one tick of the state machine for the given agent."""
        ...
```

```python
# agents/subagents.py
class SubagentManager:
    @staticmethod
    def spawn_subagent(
        parent: BaseAgent,
        archetype: CivicRole,
        task_name: str,
        target_coords: Optional[Tuple[int, int]],
        budget: float,
        materials: Dict[str, int],
        lifespan: int
    ) -> BaseAgent:
        """Validates parent limits, escrows resources, and instantiates subagent."""
        ...

    @staticmethod
    def retire_subagent(child: BaseAgent, parent: BaseAgent, reason: str) -> None:
        """Refunds unspent resources, commits results to parent memory, sets RETIRED."""
        ...
```

---

## 8. Verification & Test Plan

1. **Unit Tests (`tests/test_agents.py`)**:
   - `test_base_agent_initialization_and_serialization`: Verify Pydantic schema validation and JSON serialization.
   - `test_fsm_state_transitions`: Test transitions across `IDLE -> PERCEIVING -> DELIBERATING -> EXECUTING -> RESTING`.
   - `test_exhaustion_homeostasis_override`: Force energy to 5.0 and confirm agent aborts civic duties to seek rest.
   - `test_utility_scoring_trait_bias`: Compare action selection between high-innovation vs high-thriftiness agents.
   - `test_civic_role_action_sets`: Execute role actions for all 6 roles and verify expected state updates.
   - `test_subagent_spawning_and_escrow`: Spawn a `Surveyor` from an `Architect`, check parent funds deduction and child assignment.
   - `test_subagent_retirement_and_refund`: Complete child task, verify child state is `RETIRED` and surplus funds return to parent.
   - `test_subagent_recursion_guard`: Assert exception when a subagent attempts to spawn another subagent.
   - `test_generative_evolution_epoch_transition`: Run 100 ticks, evaluate fitness, confirm underperformers adapt traits towards exemplars.

2. **Integration Tests (`tests/test_e2e.py`)**:
   - Multi-agent 100-tick headless simulation verifying 8+ diverse civic agents and spawned subagents collaborating without exceptions, deadlocks, or orphaned agents.
