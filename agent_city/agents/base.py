"""Base agent architecture, state machine, trait vectors, memory, and goal hierarchy."""

from __future__ import annotations

import math
import uuid
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

from pydantic import BaseModel, ConfigDict, Field, model_validator


class AgentState(str, Enum):
    """8-State Finite State Machine (FSM) for autonomous civic agents."""
    IDLE = "IDLE"                    # Awaiting stimulus or next decision cycle
    PERCEIVING = "PERCEIVING"        # Gathering sensory input from grid & inbox
    DELIBERATING = "DELIBERATING"    # Evaluating goal utilities & ranking candidate actions
    MOVING = "MOVING"                # Traversing path towards target coordinate
    EXECUTING = "EXECUTING"          # Actively performing work (building, trading, etc.)
    COMMUNICATING = "COMMUNICATING"  # Sending message, proposal, or vote
    RESTING = "RESTING"              # Recovering energy in residential zone or park
    RETIRED = "RETIRED"              # Task complete / decommissioned (subagents & expired)


class CivicRole(str, Enum):
    """Primary civic roles and specialized hierarchical subagent roles."""
    # 6 Core Civic Roles
    MAYOR = "MAYOR"
    ARCHITECT = "ARCHITECT"
    ENGINEER = "ENGINEER"
    MERCHANT = "MERCHANT"
    SCHOLAR = "SCHOLAR"
    OBSERVER = "OBSERVER"

    # Specialized Subagent Roles
    SURVEYOR = "SURVEYOR"
    CONSTRUCTION_CREW = "CONSTRUCTION_CREW"
    RESEARCH_ASSISTANT = "RESEARCH_ASSISTANT"
    COURIER = "COURIER"
    DISTRICT_SUPERVISOR = "DISTRICT_SUPERVISOR"

    # Auxiliaries & Citizens
    BUILDER = "BUILDER"
    CITIZEN = "CITIZEN"


class ResourceType(str, Enum):
    """Material and commodity tokens tracked in economy and agent inventories."""
    FUNDS = "FUNDS"
    WOOD = "WOOD"
    STONE = "STONE"
    STEEL = "STEEL"
    TECH_PARTS = "TECH_PARTS"


class GoalTier(int, Enum):
    """4-Tier Goal Hierarchy from physiological homeostasis to strategic expansion."""
    HOMEOSTASIS = 1          # Energy replenish, emergency rest (energy < 15 priority override)
    CIVIC_MANDATE = 2        # Core role duty (zoning, construction, trading, research, audit)
    SOCIO_ECONOMIC = 3       # Commerce, consensus voting, coalition building
    SELF_ACTUALIZATION = 4   # Subagent spawning, monument construction, regional expansion


class TraitVector(BaseModel):
    """7-Dimensional continuous behavioral genome in [0.0, 1.0]."""
    model_config = ConfigDict(validate_assignment=True)

    diligence: float = Field(default=0.5, ge=0.0, le=1.0)       # Focus vs task switching
    innovation: float = Field(default=0.5, ge=0.0, le=1.0)      # Novelty vs conventional blueprints
    sociability: float = Field(default=0.5, ge=0.0, le=1.0)     # Frequency of communication & voting
    thriftiness: float = Field(default=0.5, ge=0.0, le=1.0)     # Capital preservation vs spending
    altruism: float = Field(default=0.5, ge=0.0, le=1.0)        # Public good vs private enrichment
    adaptability: float = Field(default=0.5, ge=0.0, le=1.0)    # Strategy realignment speed
    risk_tolerance: float = Field(default=0.5, ge=0.0, le=1.0)  # Speculation vs safe actions

    def as_vector(self) -> List[float]:
        """Return 7-D continuous trait coordinates."""
        return [
            self.diligence,
            self.innovation,
            self.sociability,
            self.thriftiness,
            self.altruism,
            self.adaptability,
            self.risk_tolerance,
        ]

    def cosine_similarity(self, other: Union[List[float], TraitVector]) -> float:
        """Compute cosine similarity between this trait vector and another."""
        v1 = self.as_vector()
        v2 = other.as_vector() if isinstance(other, TraitVector) else list(other)
        dot = sum(a * b for a, b in zip(v1, v2))
        norm1 = math.sqrt(sum(a * a for a in v1))
        norm2 = math.sqrt(sum(b * b for b in v2))
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return max(-1.0, min(1.0, dot / (norm1 * norm2)))

    def to_dict(self) -> Dict[str, float]:
        """Export traits as dictionary."""
        return {
            "diligence": self.diligence,
            "innovation": self.innovation,
            "sociability": self.sociability,
            "thriftiness": self.thriftiness,
            "altruism": self.altruism,
            "adaptability": self.adaptability,
            "risk_tolerance": self.risk_tolerance,
        }


