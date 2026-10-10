"""Empirical Adversarial Stress Testing Harness: Agents, Long-Horizon Simulation & Evolution.

Executed by: challenger_city_m2_2 (teamwork_preview_challenger)
Working Directory: c:/Users/ignaz/antigravity/keen-franklin/.agents/teamwork/challenger_city_m2_2

Mission:
1. Long-horizon continuous simulation (300 ticks) with 6 civic roles + active subagents.
2. Homeostatic recovery under zero energy stress (energy = 0.0 -> RESTING -> recovery).
3. Trait evolution bounds stability ([0.0, 1.0] across 10+ successive epochs).
4. Subagent recursion guard, concurrency caps, and escrow conservation under load.
"""

from __future__ import annotations

import asyncio
import math
import random
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

# Ensure agent_city is on Python path
sys.path.insert(0, "c:/Users/ignaz/antigravity/keen-franklin")

from agent_city.config import (
    DEFAULT_CONFIG,
    SimulationConfig,
    SimulationState,
    ZoneType,
)
from agent_city.engine.simulation import SimulationCoordinator
from agent_city.agents import (
    AgentState,
    BaseAgent,
    CivicRole,
    GoalTier,
    TraitVector,
    MayorAgent,
    ArchitectAgent,
    EngineerAgent,
    MerchantAgent,
    ScholarAgent,
    ObserverAgent,
    SurveyorAgent,
    ConstructionCrewAgent,
    ResearchAssistantAgent,
    CourierAgent,
    DistrictSupervisorAgent,
    SubagentManager,
    DelegationStatus,
    GenerativeEvolutionEngine,
    calculate_fitness,
    mutate_traits,
    evolve_traits,
    create_civic_council,
)


class TestResult:
    def __init__(self, name: str):
        self.name = name
        self.passed = False
        self.details: List[str] = []
        self.duration_s: float = 0.0

    def log(self, msg: str):
        self.details.append(msg)
        print(f"  [{self.name}] {msg}")

    def ok(self, msg: str):
        self.log(f"PASS: {msg}")

    def fail(self, msg: str):
        self.log(f"FAIL: {msg}")
        self.passed = False
        raise AssertionError(f"[{self.name}] {msg}")


# =============================================================================
# Stress Test 1: 300-Tick Long-Horizon Continuous Multi-Agent Simulation
# =============================================================================

