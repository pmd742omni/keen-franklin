"""Generative evolution, multi-objective fitness evaluation, elitism, and trait mutation."""

from __future__ import annotations

import random
from typing import Any, Dict, List, Optional

from agent_city.agents.base import AgentState, BaseAgent, TraitVector


TRAIT_FIELDS = [
    "diligence",
    "innovation",
    "sociability",
    "thriftiness",
    "altruism",
    "adaptability",
    "risk_tolerance",
]


def mutate_traits(
    traits: TraitVector,
    mutation_rate: float = 0.15,
    mutation_scale: float = 0.08,
    breakthrough_rate: float = 0.02,
) -> TraitVector:
    """
    Apply Gaussian stochastic mutation to 7-D continuous traits.
    Clamps all trait values within [0.0, 1.0].
    """
    mutated: Dict[str, float] = {}
    for field in TRAIT_FIELDS:
        val = getattr(traits, field)
        if random.random() < mutation_rate:
            noise = random.gauss(0.0, mutation_scale)
            # Rare breakthrough / radical adaptation
            if random.random() < breakthrough_rate:
                noise += random.choice([-0.3, 0.3])
            val += noise
        mutated[field] = round(max(0.0, min(1.0, float(val))), 4)

    return TraitVector(**mutated)


def evolve_traits(
    parent_a: TraitVector,
    parent_b: TraitVector,
    mutation_rate: float = 0.15,
    mutation_scale: float = 0.08,
) -> TraitVector:
    """Crossover between two parent trait vectors with stochastic mutation."""
    child_dict: Dict[str, float] = {}
    for field in TRAIT_FIELDS:
        val_a = getattr(parent_a, field)
        val_b = getattr(parent_b, field)
        # Random interpolation crossover
        alpha = random.uniform(0.3, 0.7)
        val = alpha * val_a + (1.0 - alpha) * val_b
        if random.random() < mutation_rate:
            val += random.gauss(0.0, mutation_scale)
        child_dict[field] = round(max(0.0, min(1.0, float(val))), 4)

    return TraitVector(**child_dict)


def calculate_fitness(
    agent: BaseAgent,
    context: Optional[Dict[str, Any]] = None,
) -> float:
    """
    Compute multi-objective fitness score F_i across 4 normalized pillars:
    F_i = w_civic * C_civic + w_econ * W_econ + w_energy * E_energy + w_collab * S_collab
    Weights: 0.40 civic, 0.25 economic, 0.15 energy, 0.20 collaboration.
    """
    ctx = context or {}

    # 1. Civic Duty Contribution C_civic
    # Number of executed non-idle actions in memory + historical contributions
    actions = agent.memory.recent_actions
    productive_actions = sum(1 for a in actions if a.get("type") not in ("IDLE", "REST"))
    c_civic = min(1.0, (productive_actions / max(1, len(actions))) * 0.7 + (agent.memory.historical_contributions / 100.0) * 0.3)

    # 2. Economic Solvency W_econ
    target_wealth = 300.0
    w_econ = min(1.0, max(0.0, agent.funds / target_wealth))

    # 3. Energy & Survival Efficiency E_energy
    e_energy = min(1.0, max(0.0, agent.energy / agent.max_energy))

    # 4. Collaborative Impact S_collab
    # Subagents spawned, known agents trust, social votes/messages
    collab_count = len(agent.child_ids) + len(agent.memory.known_agents)
    s_collab = min(1.0, collab_count / 5.0)

    # Combined multi-objective score
    fitness = 0.40 * c_civic + 0.25 * w_econ + 0.15 * e_energy + 0.20 * s_collab
    fitness = round(max(0.0, min(1.0, fitness)), 4)

    agent.fitness_score = fitness
    return fitness


class GenerativeEvolutionEngine:
    """
    Orchestrates epochal generational adaptation, elitism preservation,
    and guided trait centroid adaptation.
    """

    def __init__(
        self,
        mutation_rate: float = 0.15,
        mutation_scale: float = 0.08,
        breakthrough_rate: float = 0.02,
        elite_fraction: float = 0.25,
    ) -> None:
        self.mutation_rate = mutation_rate
        self.mutation_scale = mutation_scale
        self.breakthrough_rate = breakthrough_rate
        self.elite_fraction = elite_fraction

    def evaluate_epoch(
        self,
        agents: List[BaseAgent],
        epoch: int,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[BaseAgent]:
        """
        Execute generational epoch transition:
        1. Evaluate fitness scores for all active primary agents.
        2. Rank and identify top elite exemplars.
        3. Guided adaptation: steer underperforming agents towards exemplar centroid.
        """
        # Filter primary permanent agents (exclude temporary subagents and retired agents)
        primary_agents = [
            a for a in agents
            if not a.is_temporary and a.state != AgentState.RETIRED
        ]
        if not primary_agents:
            return agents

        # 1. Compute fitness for all primary agents
        for agent in primary_agents:
            calculate_fitness(agent, context)

        # 2. Sort descending by fitness
        primary_agents.sort(key=lambda a: a.fitness_score, reverse=True)

        # 3. Preserve elites and compute exemplar centroid
        elite_count = max(1, int(len(primary_agents) * self.elite_fraction))
        elites = primary_agents[:elite_count]
        exemplar_centroid = self._compute_exemplar_centroid(elites)

        # 4. Adapt underperforming cohort towards exemplar centroid
        for agent in primary_agents[elite_count:]:
            agent.traits = self._adapt_towards_exemplar(agent.traits, exemplar_centroid)
            agent.generation += 1

        return agents

    def _compute_exemplar_centroid(self, elites: List[BaseAgent]) -> TraitVector:
        """Calculate mean trait vector across elite performers."""
        avg_traits: Dict[str, float] = {}
        n = max(1, len(elites))
        for field in TRAIT_FIELDS:
            avg_traits[field] = sum(getattr(e.traits, field) for e in elites) / n
        return TraitVector(**avg_traits)

    def _adapt_towards_exemplar(
        self,
        current: TraitVector,
        exemplar: TraitVector,
    ) -> TraitVector:
        """Guide underperforming trait vector 30% towards exemplar with mutation."""
        adapted: Dict[str, float] = {}
        for field in TRAIT_FIELDS:
            curr_val = getattr(current, field)
            ex_val = getattr(exemplar, field)

            # 30% drift towards exemplar centroid
            drift = 0.30 * (ex_val - curr_val)
            noise = (
                random.gauss(0.0, self.mutation_scale)
                if random.random() < self.mutation_rate
                else 0.0
            )
            if random.random() < self.breakthrough_rate:
                noise += random.choice([-0.25, 0.25])

            val = max(0.0, min(1.0, curr_val + drift + noise))
            adapted[field] = round(val, 4)

        return TraitVector(**adapted)

    def breed_traits(
        self,
        parent_a: TraitVector,
        parent_b: TraitVector,
    ) -> TraitVector:
        """Breed two trait genomes for newly spawned civic offspring."""
        return evolve_traits(
            parent_a,
            parent_b,
            mutation_rate=self.mutation_rate,
            mutation_scale=self.mutation_scale,
        )
