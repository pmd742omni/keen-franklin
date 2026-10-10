"""Tier 1-3 Tests for Autonomous Agents:
- BaseAgent Model & Pydantic Validation
- 8-State Finite State Machine (FSM) Transitions
- 4-Tier Goal Hierarchy (Homeostasis > Civic > Socio-Economic > Self-Actualization)
- Multi-Criteria Utility Evaluation Engine
- 6 Civic Roles (Mayor, Architect, Engineer, Merchant, Scholar, Observer)
- Generative Evolution & 7-D Trait Vectors
"""

from __future__ import annotations

import math
import pytest

from agent_city.config import DEFAULT_CONFIG, SimulationConfig, ZoneType

# Conditional imports for Milestone 2 implementation
try:
    from agent_city.agents.base import (
        AgentMemory,
        AgentState,
        BaseAgent,
        CivicRole,
        ResourceType,
        TraitVector,
    )
    from agent_city.agents.decision import evaluate_utility, rank_actions
    from agent_city.agents.evolution import (
        calculate_fitness,
        evolve_traits,
        mutate_traits,
    )
    from agent_city.agents.roles import (
        ArchitectAgent,
        EngineerAgent,
        MayorAgent,
        MerchantAgent,
        ObserverAgent,
        ScholarAgent,
    )
    AGENTS_AVAILABLE = True
except ImportError:
    AGENTS_AVAILABLE = False


# =============================================================================
# Contract Model Definitions (Fallback / Spec Verification)
# =============================================================================

class SpecTraitVector:
    """Trait genome mathematical specification [0.0, 1.0]."""
    def __init__(self, **kwargs):
        self.diligence = kwargs.get("diligence", 0.5)
        self.innovation = kwargs.get("innovation", 0.5)
        self.sociability = kwargs.get("sociability", 0.5)
        self.thriftiness = kwargs.get("thriftiness", 0.5)
        self.altruism = kwargs.get("altruism", 0.5)
        self.adaptability = kwargs.get("adaptability", 0.5)
        self.risk_tolerance = kwargs.get("risk_tolerance", 0.5)

    def as_vector(self):
        return [
            self.diligence,
            self.innovation,
            self.sociability,
            self.thriftiness,
            self.altruism,
            self.adaptability,
            self.risk_tolerance,
        ]

    def cosine_similarity(self, other_vector):
        v1 = self.as_vector()
        v2 = other_vector
        dot = sum(a * b for a, b in zip(v1, v2))
        norm1 = math.sqrt(sum(a * a for a in v1))
        norm2 = math.sqrt(sum(b * b for b in v2))
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot / (norm1 * norm2)


def spec_utility_calc(
    action_type: str,
    energy: float,
    max_energy: float,
    role: str,
    traits: SpecTraitVector,
    cost_funds: float = 0.0,
    available_funds: float = 100.0,
    congestion: float = 0.0,
) -> float:
    """
    Mathematical formulation of utility from survey_report_2 §2.5:
    U(a) = w_need * N(a) + w_role * R(a) + w_trait * T(a) + w_feas * F(a) - P_risk(a)
    """
    # 1. Need Urgency N(a)
    if action_type == "REST":
        need = 1.0 - (energy / max_energy) ** 2
    else:
        need = energy / max_energy

    # 2. Role Alignment R(a)
    role_weights = {
        ("MAYOR", "PROPOSE"): 1.0,
        ("MAYOR", "REZONE"): 0.9,
        ("ARCHITECT", "REZONE"): 1.0,
        ("ARCHITECT", "BUILD"): 0.8,
        ("ENGINEER", "BUILD"): 1.0,
        ("MERCHANT", "TRADE"): 1.0,
        ("SCHOLAR", "RESEARCH"): 1.0,
        ("OBSERVER", "AUDIT"): 1.0,
    }
    role_align = role_weights.get((role, action_type), 0.5)

    # 3. Trait affinity T(a)
    # Action profile vectors: [diligence, innovation, sociability, thrift, altruism, adapt, risk]
    action_profiles = {
        "REST": [0.3, 0.1, 0.2, 0.8, 0.5, 0.5, 0.1],
        "TRADE": [0.8, 0.6, 0.8, 0.8, 0.3, 0.8, 0.7],
        "BUILD": [0.9, 0.5, 0.4, 0.6, 0.7, 0.5, 0.4],
        "PROPOSE": [0.8, 0.7, 0.9, 0.5, 0.8, 0.6, 0.4],
    }
    profile = action_profiles.get(action_type, [0.5] * 7)
    trait_affinity = traits.cosine_similarity(profile)

    # 4. Feasibility F(a)
    feasibility = 1.0 if cost_funds <= available_funds else 0.0

    # 5. Risk Penalty P_risk(a)
    risk_penalty = (1.0 - traits.risk_tolerance) * congestion

    # Utility combination
    u = 0.35 * need + 0.30 * role_align + 0.20 * trait_affinity + 0.15 * feasibility - risk_penalty
    return max(0.0, min(1.0, u))


