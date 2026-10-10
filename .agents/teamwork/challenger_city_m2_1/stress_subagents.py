"""Empirical Adversarial Stress Testing Harness for Subagent Lifecycles in agent_city (Milestone 2)

Tests:
1. Recursion depth violations & string-ID guard bypasses (max_depth = 1)
2. Concurrency exhaustion, role quota limits, and string-ID role defaulting
3. Parent retirement with active subagents, zombie subagents, and orphan recovery
4. Escrow balance leakage, negative budgets, over-refund inflation, and double-retirements
5. Economic currency conservation across subagent lifecycle loops
6. SimulationCoordinator integration, stepping stability, and voting integrity
"""

import sys
import os
import traceback
from typing import Dict, List, Any, Tuple

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from agent_city.agents.base import AgentState, BaseAgent, CivicRole, TraitVector
from agent_city.agents.roles import (
    ArchitectAgent,
    EngineerAgent,
    MayorAgent,
    MerchantAgent,
    ObserverAgent,
    ScholarAgent,
)
from agent_city.agents.subagents import (
    ConstructionCrewAgent,
    CourierAgent,
    DelegationContract,
    DelegationStatus,
    DistrictSupervisorAgent,
    ResearchAssistantAgent,
    SubagentManager,
    SubagentSpawner,
    SurveyorAgent,
)
from agent_city.config import DEFAULT_CONFIG, ProposalStatus, VoteChoice
from agent_city.engine.economy import EconomySystem
from agent_city.engine.message_bus import CivicProposal
from agent_city.engine.simulation import SimulationCoordinator


class StressTestResult:
    def __init__(self, name: str, category: str):
        self.name = name
        self.category = category
        self.passed = False
        self.vulnerability_found = False
        self.details = ""
        self.error = None

    def __repr__(self):
        status = "PASSED" if self.passed else ("VULNERABILITY" if self.vulnerability_found else "FAILED")
        return f"[{status}] {self.category} :: {self.name} - {self.details}"


