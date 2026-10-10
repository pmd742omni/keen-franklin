"""Tier 1-3 Tests for Hierarchical Subagent Spawning, Delegation Contracts, Resource Escrow, and Lifecycles:
- Parent-Child Linkage & Lineage Tracking
- DelegationContract Lifecycle (PENDING, ACTIVE, COMPLETED, FAILED, TIMED_OUT)
- Upfront Resource Escrow & Automated Refund on Retirement
- Parent Concurrency Caps (Architect <= 2, Engineer <= 3, etc.)
- Strict Recursion Ceiling (max_depth = 1)
- Subagent Retirement & Memory/Registry Cleanup
"""

from __future__ import annotations

import pytest

# Conditional imports for Milestone 2 implementation
try:
    from agent_city.agents.subagents import (
        DelegationContract,
        DelegationStatus,
        SubagentManager,
        SubagentSpawner,
    )
    SUBAGENTS_AVAILABLE = True
except ImportError:
    SUBAGENTS_AVAILABLE = False


# =============================================================================
# Mathematical & Contract Specifications for Subagents
# =============================================================================

class SpecDelegationContract:
    """Specification model of a task delegation contract."""
    def __init__(
        self,
        contract_id: str,
        parent_id: str,
        child_id: str,
        task_name: str,
        allocated_funds: float = 0.0,
        allocated_materials: float = 0.0,
        max_duration_ticks: int = 20,
    ):
        self.contract_id = contract_id
        self.parent_id = parent_id
        self.child_id = child_id
        self.task_name = task_name
        self.allocated_funds = allocated_funds
        self.allocated_materials = allocated_materials
        self.unspent_funds = allocated_funds
        self.unspent_materials = allocated_materials
        self.max_duration_ticks = max_duration_ticks
        self.ticks_elapsed = 0
        self.status = "PENDING"
        self.result_payload = {}

    def activate(self):
        self.status = "ACTIVE"

    def complete(self, result: dict):
        self.status = "COMPLETED"
        self.result_payload = result

    def step(self):
        self.ticks_elapsed += 1
        if self.ticks_elapsed >= self.max_duration_ticks and self.status == "ACTIVE":
            self.status = "TIMED_OUT"


class SpecEscrowVault:
    """Escrows resources from parent and handles automated refunds on retirement."""
    def __init__(self):
        self.escrows = {}  # child_id -> (parent_id, funds, materials)

    def lock_escrow(self, parent_ledger, child_id: str, parent_id: str, funds: float, materials: float) -> bool:
        if not parent_ledger.withdraw(funds=funds, materials=materials):
            return False
        self.escrows[child_id] = (parent_id, funds, materials)
        return True

    def refund_escrow(self, parent_ledger, child_id: str, unspent_funds: float, unspent_materials: float) -> bool:
        if child_id not in self.escrows:
            return False
        parent_id, _, _ = self.escrows.pop(child_id)
        parent_ledger.deposit(funds=unspent_funds, materials=unspent_materials)
        return True


# =============================================================================
# Tier 1-3 Tests for Subagent Spawning, Escrow, and Recursion Guard
# =============================================================================