# =============================================================================
# Unit Tests for Agent Logic & Contracts
# =============================================================================

class TestAgentMathematicalContracts:
    """Verifies mathematical specifications of the 4-tier goal hierarchy and utility formulas."""

    def test_homeostasis_energy_urgency_overrides_civic_goals(self):
        """Tier 1: When energy < 15, REST action urgency dominates all civic activities."""
        traits = SpecTraitVector()
        max_energy = 100.0

        # Normal energy (80.0): BUILD utility is high, REST utility is low
        u_build_high = spec_utility_calc("BUILD", 80.0, max_energy, "ENGINEER", traits)
        u_rest_low = spec_utility_calc("REST", 80.0, max_energy, "ENGINEER", traits)
        assert u_build_high > u_rest_low

        # Exhausted energy (10.0 < 15.0 threshold): REST urgency shoots to near 1.0, BUILD collapses
        u_build_exhausted = spec_utility_calc("BUILD", 10.0, max_energy, "ENGINEER", traits)
        u_rest_exhausted = spec_utility_calc("REST", 10.0, max_energy, "ENGINEER", traits)
        assert u_rest_exhausted > u_build_exhausted
        assert u_rest_exhausted > 0.65

    def test_trait_affinity_cosine_similarity(self):
        """Tier 1: Trait vector cosine similarity calculation correctly discriminates actions."""
        # Highly sociable & diligent merchant
        merchant_traits = SpecTraitVector(sociability=0.9, diligence=0.9, thriftiness=0.8, altruism=0.2)
        # Cosine similarity with TRADE profile should be higher than with REST
        sim_trade = merchant_traits.cosine_similarity([0.8, 0.6, 0.8, 0.8, 0.3, 0.8, 0.7])
        sim_rest = merchant_traits.cosine_similarity([0.3, 0.1, 0.2, 0.8, 0.5, 0.5, 0.1])
        assert sim_trade > sim_rest

    def test_resource_feasibility_boundary_cases(self):
        """Tier 2: Infeasible actions (insufficient funds) receive feasibility zero."""
        traits = SpecTraitVector()
        # Sufficient funds
        u_feasible = spec_utility_calc("BUILD", 90.0, 100.0, "ENGINEER", traits, cost_funds=50.0, available_funds=100.0)
        # Insufficient funds
        u_infeasible = spec_utility_calc("BUILD", 90.0, 100.0, "ENGINEER", traits, cost_funds=150.0, available_funds=100.0)
        assert u_feasible > u_infeasible

    def test_congestion_risk_penalty(self):
        """Tier 2: High congestion penalizes risk-averse agents more heavily than risk-tolerant ones."""
        cautious_traits = SpecTraitVector(risk_tolerance=0.1)
        reckless_traits = SpecTraitVector(risk_tolerance=0.9)

        u_cautious = spec_utility_calc("BUILD", 80.0, 100.0, "ENGINEER", cautious_traits, congestion=0.5)
        u_reckless = spec_utility_calc("BUILD", 80.0, 100.0, "ENGINEER", reckless_traits, congestion=0.5)

        assert u_reckless > u_cautious


# =============================================================================
# Concrete BaseAgent and 6 Civic Roles Tests (Unskipped when M2 is present)
# =============================================================================