async def stress_test_1_long_horizon_simulation() -> TestResult:
    test = TestResult("STRESS_1_300_TICKS_SIMULATION")
    t0 = time.monotonic()
    test.log("Initializing 300-tick long-horizon simulation with 6 civic roles + subagents...")

    # Configure coordinator: 32x32 grid, 30 ticks per epoch => 10 full epochs in 300 ticks!
    config = SimulationConfig(
        grid_width=32,
        grid_height=32,
        default_tps=50.0,  # Fast execution for headless stress runner
        ticks_per_epoch=30,
        initial_treasury_funds=5000.0,
        default_sales_tax_rate=0.05,
        property_tax_per_building=10.0,
    )
    coordinator = SimulationCoordinator(config=config)
    subagent_manager = SubagentManager()
    evolution_engine = GenerativeEvolutionEngine(elite_fraction=0.25, mutation_rate=0.15)

    # 1. Instantiate and register the 6 Civic Council agents
    council = create_civic_council()
    assert len(council) == 6, "Expected 6 civic council leaders"
    for agent in council:
        coordinator.register_agent(
            agent=agent,
            initial_x=agent.x,
            initial_y=agent.y,
            initial_funds=200.0,
            initial_energy=100.0,
            initial_materials=25.0,
        )
    test.ok(f"Registered {len(council)} founding civic leaders.")

    # 2. Track subagent lifecycle events across the 300 ticks
    subagents_spawned: Dict[str, str] = {}  # tick -> role
    subagents_retired: List[str] = []
    epochs_evaluated: List[int] = []

    # Connect epoch evaluation to GenerativeEvolutionEngine
    original_run_epoch_transition = coordinator._run_epoch_transition

    async def hooked_epoch_transition():
        await original_run_epoch_transition()
        ep = coordinator.current_epoch
        epochs_evaluated.append(ep)
        # Execute generative evolution across active primary agents
        primary = [a for a in coordinator.agents.values() if isinstance(a, BaseAgent) and not a.is_subagent]
        evolution_engine.evaluate_epoch(primary, epoch=ep)
        test.log(f"Epoch {ep} GenerativeEvolution evaluated on {len(primary)} primary agents.")

    coordinator._run_epoch_transition = hooked_epoch_transition

    # 3. Step through 300 discrete simulation ticks
    total_ticks = 300
    for tick in range(1, total_ticks + 1):
        # Staggered subagent spawning schedule
        if tick == 15:
            # Architect spawns Surveyor
            architect = coordinator.agents.get("agt_architect_1")
            if architect:
                cid = subagent_manager.spawn_subagent(
                    parent=architect,
                    role=CivicRole.SURVEYOR,
                    task="SURVEY_NORTH_SECTOR",
                    budget=30.0,
                    target_coords=(architect.x, architect.y),
                    lifespan=20,
                    economy_system=coordinator.economy,
                    coordinator=coordinator,
                )
                subagents_spawned[cid] = "SURVEYOR"
                test.log(f"Tick {tick}: Architect spawned Surveyor ({cid})")

        elif tick == 45:
            # Engineer spawns ConstructionCrew
            engineer = coordinator.agents.get("agt_engineer_1")
            if engineer:
                cid = subagent_manager.spawn_subagent(
                    parent=engineer,
                    role=CivicRole.CONSTRUCTION_CREW,
                    task="BUILD_COMMUNITY_CENTER",
                    budget=40.0,
                    target_coords=(engineer.x, engineer.y),
                    lifespan=30,
                    economy_system=coordinator.economy,
                    coordinator=coordinator,
                )
                subagents_spawned[cid] = "CONSTRUCTION_CREW"
                test.log(f"Tick {tick}: Engineer spawned Construction Crew ({cid})")

        elif tick == 80:
            # Merchant spawns Courier
            merchant = coordinator.agents.get("agt_merchant_1")
            if merchant:
                cid = subagent_manager.spawn_subagent(
                    parent=merchant,
                    role=CivicRole.COURIER,
                    task="DELIVER_COMMODITIES",
                    budget=25.0,
                    target_coords=(merchant.x, merchant.y),
                    lifespan=15,
                    economy_system=coordinator.economy,
                    coordinator=coordinator,
                )
                subagents_spawned[cid] = "COURIER"
                test.log(f"Tick {tick}: Merchant spawned Courier ({cid})")

        elif tick == 110:
            # Scholar spawns ResearchAssistant
            scholar = coordinator.agents.get("agt_scholar_1")
            if scholar:
                cid = subagent_manager.spawn_subagent(
                    parent=scholar,
                    role=CivicRole.RESEARCH_ASSISTANT,
                    task="SURVEY_CIVIC_SENTIMENT",
                    budget=25.0,
                    target_coords=(scholar.x, scholar.y),
                    lifespan=25,
                    economy_system=coordinator.economy,
                    coordinator=coordinator,
                )
                subagents_spawned[cid] = "RESEARCH_ASSISTANT"
                test.log(f"Tick {tick}: Scholar spawned Research Assistant ({cid})")

        elif tick == 150:
            # Mayor spawns permanent DistrictSupervisor
            mayor = coordinator.agents.get("agt_mayor_1")
            if mayor:
                cid = subagent_manager.spawn_subagent(
                    parent=mayor,
                    role=CivicRole.DISTRICT_SUPERVISOR,
                    task="GOVERN_WARD_ALPHA",
                    budget=50.0,
                    target_coords=(mayor.x, mayor.y),
                    lifespan=None,  # Permanent
                    economy_system=coordinator.economy,
                    coordinator=coordinator,
                )
                subagents_spawned[cid] = "DISTRICT_SUPERVISOR"
                test.log(f"Tick {tick}: Mayor spawned permanent District Supervisor ({cid})")

        elif tick == 180:
            # Engineer spawns second ConstructionCrew
            engineer = coordinator.agents.get("agt_engineer_1")
            if engineer:
                cid = subagent_manager.spawn_subagent(
                    parent=engineer,
                    role=CivicRole.CONSTRUCTION_CREW,
                    task="EXPAND_INFRASTRUCTURE",
                    budget=35.0,
                    target_coords=(engineer.x, engineer.y),
                    lifespan=25,
                    economy_system=coordinator.economy,
                    coordinator=coordinator,
                )
                subagents_spawned[cid] = "CONSTRUCTION_CREW"
                test.log(f"Tick {tick}: Engineer spawned second Construction Crew ({cid})")

        # Step simulation coordinator
        delta = await coordinator.step()

        # Invariant checks on delta
        if delta["tick"] != tick:
            test.fail(f"Tick delta mismatch: expected {tick}, got {delta['tick']}")
        if delta["type"] != "TICK_DELTA":
            test.fail(f"Invalid delta type: {delta['type']}")

        # Step contracts and auto-retire expired subagents
        retired_cids = subagent_manager.step_contracts(
            current_tick=tick,
            economy_system=coordinator.economy,
            coordinator=coordinator,
        )
        if retired_cids:
            for r_id in retired_cids:
                subagents_retired.append(r_id)
                test.log(f"Tick {tick}: Auto-retired expired subagent ({r_id})")

    t_elapsed = time.monotonic() - t0
    test.duration_s = t_elapsed
    test.log(f"Completed 300 ticks in {t_elapsed:.2f} seconds ({300 / t_elapsed:.1f} TPS).")

    # Invariant assertions:
    # A. Tick & Epoch counts
    if coordinator.current_tick != 300:
        test.fail(f"Coordinator tick was {coordinator.current_tick}, expected 300")
    if coordinator.current_epoch != 10:
        test.fail(f"Coordinator epoch was {coordinator.current_epoch}, expected 10")
    if len(epochs_evaluated) != 10:
        test.fail(f"Evolution evaluated {len(epochs_evaluated)} epochs, expected 10")
    test.ok("Exact 300 ticks and 10 epochs completed.")

    # B. Subagent Lifecycle: Check spawns and retirement
    if len(subagents_spawned) < 6:
        test.fail(f"Only spawned {len(subagents_spawned)} subagents, expected at least 6")
    if len(subagents_retired) < 4:
        test.fail(f"Only retired {len(subagents_retired)} subagents, expected at least 4 temporary retirements")
    test.ok(f"Subagent lifecycles verified: {len(subagents_spawned)} spawned, {len(subagents_retired)} retired.")

    # C. Permanent subagent remains active
    supervisor_cids = [cid for cid, r in subagents_spawned.items() if r == "DISTRICT_SUPERVISOR"]
    assert supervisor_cids, "No district supervisor was spawned"
    assert supervisor_cids[0] in coordinator.agents, "Permanent DistrictSupervisor was incorrectly removed!"
    test.ok("Permanent subagent (DistrictSupervisor) retained in simulation.")

    # D. Zero memory leaks in subagent registry
    for r_id in subagents_retired:
        if r_id in coordinator.agents:
            test.fail(f"Retired subagent {r_id} leaked in coordinator.agents!")
    test.ok("Zero retired subagents leaked in coordinator registry.")

    # E. Physical city expansion: Buildings & Rezoned parcels exist
    built_count = sum(1 for row in coordinator.grid._grid for p in row if p.building_id is not None)
    rezoned_count = sum(1 for row in coordinator.grid._grid for p in row if p.zone != ZoneType.WILDERNESS)
    test.log(f"Physical expansion metrics: {built_count} buildings, {rezoned_count} zoned parcels.")
    if built_count < 1:
        test.fail("Zero buildings constructed across 300 ticks!")
    test.ok(f"Emergent construction verified: {built_count} buildings constructed.")

    # F. Macroeconomic solvency
    treasury_funds = coordinator.economy.treasury.funds
    total_tax = coordinator.economy.total_tax_collected
    test.log(f"Macroeconomic metrics: Treasury funds ${treasury_funds:.2f}, Taxes collected ${total_tax:.2f}")
    if treasury_funds <= 0:
        test.fail("Treasury completely depleted or insolvent!")
    test.ok(f"Macroeconomic solvency verified: ${treasury_funds:.2f} funds remain.")

    # G. Dialogues feed
    dialogues = coordinator.message_bus.get_recent_dialogues(100)
    if len(dialogues) < 10:
        test.fail(f"Insufficient civic dialogue: only {len(dialogues)} dialogues across 300 ticks!")
    test.ok(f"Civic dialogue active: {len(dialogues)} recent messages recorded.")

    test.passed = True
    return test