class SubagentStressTester:
    def __init__(self):
        self.results: List[StressTestResult] = []

    def record_pass(self, name: str, category: str, details: str):
        r = StressTestResult(name, category)
        r.passed = True
        r.details = details
        self.results.append(r)
        print(f"  [PASS] {name}: {details}")

    def record_vuln(self, name: str, category: str, details: str):
        r = StressTestResult(name, category)
        r.passed = False
        r.vulnerability_found = True
        r.details = details
        self.results.append(r)
        print(f"  [VULNERABILITY FOUND] {name}: {details}")

    def record_fail(self, name: str, category: str, details: str, error: Exception = None):
        r = StressTestResult(name, category)
        r.passed = False
        r.details = details
        r.error = error
        self.results.append(r)
        print(f"  [FAIL] {name}: {details} (Error: {error})")

    # =========================================================================
    # SUITE 1: Recursion Depth Violations & Guard Bypasses
    # =========================================================================

    def test_1_1_direct_subagent_spawn_blocked(self):
        name = "Direct Subagent Object Spawning Blocked"
        cat = "Recursion Ceiling"
        try:
            manager = SubagentManager()
            arch = ArchitectAgent(agent_id="arch_rec_1", name="Arch", funds=100.0)
            child_id = manager.spawn_subagent(arch, "SURVEYOR")
            child_obj = manager.subagents[child_id]

            # Attempt to spawn using child_obj as parent
            try:
                manager.spawn_subagent(child_obj, "SURVEYOR")
                self.record_vuln(name, cat, "Subagent object was able to spawn another subagent!")
            except ValueError as e:
                if "recursion" in str(e).lower() or "max_depth" in str(e).lower():
                    self.record_pass(name, cat, f"Direct object recursion correctly rejected: {e}")
                else:
                    self.record_vuln(name, cat, f"Rejected with unexpected error: {e}")
        except Exception as e:
            self.record_fail(name, cat, "Exception during test", e)

    def test_1_2_string_id_recursion_bypass(self):
        name = "String ID Recursion Guard Bypass"
        cat = "Recursion Ceiling"
        try:
            manager = SubagentManager()
            arch = ArchitectAgent(agent_id="arch_rec_2", name="Arch", funds=100.0)
            child_id = manager.spawn_subagent(arch, "SURVEYOR")

            # Adversarial bypass attempt: pass child_id (string) instead of object
            try:
                second_order_id = manager.spawn_subagent(child_id, "SURVEYOR")
                # If we reached here, recursion guard was BYPASSED!
                # Try to spawn third-order
                third_order_id = manager.spawn_subagent(second_order_id, "SURVEYOR")
                self.record_vuln(
                    name,
                    cat,
                    f"CRITICAL VULNERABILITY: Passing string child_id bypassed recursion guard! "
                    f"Spawned 2nd-order '{second_order_id}' and 3rd-order '{third_order_id}' subagents."
                )
            except ValueError as e:
                if "recursion" in str(e).lower():
                    self.record_pass(name, cat, "String child_id recursion correctly blocked.")
                else:
                    self.record_vuln(name, cat, f"Blocked with non-recursion error: {e}")
        except Exception as e:
            self.record_fail(name, cat, "Exception during test", e)

    def test_1_3_forged_flags_lineage_check(self):
        name = "Forged Subagent Flags Lineage Verification"
        cat = "Recursion Ceiling"
        try:
            manager = SubagentManager()
            arch = ArchitectAgent(agent_id="arch_rec_3", name="Arch", funds=100.0)
            child_id = manager.spawn_subagent(arch, "SURVEYOR")
            child_obj = manager.subagents[child_id]

            # Forge flags on child object
            child_obj.is_subagent = False
            child_obj.is_temporary = False
            child_obj.parent_id = None

            try:
                manager.spawn_subagent(child_obj, "SURVEYOR")
                self.record_vuln(
                    name,
                    cat,
                    "VULNERABILITY: Mutating is_subagent/parent_id on child allowed it to spawn a child! "
                    "Registry lookup not enforced."
                )
            except ValueError as e:
                if "recursion" in str(e).lower():
                    self.record_pass(name, cat, "Manager checked registry and prevented forged object spawning.")
                else:
                    self.record_vuln(name, cat, f"Manager rejected for other reason: {e}")
        except Exception as e:
            self.record_fail(name, cat, "Exception during test", e)

    # =========================================================================
    # SUITE 2: Concurrency Cap Breaches & Role Quotas
    # =========================================================================

    def test_2_1_role_concurrency_caps_enforced(self):
        name = "Strict Role Concurrency Quotas"
        cat = "Concurrency Caps"
        role_classes = {
            "MAYOR": (MayorAgent, 1),
            "ARCHITECT": (ArchitectAgent, 2),
            "ENGINEER": (EngineerAgent, 3),
            "MERCHANT": (MerchantAgent, 3),
            "SCHOLAR": (ScholarAgent, 2),
            "OBSERVER": (ObserverAgent, 1),
        }
        all_ok = True
        details = []
        try:
            for role_name, (cls, max_cap) in role_classes.items():
                manager = SubagentManager()
                parent_agent = cls(agent_id=f"parent_{role_name.lower()}", name=role_name, funds=1000.0)
                # Spawn up to cap
                for i in range(max_cap):
                    manager.spawn_subagent(parent_agent, "SURVEYOR")

                # Attempt cap + 1
                try:
                    manager.spawn_subagent(parent_agent, "SURVEYOR")
                    all_ok = False
                    details.append(f"{role_name} exceeded cap {max_cap}")
                except ValueError as e:
                    if "concurrency cap" not in str(e).lower():
                        details.append(f"{role_name} error message unexpected: {e}")

            if all_ok:
                self.record_pass(name, cat, f"All 6 role concurrency caps strictly enforced ({[f'{k}:{v[1]}' for k, v in role_classes.items()]}).")
            else:
                self.record_vuln(name, cat, f"Concurrency cap breached: {'; '.join(details)}")
        except Exception as e:
            self.record_fail(name, cat, "Exception during test", e)

    def test_2_2_string_id_default_role_cap_breach(self):
        name = "String ID Default Role Cap Breach"
        cat = "Concurrency Caps"
        try:
            manager = SubagentManager()
            # Mayor has cap 1. If passed as string without parent_role, does it allow 2?
            mayor_id = "mayor_cap_test"
            c1 = manager.spawn_subagent(mayor_id, "SURVEYOR")

            # Try spawning second subagent without specifying parent_role
            try:
                c2 = manager.spawn_subagent(mayor_id, "SURVEYOR")
                # If spawned, Mayor bypassed cap of 1 because SubagentManager defaulted role to ARCHITECT (cap 2)!
                self.record_vuln(
                    name,
                    cat,
                    f"VULNERABILITY: Mayor string ID '{mayor_id}' spawned 2 subagents ({c1}, {c2}) "
                    "because SubagentManager defaulted unspecified role to ARCHITECT (cap 2) instead of looking up or enforcing minimum cap!"
                )
            except ValueError:
                self.record_pass(name, cat, "Mayor string ID was restricted from exceeding cap 1.")
        except Exception as e:
            self.record_fail(name, cat, "Exception during test", e)

    def test_2_3_quota_restoration_after_retirement(self):
        name = "Quota Slot Restoration on Retirement"
        cat = "Concurrency Caps"
        try:
            manager = SubagentManager()
            arch = ArchitectAgent(agent_id="arch_quota", name="Arch", funds=200.0)
            c1 = manager.spawn_subagent(arch, "SURVEYOR")
            c2 = manager.spawn_subagent(arch, "SURVEYOR")

            # Cap reached
            try:
                manager.spawn_subagent(arch, "SURVEYOR")
                self.record_vuln(name, cat, "Cap not enforced at 2.")
                return
            except ValueError:
                pass

            # Retire c1
            manager.retire_subagent(c1, parent_agent=arch)

            # Now spawning should succeed
            try:
                c3 = manager.spawn_subagent(arch, "SURVEYOR")
                self.record_pass(name, cat, f"Quota slot cleanly restored after retiring {c1}. New child: {c3}.")
            except ValueError as e:
                self.record_vuln(name, cat, f"Failed to spawn after legitimate retirement: {e}")
        except Exception as e:
            self.record_fail(name, cat, "Exception during test", e)

    def test_2_4_high_volume_concurrency_burst(self):
        name = "High Volume Concurrency Burst Stress"
        cat = "Concurrency Caps"
        try:
            manager = SubagentManager()
            eng = EngineerAgent(agent_id="eng_burst", name="Eng", funds=5000.0)
            spawned = []
            rejected = 0

            for i in range(100):
                try:
                    cid = manager.spawn_subagent(eng, "CONSTRUCTION_CREW", lifespan=10)
                    spawned.append(cid)
                except ValueError:
                    rejected += 1

            if len(spawned) == 3 and rejected == 97:
                self.record_pass(name, cat, f"100 burst attempts: exactly 3 allowed, 97 rejected.")
            else:
                self.record_vuln(name, cat, f"Burst violation: {len(spawned)} allowed (expected 3), {rejected} rejected.")
        except Exception as e:
            self.record_fail(name, cat, "Exception during test", e)

    # =========================================================================
    # SUITE 3: Parent Retirement & Orphan Handling
    # =========================================================================

    def test_3_1_spawning_from_retired_parent(self):
        name = "Spawning from Retired/Dead Parent"
        cat = "Parent Lifecycle"
        try:
            manager = SubagentManager()
            arch = ArchitectAgent(agent_id="arch_dead_test", name="Dead Arch", funds=100.0)
            arch.state = AgentState.RETIRED

            try:
                cid = manager.spawn_subagent(arch, "SURVEYOR")
                self.record_vuln(
                    name,
                    cat,
                    f"VULNERABILITY: Retired agent ({arch.agent_id}, state=RETIRED) was permitted "
                    f"to spawn subagent '{cid}'! Dead agents should not spawn children."
                )
            except ValueError as e:
                self.record_pass(name, cat, f"Retired parent spawning correctly rejected: {e}")
        except Exception as e:
            self.record_fail(name, cat, "Exception during test", e)

    def test_3_2_parent_unregistered_zombie_subagents(self):
        name = "Parent Unregistration Leaving Zombie Subagents"
        cat = "Parent Lifecycle"
        try:
            coord = SimulationCoordinator()
            arch = ArchitectAgent(agent_id="arch_zombie_test", name="Arch", funds=100.0)
            coord.register_agent(arch)
            manager = SubagentManager()

            cid = manager.spawn_subagent(
                arch, "SURVEYOR", budget=30.0, coordinator=coord, economy_system=coord.economy
            )

            # Unregister parent from coordinator
            coord.unregister_agent("arch_zombie_test")

            # Check if subagent is still active in coordinator
            sub_in_coord = cid in coord.agents
            if sub_in_coord:
                # Subagent is orphaned
                sub_agent = coord.agents[cid]
                self.record_vuln(
                    name,
                    cat,
                    f"VULNERABILITY: Unregistering parent 'arch_zombie_test' left orphan subagent '{cid}' "
                    f"active in simulation (state={sub_agent.state}). Subagent has dangling parent_id."
                )
            else:
                self.record_pass(name, cat, "Unregistering parent cleanly cascaded to subagents.")
        except Exception as e:
            self.record_fail(name, cat, "Exception during test", e)

    def test_3_3_permanent_district_supervisor_timeout(self):
        name = "Permanent DistrictSupervisor Premature Timeout"
        cat = "Parent Lifecycle"
        try:
            manager = SubagentManager()
            mayor = MayorAgent(agent_id="mayor_perm_test", name="Mayor", funds=500.0)
            ds_id = manager.spawn_subagent(mayor, "DISTRICT_SUPERVISOR")
            ds = manager.subagents[ds_id]

            # Verify it is permanent
            if ds.is_temporary or ds.lifespan_ticks is not None:
                self.record_vuln(name, cat, f"DistrictSupervisor is marked temporary ({ds.is_temporary}) or has lifespan ({ds.lifespan_ticks}).")
                return

            contract = manager.contracts[ds_id]
            # Check contract max_duration_ticks
            if contract.max_duration_ticks == 20:
                # Run 20 ticks
                timed_out = []
                for t in range(1, 22):
                    to = manager.step_contracts(t)
                    if to:
                        timed_out.extend(to)

                if ds_id in timed_out:
                    self.record_vuln(
                        name,
                        cat,
                        f"VULNERABILITY: Permanent DistrictSupervisor was prematurely timed out and retired "
                        f"after 20 ticks because DelegationContract defaulted max_duration_ticks=20!"
                    )
                else:
                    self.record_pass(name, cat, "Permanent supervisor survived 20 ticks.")
            else:
                self.record_pass(name, cat, f"Contract max_duration_ticks properly configured for permanent: {contract.max_duration_ticks}")
        except Exception as e:
            self.record_fail(name, cat, "Exception during test", e)

    # =========================================================================
    # SUITE 4: Resource Escrow Leakage, Depletion, and Balances
    # =========================================================================

    def test_4_1_negative_budget_injection(self):
        name = "Negative Budget Escrow Exploit"
        cat = "Escrow Integrity"
        try:
            manager = SubagentManager()
            arch = ArchitectAgent(agent_id="arch_neg_bud", name="Arch", funds=100.0)

            # Adversarial input: negative budget
            try:
                cid = manager.spawn_subagent(arch, "SURVEYOR", budget=-100.0)
                # Check arch funds
                if arch.funds > 100.0:
                    self.record_vuln(
                        name,
                        cat,
                        f"CRITICAL VULNERABILITY: Negative budget (-100.0) minted funds! "
                        f"Parent funds increased from 100.0 to {arch.funds}."
                    )
                else:
                    self.record_vuln(name, cat, f"Spawn succeeded with negative budget! Child funds: {manager.subagents[cid].funds}")
            except ValueError as e:
                self.record_pass(name, cat, f"Negative budget correctly rejected: {e}")
        except Exception as e:
            self.record_fail(name, cat, "Exception during test", e)

    def test_4_2_over_refund_inflation(self):
        name = "Over-Refund Escrow Inflation Exploit"
        cat = "Escrow Integrity"
        try:
            manager = SubagentManager()
            arch = ArchitectAgent(agent_id="arch_over_ref", name="Arch", funds=100.0)
            cid = manager.spawn_subagent(arch, "SURVEYOR", budget=25.0)
            # Arch funds = 75.0

            # Adversarial retirement: claim 500.0 unspent funds on a 25.0 escrow
            refund_info = manager.retire_subagent(cid, unspent_funds=500.0, parent_agent=arch)

            if arch.funds > 100.0:
                self.record_vuln(
                    name,
                    cat,
                    f"CRITICAL VULNERABILITY: Over-refund inflation! Escrow was 25.0, but retiring with "
                    f"unspent_funds=500.0 inflated parent funds to {arch.funds} (net profit: +{arch.funds - 100.0})."
                )
            else:
                self.record_pass(name, cat, "Over-refund was capped or rejected.")
        except Exception as e:
            self.record_fail(name, cat, "Exception during test", e)

    def test_4_3_negative_refund_underflow(self):
        name = "Negative Refund Balance Underflow"
        cat = "Escrow Integrity"
        try:
            manager = SubagentManager()
            arch = ArchitectAgent(agent_id="arch_neg_ref", name="Arch", funds=25.0)
            cid = manager.spawn_subagent(arch, "SURVEYOR", budget=25.0)
            # Arch funds = 0.0

            # Adversarial retirement: pass negative unspent funds
            try:
                refund_info = manager.retire_subagent(cid, unspent_funds=-50.0, parent_agent=arch)
                if arch.funds < 0.0:
                    self.record_vuln(
                        name,
                        cat,
                        f"CRITICAL VULNERABILITY: Negative refund underflow! Parent funds dropped to negative: {arch.funds}."
                    )
                else:
                    self.record_pass(name, cat, f"Negative refund prevented negative balance (funds={arch.funds}).")
            except Exception as e:
                # If Pydantic validate_assignment raised validation error, check if escrow was already popped (inconsistent state)
                if "greater_than_equal" in str(e):
                    if cid not in manager.escrows and cid not in manager.subagents:
                        self.record_vuln(
                            name,
                            cat,
                            f"VULNERABILITY: Negative refund crashed retire_subagent with unhandled Pydantic validation error ({type(e).__name__}), "
                            f"leaving escrow popped from vault but parent funds unrefunded and transaction corrupted!"
                        )
                    else:
                        self.record_pass(name, cat, f"Pydantic prevented negative funds: {e}")
                else:
                    self.record_fail(name, cat, "Exception during test", e)
        except Exception as e:
            self.record_fail(name, cat, "Exception during test", e)

    def test_4_4_escrow_leak_on_parent_unregistration(self):
        name = "Escrow Currency Evaporation on Parent Death"
        cat = "Escrow Integrity"
        try:
            coord = SimulationCoordinator()
            arch = ArchitectAgent(agent_id="arch_leak_test", name="Arch", funds=100.0)
            coord.register_agent(arch)
            manager = SubagentManager()

            cid = manager.spawn_subagent(
                arch, "SURVEYOR", budget=40.0, coordinator=coord, economy_system=coord.economy
            )

            # Unregister parent
            coord.unregister_agent("arch_leak_test")

            # Retire subagent with 40 funds unspent
            refund = manager.retire_subagent(cid, unspent_funds=40.0, economy_system=coord.economy)

            # Check where the 40 funds went
            parent_ledger = coord.economy.get_ledger("arch_leak_test")
            treasury = coord.economy.treasury

            if parent_ledger is None:
                # Funds are not in parent ledger. Are they in treasury?
                # Initial treasury funds: coord.config.initial_treasury_funds (10000.0)
                if treasury.funds == coord.config.initial_treasury_funds:
                    self.record_vuln(
                        name,
                        cat,
                        f"VULNERABILITY: 40.0 escrowed funds evaporated! Parent ledger is None and "
                        f"treasury did not receive the orphaned escrow. Refund reported '{refund['refunded_funds']}' "
                        f"but funds vanished from the economy."
                    )
                else:
                    self.record_pass(name, cat, "Orphaned escrow was swept to treasury.")
            else:
                self.record_pass(name, cat, f"Parent ledger received refund: {parent_ledger.funds}")
        except Exception as e:
            self.record_fail(name, cat, "Exception during test", e)

    def test_4_5_double_retirement_replay(self):
        name = "Double-Retirement Replay Exploit"
        cat = "Escrow Integrity"
        try:
            manager = SubagentManager()
            arch = ArchitectAgent(agent_id="arch_double_ret", name="Arch", funds=100.0)
            cid = manager.spawn_subagent(arch, "SURVEYOR", budget=30.0)
            # Arch funds = 70.0

            # First retire
            r1 = manager.retire_subagent(cid, unspent_funds=30.0, parent_agent=arch)
            funds_after_r1 = arch.funds  # Should be 100.0

            # Second retire attempt
            r2 = manager.retire_subagent(cid, unspent_funds=30.0, parent_agent=arch)
            funds_after_r2 = arch.funds

            if funds_after_r2 > funds_after_r1:
                self.record_vuln(
                    name,
                    cat,
                    f"CRITICAL VULNERABILITY: Double retirement replay allowed! Parent received second refund, "
                    f"funds increased from {funds_after_r1} to {funds_after_r2}."
                )
            else:
                self.record_pass(name, cat, f"Replay attack prevented. Funds remained {funds_after_r2}.")
        except Exception as e:
            self.record_fail(name, cat, "Exception during test", e)

    def test_4_6_conservation_of_currency_stress_loop(self):
        name = "100-Cycle Currency Conservation Stress Loop"
        cat = "Escrow Integrity"
        try:
            manager = SubagentManager()
            economy = EconomySystem(DEFAULT_CONFIG)
            p_ledger = economy.register_account("parent_loop", funds=500.0, materials=100.0)
            initial_funds = p_ledger.funds

            for cycle in range(100):
                cid = manager.spawn_subagent(
                    "parent_loop",
                    "SURVEYOR",
                    budget=50.0,
                    economy_system=economy,
                )
                # Unspent: 30 funds (spent 20)
                manager.retire_subagent(
                    cid,
                    unspent_funds=30.0,
                    economy_system=economy,
                )
                # Cost per cycle should be exactly 20.0 funds
                # Re-add 20.0 funds to keep solvent
                p_ledger.deposit(funds=20.0)

            final_funds = p_ledger.funds
            diff = round(final_funds - initial_funds, 4)
            if diff == 0.0:
                self.record_pass(name, cat, f"100 spawn/retire cycles conserved funds perfectly (drift = {diff}).")
            else:
                self.record_vuln(name, cat, f"Currency conservation failure across 100 cycles: drift of {diff} funds!")
        except Exception as e:
            self.record_fail(name, cat, "Exception during test", e)

    # =========================================================================
    # SUITE 5: Simulation Stepping, Democratic Voting & Stability
    # =========================================================================

    def test_5_1_subagent_voting_ballot_stuffing(self):
        name = "Subagent Democratic Ballot Stuffing"
        cat = "Governance Integrity"
        try:
            coord = SimulationCoordinator()
            manager = SubagentManager()

            # Create mayor proposal requiring quorum of 3
            proposal = CivicProposal(
                creator_id="mayor_1",
                title="Municipal Tax Reform",
                description="Adjust sales tax rate to 15 percent",
                action_type="ADJUST_TAX",
                action_payload={"sales_tax_rate": 0.15},
                created_tick=1,
                expires_tick=10,
                quorum_required=3,
            )
            coord.message_bus.submit_proposal(proposal)

            # Spawn 2 subagents from architect
            arch = ArchitectAgent(agent_id="arch_ballot", name="Arch", funds=100.0)
            coord.register_agent(arch)
            c1 = manager.spawn_subagent(arch, "SURVEYOR", coordinator=coord)
            c2 = manager.spawn_subagent(arch, "SURVEYOR", coordinator=coord)

            # Subagents cast votes
            vote_success_1 = coord.message_bus.cast_vote(proposal.id, c1, VoteChoice.AYE)
            vote_success_2 = coord.message_bus.cast_vote(proposal.id, c2, VoteChoice.AYE)

            if vote_success_1 and vote_success_2:
                # Only 1 real citizen (arch) exists, but 2 temporary subagents voted and achieved quorum!
                self.record_vuln(
                    name,
                    cat,
                    f"VULNERABILITY: Temporary subagents ('{c1}', '{c2}') were permitted to cast official "
                    f"governance votes on proposal '{proposal.id}', enabling ballot-stuffing by spawning subagents."
                )
            else:
                self.record_pass(name, cat, "Subagents were restricted from voting on civic proposals.")
        except Exception as e:
            self.record_fail(name, cat, "Exception during test", e)

    def test_5_2_multi_agent_50_tick_subagent_stability(self):
        name = "50-Tick Multi-Agent Simulation with Active Subagents"
        cat = "Simulation Stability"
        try:
            import asyncio

            async def run_sim():
                coord = SimulationCoordinator()
                manager = SubagentManager()

                # Register 6 primary agents
                agents = [
                    MayorAgent(agent_id="may_s", name="Mayor", position=(2, 2)),
                    ArchitectAgent(agent_id="arc_s", name="Arch", position=(5, 5)),
                    EngineerAgent(agent_id="eng_s", name="Eng", position=(8, 8)),
                    MerchantAgent(agent_id="mer_s", name="Mer", position=(11, 11)),
                    ScholarAgent(agent_id="sch_s", name="Sch", position=(14, 14)),
                    ObserverAgent(agent_id="obs_s", name="Obs", position=(17, 17)),
                ]
                for a in agents:
                    coord.register_agent(a)

                # Spawn subagents
                s1 = manager.spawn_subagent("arc_s", "SURVEYOR", budget=20.0, coordinator=coord)
                s2 = manager.spawn_subagent("eng_s", "CONSTRUCTION_CREW", budget=20.0, coordinator=coord)

                # Run 50 ticks
                deltas = []
                for tick in range(50):
                    delta = await coord.step()
                    deltas.append(delta)
                    # Step delegation contracts
                    manager.step_contracts(tick, economy_system=coord.economy, coordinator=coord)

                return len(deltas)

            ticks_run = asyncio.run(run_sim())
            self.record_pass(name, cat, f"Simulation ran 50 ticks stably with subagents and primary council.")
        except Exception as e:
            self.record_fail(name, cat, "Crash during 50-tick simulation", e)

    # =========================================================================
    # Run All Suites & Summarize
    # =========================================================================

    def run_all(self):
        print("=" * 80)
        print("RUNNING EMPIRICAL ADVERSARIAL STRESS SUITE: SUBAGENT LIFECYCLES")
        print("=" * 80)

        # Suite 1
        print("\n--- Suite 1: Recursion Depth Violations & Guard Bypasses ---")
        self.test_1_1_direct_subagent_spawn_blocked()
        self.test_1_2_string_id_recursion_bypass()
        self.test_1_3_forged_flags_lineage_check()

        # Suite 2
        print("\n--- Suite 2: Concurrency Caps & Quota Exploits ---")
        self.test_2_1_role_concurrency_caps_enforced()
        self.test_2_2_string_id_default_role_cap_breach()
        self.test_2_3_quota_restoration_after_retirement()
        self.test_2_4_high_volume_concurrency_burst()

        # Suite 3
        print("\n--- Suite 3: Parent Retirement & Orphan Recovery ---")
        self.test_3_1_spawning_from_retired_parent()
        self.test_3_2_parent_unregistered_zombie_subagents()
        self.test_3_3_permanent_district_supervisor_timeout()

        # Suite 4
        print("\n--- Suite 4: Escrow Leakage, Depletion & Balances ---")
        self.test_4_1_negative_budget_injection()
        self.test_4_2_over_refund_inflation()
        self.test_4_3_negative_refund_underflow()
        self.test_4_4_escrow_leak_on_parent_unregistration()
        self.test_4_5_double_retirement_replay()
        self.test_4_6_conservation_of_currency_stress_loop()

        # Suite 5
        print("\n--- Suite 5: Simulation Stepping & Governance Integrity ---")
        self.test_5_1_subagent_voting_ballot_stuffing()
        self.test_5_2_multi_agent_50_tick_subagent_stability()

        # Verdict
        passed = sum(1 for r in self.results if r.passed)
        vulns = sum(1 for r in self.results if r.vulnerability_found)
        failed = sum(1 for r in self.results if not r.passed and not r.vulnerability_found)
        total = len(self.results)

        print("\n" + "=" * 80)
        print(f"STRESS TEST SUMMARY: {total} tests executed")
        print(f"  Passed: {passed}")
        print(f"  Vulnerabilities Found: {vulns}")
        print(f"  Errors/Failed: {failed}")
        print("=" * 80)

        if vulns > 0 or failed > 0:
            print("\nGATE VERDICT: REJECT")
            print("Action required: Fix subagent lifecycle vulnerabilities before Milestone 3 progression.")
        else:
            print("\nGATE VERDICT: APPROVE")

        return vulns, failed


if __name__ == "__main__":
    tester = SubagentStressTester()
    v, f = tester.run_all()
    # Exit with code 1 if vulnerabilities found, for CI / harness automation
    sys.exit(0 if v == 0 and f == 0 else 1)