@pytest.mark.skipif(not AGENTS_AVAILABLE, reason="Milestone 2 (agent_city.agents) not yet implemented")
class TestConcreteBaseAgentAndRoles:
    """Tests executing directly against concrete BaseAgent, FSM, and 6 Civic Roles."""

    def test_base_agent_model_instantiation(self):
        """Tier 1: Verify BaseAgent initialization with default traits and vitals."""
        agent = BaseAgent(
            agent_id="test_agt_1",
            name="Archimedes",
            role=CivicRole.SCHOLAR,
            position=(5, 5),
            energy=100.0,
            funds=200.0,
        )
        assert agent.agent_id == "test_agt_1"
        assert agent.state == AgentState.IDLE
        assert agent.position == (5, 5)
        assert agent.energy == 100.0
        assert agent.funds == 200.0
        assert agent.traits.diligence >= 0.0 and agent.traits.diligence <= 1.0

    def test_fsm_state_transitions(self):
        """Tier 1: Test valid FSM state transitions."""
        agent = BaseAgent(
            agent_id="fsm_agt",
            name="Vitruvius",
            role=CivicRole.ARCHITECT,
            position=(0, 0),
        )
        # IDLE -> PERCEIVING
        agent.state = AgentState.PERCEIVING
        assert agent.state == AgentState.PERCEIVING

        # PERCEIVING -> DELIBERATING
        agent.state = AgentState.DELIBERATING
        assert agent.state == AgentState.DELIBERATING

        # DELIBERATING -> MOVING
        agent.state = AgentState.MOVING
        assert agent.state == AgentState.MOVING

        # MOVING -> EXECUTING
        agent.state = AgentState.EXECUTING
        assert agent.state == AgentState.EXECUTING

        # EXECUTING -> RESTING
        agent.state = AgentState.RESTING
        assert agent.state == AgentState.RESTING

        # RESTING -> IDLE
        agent.state = AgentState.IDLE
        assert agent.state == AgentState.IDLE

        # Any -> RETIRED
        agent.state = AgentState.RETIRED
        assert agent.state == AgentState.RETIRED

    def test_six_civic_roles_defaults(self):
        """Tier 1: Verify all 6 Civic Roles possess appropriate agendas and starting traits."""
        mayor = MayorAgent(agent_id="m1", name="Augustus", position=(0, 0))
        assert mayor.role == CivicRole.MAYOR
        assert mayor.traits.sociability >= 0.7  # High sociability
        assert mayor.traits.altruism >= 0.6

        architect = ArchitectAgent(agent_id="a1", name="Brunelleschi", position=(1, 1))
        assert architect.role == CivicRole.ARCHITECT
        assert architect.traits.innovation >= 0.7

        engineer = EngineerAgent(agent_id="e1", name="Tesla", position=(2, 2))
        assert engineer.role == CivicRole.ENGINEER
        assert engineer.traits.diligence >= 0.7

        merchant = MerchantAgent(agent_id="mer1", name="Medici", position=(3, 3))
        assert merchant.role == CivicRole.MERCHANT
        assert merchant.traits.thriftiness >= 0.7

        scholar = ScholarAgent(agent_id="s1", name="Hypatia", position=(4, 4))
        assert scholar.role == CivicRole.SCHOLAR
        assert scholar.traits.innovation >= 0.8

        observer = ObserverAgent(agent_id="o1", name="Herodotus", position=(5, 5))
        assert observer.role == CivicRole.OBSERVER
        assert observer.traits.diligence >= 0.8

    def test_trait_mutation_and_evolution(self):
        """Tier 1: Trait mutation remains clamped within [0.0, 1.0]."""
        traits = TraitVector(diligence=0.98, risk_tolerance=0.02)
        mutated = mutate_traits(traits, mutation_rate=0.05)
        assert 0.0 <= mutated.diligence <= 1.0
        assert 0.0 <= mutated.risk_tolerance <= 1.0

    def test_homeostasis_energy_override_in_agent_deliberation(self):
        """Tier 1: When energy < 15, agent deliberation forces REST action and RESTING state."""
        agent = EngineerAgent(agent_id="e_tired", name="Tired Engineer", position=(2, 2))
        agent.energy = 10.0  # Under 15.0 threshold
        action = agent.deliberate()
        assert action["type"] == "REST"
        assert agent.state == AgentState.RESTING

    def test_decision_engine_goal_tier_hierarchy(self):
        """Tier 1: Verify DecisionEngine evaluates 4-tier goal hierarchy properly."""
        from agent_city.agents.decision import DecisionEngine
        from agent_city.agents.base import GoalTier

        # Tier 1: Homeostasis
        exhausted = MayorAgent(agent_id="m_low", name="Low Energy Mayor", position=(0, 0))
        exhausted.energy = 8.0
        goal_1 = DecisionEngine.determine_goal(exhausted)
        assert goal_1.tier == GoalTier.HOMEOSTASIS
        assert goal_1.target_type == "REST"

        # Tier 2: Civic Role Mandate
        fit_architect = ArchitectAgent(agent_id="a_fit", name="Active Architect", position=(0, 0))
        fit_architect.energy = 90.0
        goal_2 = DecisionEngine.determine_goal(fit_architect)
        assert goal_2.tier == GoalTier.CIVIC_MANDATE
        assert goal_2.target_type == "REZONE"

    def test_concrete_utility_evaluation_and_ranking(self):
        """Tier 2: evaluate_utility and rank_actions score actions relative to agent traits and role."""
        engineer = EngineerAgent(agent_id="eng_eval", name="Eval Engineer", position=(3, 3))
        engineer.energy = 95.0
        candidate_actions = [
            {"type": "BUILD", "cost_funds": 20.0},
            {"type": "TRADE", "cost_funds": 10.0},
            {"type": "REST"},
        ]
        ranked = rank_actions(engineer, candidate_actions)
        assert len(ranked) == 3
        # BUILD should rank higher than TRADE or REST for well-rested Engineer
        top_action, top_score = ranked[0]
        assert top_action["type"] == "BUILD"
        assert top_score > ranked[1][1]

    def test_six_civic_roles_speech_bubbles(self):
        """Tier 1: Verify all 6 Civic Roles generate contextual speech bubble dialogues."""
        mayor = MayorAgent(agent_id="m_spk", name="Mayor Augustus")
        assert "Treasury reserves" in mayor.get_speech("general")

        architect = ArchitectAgent(agent_id="a_spk", name="Architect Brunelleschi")
        assert "blueprint" in architect.get_speech("general").lower()

        engineer = EngineerAgent(agent_id="e_spk", name="Engineer Tesla")
        assert "foundation pour" in engineer.get_speech("general").lower()

        merchant = MerchantAgent(agent_id="mer_spk", name="Merchant Medici")
        assert "market stall" in merchant.get_speech("general").lower()

        scholar = ScholarAgent(agent_id="s_spk", name="Scholar Hypatia")
        assert "research breakthrough" in scholar.get_speech("general").lower()

        observer = ObserverAgent(agent_id="o_spk", name="Observer Herodotus")
        assert "census update" in observer.get_speech("general").lower()

    def test_generative_evolution_epoch_evaluation(self):
        """Tier 3: GenerativeEvolutionEngine ranks agents, preserves elites, and adapts underperformers."""
        from agent_city.agents.evolution import GenerativeEvolutionEngine

        engine = GenerativeEvolutionEngine(elite_fraction=0.25, mutation_rate=0.1)
        agents = [
            MayorAgent(agent_id="m_evo", name="Mayor", funds=500.0, energy=100.0),
            ArchitectAgent(agent_id="a_evo", name="Architect", funds=400.0, energy=90.0),
            EngineerAgent(agent_id="e_evo", name="Engineer", funds=100.0, energy=50.0),
            MerchantAgent(agent_id="mer_evo", name="Merchant", funds=50.0, energy=30.0),
        ]
        # Simulate productive action memory on Mayor
        agents[0].memory.recent_actions = [{"type": "PROPOSE"}, {"type": "REZONE"}, {"type": "SPEAK"}]
        agents[0].child_ids = ["sub_1", "sub_2"]

        # Run epoch evaluation
        adapted_agents = engine.evaluate_epoch(agents, epoch=1)
        assert len(adapted_agents) == 4
        # At least one underperforming agent should have incremented generation
        generations = [a.generation for a in adapted_agents]
        assert max(generations) > 1

    def test_factory_functions(self):
        """Tier 1: Factory functions instantiate valid agents, subagents, and civic councils."""
        from agent_city.agents import create_agent, create_subagent, create_civic_council

        council = create_civic_council()
        assert len(council) == 6
        roles = {a.role for a in council}
        assert CivicRole.MAYOR in roles
        assert CivicRole.ARCHITECT in roles
        assert CivicRole.ENGINEER in roles
        assert CivicRole.MERCHANT in roles
        assert CivicRole.SCHOLAR in roles
        assert CivicRole.OBSERVER in roles

        sub = create_subagent(parent_id="agt_architect_1", role=CivicRole.SURVEYOR, task="SURVEY_QUADRANT")
        assert sub.parent_id == "agt_architect_1"
        assert sub.is_subagent is True

    @pytest.mark.asyncio
    async def test_concrete_agents_step_in_simulation_coordinator(self, coordinator):
        """Tier 3: Register all 6 concrete civic roles into SimulationCoordinator and step 10 ticks."""
        from agent_city.agents import create_civic_council

        council = create_civic_council()
        for agent in council:
            coordinator.register_agent(
                agent=agent,
                initial_x=agent.x,
                initial_y=agent.y,
                initial_funds=agent.funds,
                initial_energy=agent.energy,
            )

        for _ in range(10):
            delta = await coordinator.step()
            assert delta["type"] == "TICK_DELTA"
            assert len(delta["agents"]) == 6

        assert coordinator.current_tick == 10