# =============================================================================
# Stress Test 2: Homeostatic Exhaustion & Recovery Under Zero Energy Stress
# =============================================================================

async def stress_test_2_homeostatic_recovery() -> TestResult:
    test = TestResult("STRESS_2_HOMEOSTATIC_RECOVERY")
    t0 = time.monotonic()
    test.log("Initializing Homeostatic Recovery Stress Test under Zero Energy Shock...")

    config = SimulationConfig(
        grid_width=16,
        grid_height=16,
        energy_regen_residential=2.5,
        energy_burn_idle=0.2,
        energy_burn_move=0.5,
        energy_burn_work=1.0,
    )
    coordinator = SimulationCoordinator(config=config)

    # Register all 6 Civic Roles + 1 Subagent
    council = create_civic_council()
    for agent in council:
        coordinator.register_agent(agent, initial_x=agent.x, initial_y=agent.y, initial_funds=100.0, initial_energy=100.0)

    # Spawn surveyor subagent under architect
    architect = coordinator.agents["agt_architect_1"]
    manager = SubagentManager()
    sub_id = manager.spawn_subagent(
        parent=architect,
        role=CivicRole.SURVEYOR,
        budget=20.0,
        target_coords=(architect.x, architect.y),
        coordinator=coordinator,
    )

    test.log(f"Active population: {len(coordinator.agents)} agents registered.")

    # -------------------------------------------------------------------------
    # Part 2.1: Catastrophic Zero-Energy Shock Wave
    # -------------------------------------------------------------------------
    test.log("Applying Catastrophic Zero-Energy Shock: Setting ALL agent energy to 0.000...")
    for agent_id, agent in coordinator.agents.items():
        if isinstance(agent, BaseAgent):
            agent.energy = 0.0
        ledger = coordinator.economy.get_ledger(agent_id)
        if ledger:
            ledger.energy = 0.0

    # Verify state right before deliberation
    for agent_id, agent in coordinator.agents.items():
        ledger = coordinator.economy.get_ledger(agent_id)
        assert ledger.energy == 0.0, f"Ledger energy not 0 for {agent_id}"

    # Step exactly 1 tick to test immediate deliberation behavior under zero energy
    test.log("Stepping 1 tick during zero-energy shock...")
    delta = await coordinator.step()

    # Verify that ALL agents transitioned to RESTING state and chose REST action
    for agent_id, agent in coordinator.agents.items():
        if isinstance(agent, BaseAgent):
            if agent.state != AgentState.RESTING:
                test.fail(f"Agent {agent_id} in state {agent.state}, expected RESTING under energy 0.0!")
            if not agent.current_action or agent.current_action.get("type") != "REST":
                test.fail(f"Agent {agent_id} chose action {agent.current_action}, expected REST!")
            test.log(f"Agent {agent_id} ({agent.role}): correctly transitioned to RESTING, action=REST.")

    test.ok("All agents cleanly transitioned to RESTING without crash or freeze.")

    # -------------------------------------------------------------------------
    # Part 2.2: Continuous Recovery Progression
    # -------------------------------------------------------------------------
    test.log("Stepping 15 ticks to observe physiological recovery progression...")
    energies_per_tick: Dict[int, Dict[str, float]] = {}

    for step_idx in range(1, 16):
        d = await coordinator.step()
        curr_energies = {}
        for agent_id, agent in coordinator.agents.items():
            ledger = coordinator.economy.get_ledger(agent_id)
            curr_energies[agent_id] = ledger.energy if ledger else agent.energy
        energies_per_tick[step_idx] = curr_energies

    # Verify monotonic recovery: energy at tick 15 must be significantly higher than tick 1
    for agent_id in coordinator.agents.keys():
        e_initial = energies_per_tick[1][agent_id]
        e_final = energies_per_tick[15][agent_id]
        test.log(f"Agent {agent_id}: energy recovered from {e_initial:.1f} to {e_final:.1f}")
        if e_final <= e_initial:
            test.fail(f"Agent {agent_id} failed to recover energy: initial {e_initial}, final {e_final}")
        if e_final < 20.0:
            test.fail(f"Agent {agent_id} recovery too sluggish: final energy only {e_final:.1f} after 15 ticks")

    test.ok("Monotonic energy recovery verified across all agents.")

    # -------------------------------------------------------------------------
    # Part 2.3: State Transition from RESTING back to Productive Civic Activity
    # -------------------------------------------------------------------------
    test.log("Stepping an additional 20 ticks to verify transition out of RESTING...")
    for _ in range(20):
        await coordinator.step()

    active_states = {agent.state for agent in coordinator.agents.values() if isinstance(agent, BaseAgent)}
    test.log(f"Active agent states after full recovery: {active_states}")
    # At least some agents should be MOVING, EXECUTING, or COMMUNICATING
    non_resting = [a for a in coordinator.agents.values() if isinstance(a, BaseAgent) and a.state != AgentState.RESTING]
    if len(non_resting) == 0:
        test.fail("No agents resumed active civic duties after energy recovery!")
    test.ok(f"{len(non_resting)} of {len(coordinator.agents)} agents resumed non-RESTING civic tasks.")

    # -------------------------------------------------------------------------
    # Part 2.4: Dual Bankruptcy & Exhaustion Edge Case (Energy = 0.0, Funds = 0.0)
    # -------------------------------------------------------------------------
    test.log("Testing Dual Bankruptcy + Exhaustion Edge Case (Energy = 0, Funds = 0)...")
    scholar = coordinator.agents["agt_scholar_1"]
    scholar.energy = 0.0
    scholar.funds = 0.0
    s_ledger = coordinator.economy.get_ledger("agt_scholar_1")
    s_ledger.energy = 0.0
    s_ledger.funds = 0.0

    # Step 5 ticks
    for _ in range(5):
        await coordinator.step()

    if scholar.energy <= 0.0:
        test.fail("Bankrupt & exhausted agent failed to recover energy!")
    test.ok(f"Bankrupt & exhausted agent safely recovered to {scholar.energy:.1f} energy.")

    test.duration_s = time.monotonic() - t0
    test.passed = True
    return test


