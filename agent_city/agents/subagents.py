"""Hierarchical subagents, delegation contracts, escrow vaults, and retirement lifecycle."""

from __future__ import annotations

import uuid
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

from pydantic import BaseModel, ConfigDict, Field

from agent_city.agents.base import AgentState, BaseAgent, CivicRole, TraitVector


class DelegationStatus(str, Enum):
    """Lifecycle status for hierarchical delegation contracts."""
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    TIMED_OUT = "TIMED_OUT"


class DelegationContract(BaseModel):
    """
    Formal task delegation contract between parent civic agent and child subagent.
    Tracks budget escrow, duration, status, and returned findings.
    """
    model_config = ConfigDict(arbitrary_types_allowed=True, validate_assignment=True)

    contract_id: str = Field(default_factory=lambda: f"c_{uuid.uuid4().hex[:8]}")
    parent_id: str
    child_id: str
    task_name: str
    target_coordinates: Optional[Tuple[int, int]] = None
    allocated_funds: float = 0.0
    allocated_materials: float = 0.0
    unspent_funds: float = 0.0
    unspent_materials: float = 0.0
    max_duration_ticks: int = 20
    created_at_tick: int = 0
    ticks_elapsed: int = 0
    status: DelegationStatus = DelegationStatus.PENDING
    result_payload: Dict[str, Any] = Field(default_factory=dict)

    def activate(self) -> None:
        """Activate contract upon subagent mobilization."""
        self.status = DelegationStatus.ACTIVE

    def complete(self, result: Optional[Dict[str, Any]] = None) -> None:
        """Mark contract successfully completed and record findings."""
        self.status = DelegationStatus.COMPLETED
        if result is not None:
            self.result_payload = result

    def fail(self, reason: str = "") -> None:
        """Mark contract failed."""
        self.status = DelegationStatus.FAILED
        self.result_payload["failure_reason"] = reason

    def step(self) -> None:
        """Step contract duration timer and trigger timeout if overdue."""
        self.ticks_elapsed += 1
        if self.ticks_elapsed >= self.max_duration_ticks and self.status == DelegationStatus.ACTIVE:
            self.status = DelegationStatus.TIMED_OUT


# =============================================================================
# Specialized Subagent Archetypes
# =============================================================================

class SurveyorAgent(BaseAgent):
    """Temporary subagent spawned by Architect to inspect terrain and report zoning feasibility."""
    role: CivicRole = CivicRole.SURVEYOR
    is_temporary: bool = True
    is_subagent: bool = True
    lifespan_ticks: Optional[int] = 20
    traits: TraitVector = Field(
        default_factory=lambda: TraitVector(
            diligence=0.85,
            innovation=0.7,
            sociability=0.3,
            thriftiness=0.6,
            altruism=0.5,
            adaptability=0.8,
            risk_tolerance=0.5,
        )
    )


class ConstructionCrewAgent(BaseAgent):
    """Temporary subagent spawned by Engineer to supply multiplied construction labor."""
    role: CivicRole = CivicRole.CONSTRUCTION_CREW
    is_temporary: bool = True
    is_subagent: bool = True
    lifespan_ticks: Optional[int] = 35
    traits: TraitVector = Field(
        default_factory=lambda: TraitVector(
            diligence=0.95,
            innovation=0.3,
            sociability=0.4,
            thriftiness=0.7,
            altruism=0.6,
            adaptability=0.4,
            risk_tolerance=0.4,
        )
    )


class ResearchAssistantAgent(BaseAgent):
    """Temporary subagent spawned by Scholar to survey public sentiment and gather environmental data."""
    role: CivicRole = CivicRole.RESEARCH_ASSISTANT
    is_temporary: bool = True
    is_subagent: bool = True
    lifespan_ticks: Optional[int] = 25
    traits: TraitVector = Field(
        default_factory=lambda: TraitVector(
            diligence=0.85,
            innovation=0.8,
            sociability=0.7,
            thriftiness=0.5,
            altruism=0.7,
            adaptability=0.7,
            risk_tolerance=0.4,
        )
    )