class AgentMemory(BaseModel):
    """Short-term and episodic memory store for social trust, visited parcels, and contributions."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    recent_actions: List[Dict[str, Any]] = Field(default_factory=list)
    known_agents: Dict[str, float] = Field(default_factory=dict)  # agent_id -> trust_score [-1.0, 1.0]
    visited_parcels: List[Tuple[int, int]] = Field(default_factory=list)
    active_contracts: List[str] = Field(default_factory=list)
    historical_contributions: float = 0.0

    def record_action(self, action: Dict[str, Any], max_history: int = 20) -> None:
        """Record an executed action in rolling memory."""
        self.recent_actions.append(action)
        if len(self.recent_actions) > max_history:
            self.recent_actions.pop(0)

    def update_trust(self, agent_id: str, delta: float) -> float:
        """Update interpersonal trust score towards another agent."""
        curr = self.known_agents.get(agent_id, 0.0)
        new_val = max(-1.0, min(1.0, curr + delta))
        self.known_agents[agent_id] = new_val
        return new_val

    def visit_parcel(self, coord: Tuple[int, int], max_visited: int = 50) -> None:
        """Record a visited coordinate in spatial memory."""
        if coord not in self.visited_parcels:
            self.visited_parcels.append(coord)
            if len(self.visited_parcels) > max_visited:
                self.visited_parcels.pop(0)


class AgentGoal(BaseModel):
    """Structured goal representation with tier priority and completion status."""
    goal_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    tier: GoalTier = GoalTier.CIVIC_MANDATE
    description: str = ""
    target_type: str = ""
    target_payload: Dict[str, Any] = Field(default_factory=dict)
    urgency: float = Field(default=0.5, ge=0.0, le=1.0)
    is_completed: bool = False


class AgentAction(BaseModel):
    """Candidate or chosen action package for simulation coordinator resolution."""
    type: str = "IDLE"
    target: Optional[Tuple[int, int]] = None
    payload: Dict[str, Any] = Field(default_factory=dict)
    cost_funds: float = 0.0
    cost_materials: Dict[str, int] = Field(default_factory=dict)
    expected_utility: float = 0.0
    action_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert action to dictionary format expected by coordinator."""
        d: Dict[str, Any] = {"type": self.type, "payload": self.payload}
        if self.target is not None:
            d["target"] = self.target
        if self.cost_funds > 0:
            d["cost_funds"] = self.cost_funds
        if self.cost_materials:
            d["cost_materials"] = self.cost_materials
        return d