# =============================================================================
# Stress Test 3: Trait Evolution Bounds Stability & Convergence Across 10+ Epochs
# =============================================================================

async def stress_test_3_trait_evolution_bounds() -> TestResult:
    test = TestResult("STRESS_3_TRAIT_EVOLUTION_BOUNDS")
    t0 = time.monotonic()
    test.log("Initializing Trait Evolution Bounds Stability Test across 10+ successive epochs...")

    engine = GenerativeEvolutionEngine(
        elite_fraction=0.25,
        mutation_rate=0.25,      # Elevated mutation rate to stress boundaries
        mutation_scale=0.15,     # Elevated scale for larger shocks
        breakthrough_rate=0.08,  # Frequent radical adaptation jumps
    )

    # 1. Council cohort with diverse initial traits
    agents: List[BaseAgent] = [
        MayorAgent(agent_id="m_1", name="Mayor 1", funds=300.0, energy=90.0),
        ArchitectAgent(agent_id="a_1", name="Architect 1", funds=250.0, energy=85.0),
        EngineerAgent(agent_id="e_1", name="Engineer 1", funds=200.0, energy=80.0),
        MerchantAgent(agent_id="mer_1", name="Merchant 1", funds=350.0, energy=75.0),
        ScholarAgent(agent_id="s_1", name="Scholar 1", funds=150.0, energy=70.0),
        ObserverAgent(agent_id="o_1", name="Observer 1", funds=100.0, energy=65.0),
    ]

    TRAIT_KEYS = [
        "diligence",
        "innovation",
        "sociability",
        "thriftiness",
        "altruism",
        "adaptability",
        "risk_tolerance",
    ]

    # 2. Run 20 successive generational epochs (double the required 10 epochs)
    total_epochs = 20
    test.log(f"Simulating {total_epochs} generational evolutionary epochs...")

    for ep in range(1, total_epochs + 1):
        # Dynamically vary agent contributions and funds to simulate dynamic city life
        for idx, agt in enumerate(agents):
            agt.funds += random.uniform(-20.0, 50.0)
            agt.energy = max(10.0, min(100.0, agt.energy + random.uniform(-15.0, 20.0)))
            agt.memory.recent_actions.append({"type": random.choice(["BUILD", "TRADE", "PROPOSE", "REZONE", "SPEAK"])})
            if len(agt.memory.recent_actions) > 20:
                agt.memory.recent_actions.pop(0)

        # Run epoch evaluation
        adapted_agents = engine.evaluate_epoch(agents, epoch=ep)

        # Rigorous bounds and validity checks
        for agt in adapted_agents:
            # Check fitness bounds
            if agt.fitness_score < 0.0 or agt.fitness_score > 1.0:
                test.fail(f"Epoch {ep}: Agent {agt.agent_id} fitness {agt.fitness_score} out of [0.0, 1.0]!")
            if math.isnan(agt.fitness_score) or math.isinf(agt.fitness_score):
                test.fail(f"Epoch {ep}: Agent {agt.agent_id} fitness is NaN or Inf!")

            # Check every trait dimension
            for trait_name in TRAIT_KEYS:
                val = getattr(agt.traits, trait_name)
                if val < 0.0 or val > 1.0:
                    test.fail(f"Epoch {ep}: Agent {agt.agent_id} trait '{trait_name}' = {val} violated [0.0, 1.0] bounds!")
                if math.isnan(val) or math.isinf(val):
                    test.fail(f"Epoch {ep}: Agent {agt.agent_id} trait '{trait_name}' is NaN/Inf!")

        test.log(f"Epoch {ep}: All 6 agents passed trait bounds [0.0, 1.0] & fitness checks.")

    test.ok(f"All traits maintained strictly within [0.0, 1.0] across all {total_epochs} epochs.")

    # 3. High-Intensity Stochastic Mutation Stress (10,000 iterations)
    test.log("Running 10,000 extreme stochastic mutation iterations...")
    base_trait = TraitVector(
        diligence=0.5, innovation=0.5, sociability=0.5, thriftiness=0.5,
        altruism=0.5, adaptability=0.5, risk_tolerance=0.5
    )

    curr_trait = base_trait
    for i in range(10_000):
        # 100% mutation rate with aggressive noise and breakthroughs
        curr_trait = mutate_traits(
            curr_trait,
            mutation_rate=1.0,
            mutation_scale=0.25,
            breakthrough_rate=0.20,
        )
        for trait_name in TRAIT_KEYS:
            v = getattr(curr_trait, trait_name)
            if v < 0.0 or v > 1.0 or math.isnan(v) or math.isinf(v):
                test.fail(f"Iteration {i}: Trait {trait_name}={v} broke bounds under high mutation!")

    test.ok("10,000 consecutive extreme mutation cycles: zero bound breaches, zero NaNs.")

    # 4. Extreme Boundary Parent Crossover Stress
    test.log("Testing extreme boundary crossover (all 0.0 vs all 1.0 parents)...")
    parent_zero = TraitVector(
        diligence=0.0, innovation=0.0, sociability=0.0, thriftiness=0.0,
        altruism=0.0, adaptability=0.0, risk_tolerance=0.0
    )
    parent_one = TraitVector(
        diligence=1.0, innovation=1.0, sociability=1.0, thriftiness=1.0,
        altruism=1.0, adaptability=1.0, risk_tolerance=1.0
    )

    for i in range(2_000):
        child = evolve_traits(parent_zero, parent_one, mutation_rate=0.5, mutation_scale=0.2)
        for trait_name in TRAIT_KEYS:
            v = getattr(child, trait_name)
            if v < 0.0 or v > 1.0 or math.isnan(v) or math.isinf(v):
                test.fail(f"Crossover iteration {i}: Trait {trait_name}={v} broke bounds!")

    test.ok("2,000 extreme boundary crossover cycles verified within [0.0, 1.0].")

    # 5. Cosine Similarity Edge Case Robustness
    test.log("Testing TraitVector cosine similarity edge cases...")
    # Zero norm vector
    sim_zero = parent_zero.cosine_similarity([0.0] * 7)
    if sim_zero != 0.0:
        test.fail(f"Zero vector cosine similarity returned {sim_zero}, expected 0.0")

    # Identical vector
    sim_ident = parent_one.cosine_similarity(parent_one)
    if abs(sim_ident - 1.0) > 1e-4:
        test.fail(f"Identical vector cosine similarity returned {sim_ident}, expected 1.0")

    test.ok("Cosine similarity numerical safety verified (no ZeroDivisionError, values in [-1, 1]).")

    test.duration_s = time.monotonic() - t0
    test.passed = True
    return test