class TestSubagentContractsAndEscrow:
    """Verifies subagent lifecycle, parent-child escrow, and recursion constraints."""

    def test_delegation_contract_lifecycle(self):
        """Tier 1: Verify contract progression from PENDING -> ACTIVE -> COMPLETED."""
        contract = SpecDelegationContract(
            contract_id="c_101",
            parent_id="architect_1",
            child_id="surveyor_101",
            task_name="SURVEY_PARCEL",
            allocated_funds=50.0,
            max_duration_ticks=10,
        )
        assert contract.status == "PENDING"
        contract.activate()
        assert contract.status == "ACTIVE"

        # Advance 5 ticks
        for _ in range(5):
            contract.step()
        assert contract.status == "ACTIVE"

        contract.complete({"zoning_potential": "COMMERCIAL", "slope": 0.05})
        assert contract.status == "COMPLETED"
        assert contract.result_payload["zoning_potential"] == "COMMERCIAL"

    def test_delegation_contract_timeout(self):
        """Tier 2: Contracts that exceed max_duration_ticks automatically time out."""
        contract = SpecDelegationContract(
            contract_id="c_102",
            parent_id="engineer_1",
            child_id="crew_102",
            task_name="POUR_FOUNDATION",
            max_duration_ticks=5,
        )
        contract.activate()
        for _ in range(5):
            contract.step()
        assert contract.status == "TIMED_OUT"

    def test_resource_escrow_and_refund_lifecycle(self, economy):
        """Tier 1 & 3: Upfront escrow from parent ledger with automated refund of unused assets."""
        parent_ledger = economy.register_account("parent_agent", funds=200.0, materials=50.0)
        vault = SpecEscrowVault()

        # Lock escrow: 50 funds, 20 materials
        assert vault.lock_escrow(parent_ledger, "child_sub", "parent_agent", 50.0, 20.0) is True
        assert parent_ledger.funds == 150.0
        assert parent_ledger.materials == 30.0

        # Child finishes task having spent 20 funds and 15 materials (unspent: 30 funds, 5 materials)
        assert vault.refund_escrow(parent_ledger, "child_sub", unspent_funds=30.0, unspent_materials=5.0) is True
        assert parent_ledger.funds == 180.0  # 150 + 30
        assert parent_ledger.materials == 35.0  # 30 + 5

    def test_parent_insolvency_prevents_subagent_spawning(self, economy):
        """Tier 2: Parent with insufficient funds cannot escrow resources for subagents."""
        parent_ledger = economy.register_account("poor_parent", funds=10.0, materials=0.0)
        vault = SpecEscrowVault()

        # Requires 50 funds -> fails
        assert vault.lock_escrow(parent_ledger, "child_sub", "poor_parent", 50.0, 0.0) is False
        assert parent_ledger.funds == 10.0  # Unchanged

    def test_parent_concurrency_caps(self):
        """Tier 2: Parents cannot exceed maximum concurrent subagent allocations."""
        caps = {
            "MAYOR": 1,
            "ARCHITECT": 2,
            "ENGINEER": 3,
            "MERCHANT": 3,
            "SCHOLAR": 2,
            "OBSERVER": 1,
        }
        # Simulate architect spawning up to cap
        active_children = ["sub_1", "sub_2"]
        architect_role = "ARCHITECT"
        can_spawn_third = len(active_children) < caps[architect_role]
        assert can_spawn_third is False

    def test_strict_recursion_depth_limit(self):
        """Tier 2: Subagents are forbidden from spawning second-order subagents (max_depth=1)."""
        def can_spawn(agent_is_subagent: bool, current_depth: int) -> bool:
            if agent_is_subagent or current_depth >= 1:
                return False
            return True

        assert can_spawn(agent_is_subagent=False, current_depth=0) is True
        assert can_spawn(agent_is_subagent=True, current_depth=1) is False


# =============================================================================
# Concrete SubagentManager Tests (Unskipped when M2 is present)
# =============================================================================