class CourierAgent(BaseAgent):
    """Temporary subagent spawned by Merchant for high-speed cargo and resource delivery."""
    role: CivicRole = CivicRole.COURIER
    is_temporary: bool = True
    is_subagent: bool = True
    lifespan_ticks: Optional[int] = 15
    traits: TraitVector = Field(
        default_factory=lambda: TraitVector(
            diligence=0.9,
            innovation=0.4,
            sociability=0.5,
            thriftiness=0.8,
            altruism=0.4,
            adaptability=0.8,
            risk_tolerance=0.7,
        )
    )


class DistrictSupervisorAgent(BaseAgent):
    """Permanent subagent spawned by Mayor to manage regional district governance."""
    role: CivicRole = CivicRole.DISTRICT_SUPERVISOR
    is_temporary: bool = False
    is_subagent: bool = True
    lifespan_ticks: Optional[int] = None
    traits: TraitVector = Field(
        default_factory=lambda: TraitVector(
            diligence=0.85,
            innovation=0.5,
            sociability=0.8,
            thriftiness=0.7,
            altruism=0.8,
            adaptability=0.6,
            risk_tolerance=0.3,
        )
    )


# =============================================================================
# Subagent Spawner & Subagent Manager
# =============================================================================

class SubagentSpawner:
    """Instantiates concrete subagents with parent links, budgets, and temporary lifespans."""

    ARCHETYPE_MAP = {
        "SURVEYOR": SurveyorAgent,
        CivicRole.SURVEYOR: SurveyorAgent,
        "CONSTRUCTION_CREW": ConstructionCrewAgent,
        CivicRole.CONSTRUCTION_CREW: ConstructionCrewAgent,
        "RESEARCH_ASSISTANT": ResearchAssistantAgent,
        CivicRole.RESEARCH_ASSISTANT: ResearchAssistantAgent,
        "COURIER": CourierAgent,
        CivicRole.COURIER: CourierAgent,
        "DISTRICT_SUPERVISOR": DistrictSupervisorAgent,
        CivicRole.DISTRICT_SUPERVISOR: DistrictSupervisorAgent,
    }

    def spawn(
        self,
        parent_id: str,
        role: Union[str, CivicRole],
        task: str = "",
        budget: Optional[Union[Dict[str, float], float]] = None,
        target_coords: Optional[Tuple[int, int]] = None,
        lifespan: Optional[int] = None,
        name: Optional[str] = None,
        **kwargs: Any,
    ) -> BaseAgent:
        """Instantiate and initialize a specialized subagent."""
        role_key = role.value if isinstance(role, CivicRole) else str(role).upper()
        agent_cls = self.ARCHETYPE_MAP.get(role_key, BaseAgent)

        allocated_funds = 25.0
        allocated_materials = 0.0
        if isinstance(budget, dict):
            allocated_funds = float(budget.get("funds", 25.0))
            allocated_materials = float(budget.get("materials", 0.0))
        elif isinstance(budget, (int, float)):
            allocated_funds = float(budget)

        uid = f"sub_{role_key.lower()}_{uuid.uuid4().hex[:6]}"
        agent_name = name or f"{role_key.capitalize()} ({parent_id})"

        is_temp = role_key != "DISTRICT_SUPERVISOR"
        agent_lifespan = lifespan if lifespan is not None else (kwargs.get("lifespan_ticks") or (20 if is_temp else None))

        agent = agent_cls(
            agent_id=uid,
            name=agent_name,
            role=role if isinstance(role, CivicRole) else CivicRole(role_key),
            position=target_coords or (0, 0),
            parent_id=parent_id,
            is_temporary=is_temp,
            is_subagent=True,
            lifespan_ticks=agent_lifespan,
            funds=allocated_funds,
            energy=100.0,
            **kwargs,
        )
        return agent