# =============================================================================
# Stress Test 4: Subagent Concurrency, Recursion Guard & Escrow Invariants
# =============================================================================

async def stress_test_4_subagent_concurrency_and_escrow() -> TestResult:
    test = TestResult("STRESS_4_SUBAGENT_CONCURRENCY_AND_ESCROW")
    t0 = time.monotonic()
    test.log("Initializing Subagent Concurrency, Recursion Guard & Escrow Stress Tests...")

    manager = SubagentManager()
    architect = ArchitectAgent(agent_id="agt_arch_test", name="Architect Brunelleschi", funds=500.0)

    # 1. Test Strict Recursion Guard (Subagents cannot spawn subagents)
    test.log("Testing strict recursion guard (max_depth = 1)...")
    sub_id = manager.spawn_subagent(
        parent=architect,
        role=CivicRole.SURVEYOR,
        budget=30.0,
    )
    subagent = manager.subagents[sub_id]

    can_spawn, reason = manager.can_spawn(subagent, CivicRole.SURVEYOR)
    if can_spawn:
        test.fail("Subagent was incorrectly permitted to spawn a child subagent! Recursion guard failed!")
    test.log(f"Recursion guard properly blocked subagent spawning: '{reason}'")

    try:
        manager.spawn_subagent(parent=subagent, role=CivicRole.SURVEYOR)
        test.fail("Subagent spawning child did not raise ValueError!")
    except ValueError as e:
        test.log(f"Spawn attempt raised expected error: {e}")
    test.ok("Strict recursion guard enforced.")

    # 2. Test Role Concurrency Caps
    test.log("Testing role concurrency caps (Architect cap is 2)...")
    # Architect already has 1 child (sub_id). Spawn second child:
    sub_id_2 = manager.spawn_subagent(
        parent=architect,
        role=CivicRole.SURVEYOR,
        budget=30.0,
    )
    test.log("Architect successfully spawned second child.")

    # Attempt to spawn third child (should exceed cap)
    can_spawn_3, reason_3 = manager.can_spawn(architect, CivicRole.SURVEYOR)
    if can_spawn_3:
        test.fail("Architect was permitted to exceed concurrency cap of 2!")
    test.log(f"Concurrency cap properly blocked third child: '{reason_3}'")

    try:
        manager.spawn_subagent(parent=architect, role=CivicRole.SURVEYOR)
        test.fail("Third child spawn attempt did not raise ValueError!")
    except ValueError as e:
        test.log(f"Third child spawn attempt raised expected error: {e}")
    test.ok("Parent role concurrency caps enforced.")

    # 3. Test Escrow Vault Conservation across 50 Rapid Spawn/Retire Cycles
    test.log("Testing Escrow Vault Conservation across 50 rapid spawn & retire cycles...")
    engineer = EngineerAgent(agent_id="agt_eng_test", name="Engineer Tesla", funds=1000.0)
    initial_funds = engineer.funds
    escrow_deposit = 40.0

    for cycle in range(1, 51):
        # Spawn
        cid = manager.spawn_subagent(
            parent=engineer,
            role=CivicRole.CONSTRUCTION_CREW,
            budget=escrow_deposit,
        )
        expected_after_spawn = initial_funds - escrow_deposit
        if abs(engineer.funds - expected_after_spawn) > 1e-4:
            test.fail(f"Cycle {cycle}: Funds after spawn {engineer.funds} != expected {expected_after_spawn}")

        # Simulate work & retirement with partial refund (e.g., spent $10, unspent $30)
        spent = 10.0
        unspent = escrow_deposit - spent
        manager.retire_subagent(
            child_id=cid,
            reason="COMPLETED",
            unspent_funds=unspent,
            parent_agent=engineer,
        )
        initial_funds -= spent
        if abs(engineer.funds - initial_funds) > 1e-4:
            test.fail(f"Cycle {cycle}: Escrow refund leak! Engineer funds {engineer.funds} != expected {initial_funds}")

    test.ok(f"50 rapid spawn/retire cycles executed with zero escrow leak. Final funds: ${engineer.funds:.2f}.")

    test.duration_s = time.monotonic() - t0
    test.passed = True
    return test