class BaseAgent(BaseModel):
    """
    Autonomous civic agent with 8-state FSM, 7-D traits, 4-tier goal hierarchy,
    and hierarchical subagent linkage.
    """
    model_config = ConfigDict(arbitrary_types_allowed=True, validate_assignment=True)

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
    energy: float = Field(default=100.0, ge=0.0, le=100.0)
    max_energy: float = 100.0
    energy_burn_rate: float = 0.5
    funds: float = Field(default=100.0, ge=0.0)
    materials: Dict[str, int] = Field(default_factory=lambda: {
        "WOOD": 10,
        "STONE": 5,
        "STEEL": 2,
        "TECH_PARTS": 0,
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
    is_subagent: bool = False
    lifespan_ticks: Optional[int] = None
    ticks_alive: int = 0

    # Cognitive & Memory Stores
    memory: AgentMemory = Field(default_factory=AgentMemory)
    current_goal: Optional[str] = None
    current_action: Optional[Dict[str, Any]] = None
    action_ticks_remaining: int = 0
    inbox: List[Any] = Field(default_factory=list)
    last_perceived_context: Optional[Dict[str, Any]] = None

    @model_validator(mode="before")
    @classmethod
    def _normalize_initial_values(cls, data: Any) -> Any:
        """Handle coordinate normalization, string roles, and subagent flags."""
        if isinstance(data, dict):
            # Coordinate normalization
            if "x" in data or "y" in data:
                pos = data.get("position", (0, 0))
                px = data.get("x", pos[0])
                py = data.get("y", pos[1])
                data["position"] = (int(px), int(py))

            # Role enum normalization
            if "role" in data:
                r = data["role"]
                if isinstance(r, str):
                    try:
                        data["role"] = CivicRole(r)
                    except ValueError:
                        # Allow custom/legacy roles if needed
                        pass

            # Subagent flag normalization
            if data.get("parent_id") and "is_subagent" not in data:
                data["is_subagent"] = True
            if data.get("is_temporary") and "is_subagent" not in data:
                data["is_subagent"] = True

        return data

    @property
    def id(self) -> str:
        """Convenience property for agent identity."""
        return self.agent_id

    @property
    def x(self) -> int:
        """X coordinate on city grid."""
        return self.position[0]

    @x.setter
    def x(self, val: int) -> None:
        self.position = (int(val), self.position[1])

    @property
    def y(self) -> int:
        """Y coordinate on city grid."""
        return self.position[1]

    @y.setter
    def y(self, val: int) -> None:
        self.position = (self.position[0], int(val))

    # =========================================================================
    # Lifecycle & Perception
    # =========================================================================

    def receive_messages(self, messages: List[Any]) -> None:
        """Append incoming messages from coordinator message bus."""
        self.inbox.extend(messages)

    def perceive(self, context: Dict[str, Any]) -> None:
        """Perceive neighborhood, inbox, and synchronise internal vitals."""
        self.state = AgentState.PERCEIVING
        self.last_perceived_context = context
        self.ticks_alive += 1

        # Synchronize ledger values if provided by coordinator
        ledger = context.get("ledger")
        if ledger is not None:
            self.energy = max(0.0, min(self.max_energy, getattr(ledger, "energy", self.energy)))
            self.funds = max(0.0, getattr(ledger, "funds", self.funds))

        # Record visited position in spatial memory
        pos = context.get("position") or self.position
        if pos:
            self.memory.visit_parcel(pos)

    def deliberate(self) -> Optional[Dict[str, Any]]:
        """
        Formulate next action using 4-tier goal hierarchy and utility scoring.
        Applies Homeostasis override when energy < 15.0.
        """
        self.state = AgentState.DELIBERATING

        # ---------------------------------------------------------------------
        # Tier 1 Override: Homeostasis (Exhaustion / Energy < 15.0)
        # ---------------------------------------------------------------------
        if self.energy < 15.0:
            action = {"type": "REST"}
            self.state = AgentState.RESTING
            self.current_action = action
            self.memory.record_action(action)
            return action

        # Default fallback deliberation for BaseAgent
        action = {"type": "IDLE"}
        self.state = AgentState.IDLE
        self.current_action = action
        self.memory.record_action(action)
        return action

    def on_epoch(self, epoch: int) -> None:
        """Epoch boundary notification hook for generational tracking."""
        pass

    def can_spawn_subagent(self, role: Union[CivicRole, str], current_child_count: int) -> Tuple[bool, str]:
        """
        Validate spawning eligibility under strict recursion and concurrency caps:
        - Strict recursion limit: Subagents cannot spawn subagents (max_depth = 1).
        - Role concurrency caps:
            MAYOR <= 1, ARCHITECT <= 2, ENGINEER <= 3, MERCHANT <= 3, SCHOLAR <= 2, OBSERVER <= 1.
        """
        # Strict recursion ceiling
        if self.is_subagent or self.is_temporary or self.parent_id is not None:
            return False, "Recursion limit exceeded: subagents cannot spawn second-order subagents (max_depth=1)"

        caps: Dict[str, int] = {
            CivicRole.MAYOR.value: 1,
            CivicRole.ARCHITECT.value: 2,
            CivicRole.ENGINEER.value: 3,
            CivicRole.MERCHANT.value: 3,
            CivicRole.SCHOLAR.value: 2,
            CivicRole.OBSERVER.value: 1,
        }
        role_str = self.role.value if isinstance(self.role, CivicRole) else str(self.role)
        max_allowed = caps.get(role_str, 1)
        if current_child_count >= max_allowed:
            return False, f"Parent role {role_str} reached maximum concurrent subagent cap ({max_allowed})"

        return True, "Eligible"

    def to_dict(self) -> Dict[str, Any]:
        """Serialize agent state for REST endpoints and JSON snapshots."""
        return {
            "agent_id": self.agent_id,
            "id": self.agent_id,
            "name": self.name,
            "role": self.role.value if isinstance(self.role, CivicRole) else str(self.role),
            "state": self.state.value if isinstance(self.state, AgentState) else str(self.state),
            "position": self.position,
            "x": self.x,
            "y": self.y,
            "energy": round(self.energy, 2),
            "funds": round(self.funds, 2),
            "materials": self.materials,
            "traits": self.traits.to_dict(),
            "generation": self.generation,
            "birth_epoch": self.birth_epoch,
            "fitness_score": round(self.fitness_score, 3),
            "parent_id": self.parent_id,
            "child_ids": list(self.child_ids),
            "is_temporary": self.is_temporary,
            "is_subagent": self.is_subagent,
            "ticks_alive": self.ticks_alive,
            "lifespan_ticks": self.lifespan_ticks,
        }