class SubagentManager:
    """
    Lifecycle, resource escrow, and concurrency manager for subagents.
    Enforces:
    - Upfront escrow deposit & automated refund upon retirement
    - Strict parent concurrency caps (Architect <= 2, Engineer <= 3, etc.)
    - Strict recursion limit (max_depth = 1)
    """

    ROLE_CAPS: Dict[str, int] = {
        "MAYOR": 1,
        "ARCHITECT": 2,
        "ENGINEER": 3,
        "MERCHANT": 3,
        "SCHOLAR": 2,
        "OBSERVER": 1,
    }

    def __init__(self) -> None:
        self.spawner: SubagentSpawner = SubagentSpawner()
        self.subagents: Dict[str, BaseAgent] = {}
        self.parent_to_children: Dict[str, List[str]] = {}
        self.contracts: Dict[str, DelegationContract] = {}
        # Escrow store: child_id -> (parent_id, funds, materials)
        self.escrows: Dict[str, Tuple[str, float, float]] = {}

    def can_spawn(
        self,
        parent: Union[BaseAgent, str],
        role: Union[str, CivicRole],
        parent_role: Optional[str] = None,
    ) -> Tuple[bool, str]:
        """Verify strict recursion guard and concurrency caps."""
        # Check recursion limit
        if isinstance(parent, BaseAgent):
            if parent.is_subagent or parent.is_temporary or parent.parent_id is not None:
                return False, "Strict recursion ceiling: subagents cannot spawn second-order subagents (max_depth=1)"
            p_role = parent.role.value if isinstance(parent.role, CivicRole) else str(parent.role)
            p_id = parent.agent_id
        else:
            p_id = parent
            p_role = parent_role or "ARCHITECT"

        # Check concurrency caps
        active_children = self.parent_to_children.get(p_id, [])
        cap = self.ROLE_CAPS.get(p_role.upper(), 2)
        if len(active_children) >= cap:
            return False, f"Parent {p_id} reached maximum concurrency cap of {cap} subagents"

        return True, "Eligible"

    def spawn_subagent(
        self,
        parent: Union[str, BaseAgent],
        role: Union[str, CivicRole],
        task: str = "DEFAULT_TASK",
        budget: Optional[Union[Dict[str, float], float]] = None,
        target_coords: Optional[Tuple[int, int]] = None,
        lifespan: Optional[int] = None,
        economy_system: Optional[Any] = None,
        coordinator: Optional[Any] = None,
    ) -> str:
        """
        Validate constraints, escrow parent resources, spawn subagent,
        and register delegation contract. Returns child_id string.
        """
        parent_id = parent.agent_id if isinstance(parent, BaseAgent) else str(parent)
        parent_role = (
            parent.role.value if isinstance(parent, BaseAgent) and isinstance(parent.role, CivicRole)
            else (str(parent.role) if isinstance(parent, BaseAgent) else "ARCHITECT")
        )

        eligible, reason = self.can_spawn(parent, role, parent_role=parent_role)
        if not eligible:
            raise ValueError(f"Cannot spawn subagent: {reason}")

        # Parse budget
        allocated_funds = 25.0
        allocated_materials = 0.0
        if isinstance(budget, dict):
            allocated_funds = float(budget.get("funds", 25.0))
            allocated_materials = float(budget.get("materials", 0.0))
        elif isinstance(budget, (int, float)):
            allocated_funds = float(budget)

        # Upfront Escrow Lock
        if economy_system is not None:
            ledger = economy_system.get_ledger(parent_id)
            if ledger:
                if not ledger.withdraw(funds=allocated_funds, materials=allocated_materials):
                    raise ValueError(f"Parent {parent_id} lacks sufficient resources for escrow.")
        elif isinstance(parent, BaseAgent):
            if parent.funds < allocated_funds:
                raise ValueError(f"Parent {parent_id} lacks sufficient funds ({parent.funds} < {allocated_funds})")
            parent.funds -= allocated_funds

        # Spawn subagent instance
        child = self.spawner.spawn(
            parent_id=parent_id,
            role=role,
            task=task,
            budget={"funds": allocated_funds, "materials": allocated_materials},
            target_coords=target_coords,
            lifespan=lifespan,
        )
        child_id = child.agent_id

        # Record escrow
        self.escrows[child_id] = (parent_id, allocated_funds, allocated_materials)

        # Register child
        self.subagents[child_id] = child
        if parent_id not in self.parent_to_children:
            self.parent_to_children[parent_id] = []
        self.parent_to_children[parent_id].append(child_id)

        if isinstance(parent, BaseAgent) and child_id not in parent.child_ids:
            parent.child_ids.append(child_id)

        # Create delegation contract
        contract = DelegationContract(
            parent_id=parent_id,
            child_id=child_id,
            task_name=task,
            target_coordinates=target_coords,
            allocated_funds=allocated_funds,
            allocated_materials=allocated_materials,
            unspent_funds=allocated_funds,
            unspent_materials=allocated_materials,
            max_duration_ticks=lifespan or 20,
        )
        contract.activate()
        self.contracts[child_id] = contract

        # Register into simulation coordinator if provided
        if coordinator is not None:
            coordinator.register_agent(
                child,
                initial_x=child.x,
                initial_y=child.y,
                initial_funds=allocated_funds,
                initial_materials=allocated_materials,
            )

        return child_id

    def retire_subagent(
        self,
        child_id: Union[str, BaseAgent],
        reason: str = "COMPLETED",
        result_payload: Optional[Dict[str, Any]] = None,
        unspent_funds: Optional[float] = None,
        unspent_materials: Optional[float] = None,
        economy_system: Optional[Any] = None,
        coordinator: Optional[Any] = None,
        parent_agent: Optional[BaseAgent] = None,
    ) -> Dict[str, Any]:
        """
        Retire subagent, refund unspent escrowed assets to parent,
        update contract, and clean up active child references.
        """
        cid = child_id.agent_id if isinstance(child_id, BaseAgent) else str(child_id)
        child = self.subagents.get(cid)
        contract = self.contracts.get(cid)

        if child is not None:
            child.state = AgentState.RETIRED

        # Determine refunds
        escrow_data = self.escrows.pop(cid, None)
        parent_id = escrow_data[0] if escrow_data else (child.parent_id if child else None)
        orig_funds = escrow_data[1] if escrow_data else 0.0
        orig_materials = escrow_data[2] if escrow_data else 0.0

        refund_f = unspent_funds if unspent_funds is not None else (child.funds if child else orig_funds)
        refund_m = unspent_materials if unspent_materials is not None else orig_materials

        # Deposit refund back to parent
        if parent_id:
            if economy_system is not None:
                ledger = economy_system.get_ledger(parent_id)
                if ledger:
                    ledger.deposit(funds=refund_f, materials=refund_m)
            elif parent_agent is not None and parent_agent.agent_id == parent_id:
                parent_agent.funds += refund_f

            # Clean up parent child list
            if parent_id in self.parent_to_children:
                if cid in self.parent_to_children[parent_id]:
                    self.parent_to_children[parent_id].remove(cid)

            if parent_agent is not None and cid in parent_agent.child_ids:
                parent_agent.child_ids.remove(cid)

        # Update contract
        if contract is not None:
            if reason.upper() == "COMPLETED":
                contract.complete(result_payload or {})
            elif reason.upper() == "TIMED_OUT":
                contract.status = DelegationStatus.TIMED_OUT
            else:
                contract.fail(reason)
            contract.unspent_funds = refund_f
            contract.unspent_materials = refund_m

        # Unregister from coordinator if active
        if coordinator is not None:
            coordinator.unregister_agent(cid)

        self.subagents.pop(cid, None)

        return {
            "child_id": cid,
            "parent_id": parent_id,
            "status": "RETIRED",
            "reason": reason,
            "refunded_funds": refund_f,
            "refunded_materials": refund_m,
        }

    def has_active_child(self, parent_id: str, child_id: str) -> bool:
        """Check if parent currently retains an active subagent."""
        active = self.parent_to_children.get(parent_id, [])
        return child_id in active

    def get_active_children(self, parent_id: str) -> List[str]:
        """Return list of active child IDs for parent."""
        return list(self.parent_to_children.get(parent_id, []))

    def step_contracts(
        self,
        current_tick: int,
        economy_system: Optional[Any] = None,
        coordinator: Optional[Any] = None,
    ) -> List[str]:
        """Step all active delegation contracts and auto-retire expired subagents."""
        timed_out: List[str] = []
        for cid, contract in list(self.contracts.items()):
            if contract.status == DelegationStatus.ACTIVE:
                contract.step()
                if contract.status == DelegationStatus.TIMED_OUT:
                    timed_out.append(cid)
                    self.retire_subagent(
                        child_id=cid,
                        reason="TIMED_OUT",
                        economy_system=economy_system,
                        coordinator=coordinator,
                    )
        return timed_out