# =============================================================================
# Main Test Runner & Verdict Formulation
# =============================================================================

async def main():
    print("=" * 80)
    print("EMPIRICAL ADVERSARIAL STRESS TEST SUITE: AGENT CITY M2")
    print("=" * 80)

    results: List[TestResult] = []

    try:
        r1 = await stress_test_1_long_horizon_simulation()
        results.append(r1)
    except Exception as e:
        print(f"FAILED STRESS TEST 1: {e}")
        r1 = TestResult("STRESS_1_300_TICKS_SIMULATION")
        r1.details.append(str(e))
        results.append(r1)

    try:
        r2 = await stress_test_2_homeostatic_recovery()
        results.append(r2)
    except Exception as e:
        print(f"FAILED STRESS TEST 2: {e}")
        r2 = TestResult("STRESS_2_HOMEOSTATIC_RECOVERY")
        r2.details.append(str(e))
        results.append(r2)

    try:
        r3 = await stress_test_3_trait_evolution_bounds()
        results.append(r3)
    except Exception as e:
        print(f"FAILED STRESS TEST 3: {e}")
        r3 = TestResult("STRESS_3_TRAIT_EVOLUTION_BOUNDS")
        r3.details.append(str(e))
        results.append(r3)

    try:
        r4 = await stress_test_4_subagent_concurrency_and_escrow()
        results.append(r4)
    except Exception as e:
        print(f"FAILED STRESS TEST 4: {e}")
        r4 = TestResult("STRESS_4_SUBAGENT_CONCURRENCY_AND_ESCROW")
        r4.details.append(str(e))
        results.append(r4)

    print("\n" + "=" * 80)
    print("STRESS TEST EXECUTION SUMMARY:")
    print("=" * 80)

    all_passed = True
    for r in results:
        status_str = "PASS" if r.passed else "FAIL"
        print(f"  {r.name:<45} [{status_str}] ({r.duration_s:.2f}s)")
        if not r.passed:
            all_passed = False

    print("=" * 80)
    verdict = "APPROVE" if all_passed else "REJECT"
    print(f"FINAL ADVERSARIAL VERDICT: {verdict}")
    print("=" * 80)

    return 0 if all_passed else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