@pytest.mark.skipif(not SUBAGENTS_AVAILABLE, reason="Milestone 2 (agent_city.agents.subagents) not yet implemented")
class TestConcreteSubagents:
    """Direct tests against the concrete SubagentManager and DelegationContract implementations."""

    def test_concrete_subagent_spawning(self):
        """Tier 1: Spawner registers child agent and links parent_id."""
        spawner = SubagentSpawner()
        child = spawner.spawn(
            parent_id="architect_1",
            role="SURVEYOR",
            task="SURVEY_EAST_PERIMETER",
            budget={"funds": 25.0, "materials": 0.0},
        )
        assert child.parent_id == "architect_1"
        assert child.is_temporary is True
        assert child.role == "SURVEYOR"

    def test_concrete_subagent_retirement(self):
        """Tier 1: Retiring child unregisters agent and cleans up parent child_ids."""
        manager = SubagentManager()
        child_id = manager.spawn_subagent("architect_1", "SURVEYOR", "SURVEY")
        assert manager.has_active_child("architect_1", child_id) is True

        manager.retire_subagent(child_id)
        assert manager.has_active_child("architect_1", child_id) is False

    def test_five_subagent_archetypes_instantiation(self):
        """Tier 1: Verify all 5 subagent archetypes instantiate with correct roles and lifespans."""
        from agent_city.agents.subagents import (
            SurveyorAgent,
            ConstructionCrewAgent,
            ResearchAssistantAgent,
            CourierAgent,
            DistrictSupervisorAgent,
        )
        from agent_city.agents.base import CivicRole

        surveyor = SurveyorAgent(agent_id="s1", name="Surveyor 1", parent_id="arch_1")
        assert surveyor.role == CivicRole.SURVEYOR
        assert surveyor.is_temporary is True
        assert surveyor.lifespan_ticks == 20

        crew = ConstructionCrewAgent(agent_id="c1", name="Crew 1", parent_id="eng_1")
        assert crew.role == CivicRole.CONSTRUCTION_CREW
        assert crew.is_temporary is True
        assert crew.lifespan_ticks == 35

        assistant = ResearchAssistantAgent(agent_id="r1", name="Assistant 1", parent_id="sch_1")
        assert assistant.role == CivicRole.RESEARCH_ASSISTANT
        assert assistant.is_temporary is True
        assert assistant.lifespan_ticks == 25

        courier = CourierAgent(agent_id="cr1", name="Courier 1", parent_id="mer_1")
        assert courier.role == CivicRole.COURIER
        assert courier.is_temporary is True
        assert courier.lifespan_ticks == 15

        supervisor = DistrictSupervisorAgent(agent_id="ds1", name="Supervisor 1", parent_id="may_1")
        assert supervisor.role == CivicRole.DISTRICT_SUPERVISOR
        assert supervisor.is_temporary is False
        assert supervisor.lifespan_ticks is None

    def test_subagent_manager_concurrency_caps_enforced(self):
        """Tier 2: SubagentManager enforces role concurrency limits (Architect max 2)."""
        manager = SubagentManager()
        c1 = manager.spawn_subagent("architect_cap", "SURVEYOR", "TASK_1")
        c2 = manager.spawn_subagent("architect_cap", "SURVEYOR", "TASK_2")
        assert manager.has_active_child("architect_cap", c1) is True
        assert manager.has_active_child("architect_cap", c2) is True

        # Third subagent exceeds cap (Architect <= 2)
        with pytest.raises(ValueError, match="maximum concurrency cap"):
            manager.spawn_subagent("architect_cap", "SURVEYOR", "TASK_3")

    def test_subagent_manager_recursion_guard_enforced(self):
        """Tier 2: Subagents cannot spawn second-order subagents (max_depth=1)."""
        from agent_city.agents.subagents import SurveyorAgent
        subagent = SurveyorAgent(agent_id="sub_surveyor_rec", name="Surveyor", parent_id="arch_1")
        manager = SubagentManager()

        with pytest.raises(ValueError, match="recursion"):
            manager.spawn_subagent(subagent, "SURVEYOR", "TASK_ILLEGAL")

    def test_subagent_manager_escrow_refund_lifecycle(self, economy):
        """Tier 2 & 3: Upfront escrow from parent agent and automated refund on retirement."""
        from agent_city.agents.roles import ArchitectAgent
        parent = ArchitectAgent(agent_id="arch_escrow", name="Architect Escrow", funds=100.0)
        manager = SubagentManager()

        # Spawn subagent with 30 funds budget
        child_id = manager.spawn_subagent(parent, "SURVEYOR", "SURVEY_SITE", budget=30.0)
        assert parent.funds == 70.0
        assert child_id in parent.child_ids

        # Retire subagent with 10 funds unspent
        refund_info = manager.retire_subagent(child_id, unspent_funds=10.0, parent_agent=parent)
        assert refund_info["refunded_funds"] == 10.0
        assert parent.funds == 80.0
        assert child_id not in parent.child_ids

    def test_subagent_manager_step_contracts_timeout(self):
        """Tier 2: step_contracts automatically retires timed-out subagents."""
        manager = SubagentManager()
        child_id = manager.spawn_subagent("arch_time", "SURVEYOR", "SHORT_TASK", lifespan=2)
        assert manager.has_active_child("arch_time", child_id) is True

        # Advance 1 tick: still active
        timed_out = manager.step_contracts(1)
        assert len(timed_out) == 0
        assert manager.has_active_child("arch_time", child_id) is True

        # Advance 2nd tick: expires and auto-retires
        timed_out = manager.step_contracts(2)
        assert child_id in timed_out
        assert manager.has_active_child("arch_time", child_id) is False

