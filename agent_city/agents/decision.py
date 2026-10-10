"""Multi-criteria utility evaluation engine and 4-tier goal hierarchy."""

from __future__ import annotations

import math
import random
from typing import Any, Dict, List, Optional, Tuple, Union

from agent_city.agents.base import (
    AgentAction,
    AgentGoal,
    AgentState,
    BaseAgent,
    CivicRole,
    GoalTier,
    TraitVector,
)


# Action trait affinity profiles [diligence, innovation, sociability, thrift, altruism, adapt, risk]
ACTION_TRAIT_PROFILES: Dict[str, List[float]] = {
    "REST": [0.3, 0.1, 0.2, 0.8, 0.5, 0.5, 0.1],
    "TRADE": [0.8, 0.6, 0.8, 0.8, 0.3, 0.8, 0.7],
    "BUILD": [0.9, 0.5, 0.4, 0.6, 0.7, 0.5, 0.4],
    "PROPOSE": [0.8, 0.7, 0.9, 0.5, 0.8, 0.6, 0.4],
    "REZONE": [0.8, 0.7, 0.7, 0.6, 0.7, 0.6, 0.4],
    "RESEARCH": [0.9, 0.95, 0.6, 0.5, 0.8, 0.7, 0.4],
    "AUDIT": [0.95, 0.4, 0.5, 0.9, 0.9, 0.6, 0.2],
    "MOVE": [0.5, 0.5, 0.5, 0.5, 0.5, 0.6, 0.5],
    "SPEAK": [0.6, 0.6, 0.9, 0.4, 0.7, 0.6, 0.4],
    "VOTE": [0.7, 0.5, 0.8, 0.5, 0.8, 0.6, 0.3],
    "SURVEY": [0.8, 0.8, 0.4, 0.6, 0.6, 0.7, 0.5],
    "REPAIR": [0.9, 0.4, 0.3, 0.7, 0.8, 0.5, 0.3],
}

# Role alignment matrix: (Role, ActionType) -> alignment [0.0, 1.0]
ROLE_ALIGNMENT_WEIGHTS: Dict[Tuple[str, str], float] = {
    ("MAYOR", "PROPOSE"): 1.0,
    ("MAYOR", "REZONE"): 0.9,
    ("MAYOR", "SPEAK"): 0.8,
    ("MAYOR", "VOTE"): 0.8,
    ("ARCHITECT", "REZONE"): 1.0,
    ("ARCHITECT", "BUILD"): 0.8,
    ("ARCHITECT", "SURVEY"): 0.9,
    ("ENGINEER", "BUILD"): 1.0,
    ("ENGINEER", "REPAIR"): 0.9,
    ("ENGINEER", "PAVE"): 0.8,
    ("MERCHANT", "TRADE"): 1.0,
    ("MERCHANT", "COURIER"): 0.9,
    ("SCHOLAR", "RESEARCH"): 1.0,
    ("SCHOLAR", "VOTE"): 0.9,
    ("OBSERVER", "AUDIT"): 1.0,
    ("OBSERVER", "MOVE"): 0.8,
    ("SURVEYOR", "SURVEY"): 1.0,
    ("CONSTRUCTION_CREW", "BUILD"): 1.0,
    ("RESEARCH_ASSISTANT", "RESEARCH"): 1.0,
    ("COURIER", "TRADE"): 1.0,
    ("DISTRICT_SUPERVISOR", "PROPOSE"): 0.9,
}


def evaluate_utility(
    action_type: Optional[str] = None,
    energy: Optional[float] = None,
    max_energy: float = 100.0,
    role: Union[str, CivicRole] = "CITIZEN",
    traits: Optional[Union[TraitVector, Any]] = None,
    cost_funds: float = 0.0,
    available_funds: float = 100.0,
    congestion: float = 0.0,
    *,
    agent: Optional[BaseAgent] = None,
    action: Optional[Union[Dict[str, Any], AgentAction]] = None,
    **kwargs: Any,
) -> float:
    """
    Mathematical formulation of utility U(a):
    U(a) = w_need * N(a) + w_role * R(a) + w_trait * T(a) + w_feas * F(a) - P_risk(a)
    """
    # If agent object is passed, extract attributes
    if agent is not None:
        energy = agent.energy if energy is None else energy
        max_energy = agent.max_energy
        role = agent.role.value if isinstance(agent.role, CivicRole) else str(agent.role)
        traits = agent.traits if traits is None else traits
        available_funds = agent.funds

    if action is not None:
        if isinstance(action, dict):
            action_type = action.get("type", action_type or "IDLE")
            cost_funds = action.get("cost_funds", cost_funds)
        elif hasattr(action, "type"):
            action_type = action.type
            cost_funds = getattr(action, "cost_funds", cost_funds)

    act_str = str(action_type or "IDLE").upper()
    current_energy = 100.0 if energy is None else float(energy)
    role_str = role.value if isinstance(role, CivicRole) else str(role).upper()

    trait_vec = traits if traits is not None else TraitVector()

    # 1. Need Urgency N(a)
    if act_str == "REST":
        need = 1.0 - (current_energy / max_energy) ** 2
    else:
        need = current_energy / max_energy

    # 2. Role Alignment R(a)
    role_align = ROLE_ALIGNMENT_WEIGHTS.get((role_str, act_str), 0.5)

    # 3. Trait Affinity T(a)
    profile = ACTION_TRAIT_PROFILES.get(act_str, [0.5] * 7)
    if hasattr(trait_vec, "cosine_similarity"):
        trait_affinity = trait_vec.cosine_similarity(profile)
    else:
        trait_affinity = 0.5

    # 4. Feasibility F(a)
    feasibility = 1.0 if cost_funds <= available_funds else 0.0

    # 5. Risk Penalty P_risk(a)
    risk_tol = getattr(trait_vec, "risk_tolerance", 0.5)
    risk_penalty = (1.0 - risk_tol) * congestion

    # Utility combination
    u = 0.35 * need + 0.30 * role_align + 0.20 * trait_affinity + 0.15 * feasibility - risk_penalty
    return max(0.0, min(1.0, float(u)))


def rank_actions(
    agent: BaseAgent,
    candidate_actions: List[Union[Dict[str, Any], AgentAction]],
    context: Optional[Dict[str, Any]] = None,
) -> List[Tuple[Any, float]]:
    """Rank candidate actions by utility in descending order."""
    ctx = context or {}
    congestion = float(ctx.get("congestion", 0.0))

    scored: List[Tuple[Any, float]] = []
    for act in candidate_actions:
        score = evaluate_utility(
            agent=agent,
            action=act,
            congestion=congestion,
        )
        scored.append((act, score))

    scored.sort(key=lambda item: item[1], reverse=True)
    return scored


class DecisionEngine:
    """Deliberation coordinator implementing the 4-Tier Goal Hierarchy and action selection."""

    @staticmethod
    def determine_goal(agent: BaseAgent) -> AgentGoal:
        """
        Evaluate 4-tier goal hierarchy:
        - Tier 1: Homeostasis (energy < 15.0 priority override)
        - Tier 2: Civic Role Mandates (zoning, construction, trading, research, audit)
        - Tier 3: Socio-Economic Exchange & Consensus (voting, market exchanges)
        - Tier 4: Self-Actualization & Strategic Expansion (subagent spawning, monuments)
        """
        # Tier 1: Homeostasis override
        if agent.energy < 15.0:
            return AgentGoal(
                tier=GoalTier.HOMEOSTASIS,
                description="Urgent vitality replenishment (Homeostasis override)",
                target_type="REST",
                urgency=1.0 - (agent.energy / agent.max_energy),
            )

        role_str = agent.role.value if isinstance(agent.role, CivicRole) else str(agent.role)

        # Tier 3: Pending referendums in inbox take civic priority if sociable
        if agent.traits.sociability > 0.6 and agent.inbox:
            for msg in agent.inbox:
                msg_type = getattr(msg, "type", "")
                if msg_type in ("PROPOSAL", "proposal") or "proposal_id" in getattr(msg, "payload", {}):
                    return AgentGoal(
                        tier=GoalTier.SOCIO_ECONOMIC,
                        description="Participate in municipal referendum consensus voting",
                        target_type="VOTE",
                        urgency=0.85,
                    )

        # Tier 2: Core civic duty based on role
        if role_str == "MAYOR":
            return AgentGoal(
                tier=GoalTier.CIVIC_MANDATE,
                description="Executive administration and public policy proposals",
                target_type="PROPOSE",
                urgency=0.8,
            )
        elif role_str == "ARCHITECT":
            return AgentGoal(
                tier=GoalTier.CIVIC_MANDATE,
                description="Urban layout optimization and zoning decrees",
                target_type="REZONE",
                urgency=0.8,
            )
        elif role_str == "ENGINEER":
            return AgentGoal(
                tier=GoalTier.CIVIC_MANDATE,
                description="Physical infrastructure construction and structural repair",
                target_type="BUILD",
                urgency=0.8,
            )
        elif role_str == "MERCHANT":
            return AgentGoal(
                tier=GoalTier.CIVIC_MANDATE,
                description="Commodity arbitrage and market liquidity distribution",
                target_type="TRADE",
                urgency=0.8,
            )
        elif role_str == "SCHOLAR":
            return AgentGoal(
                tier=GoalTier.CIVIC_MANDATE,
                description="Technological tree advancement and efficiency research",
                target_type="RESEARCH",
                urgency=0.8,
            )
        elif role_str == "OBSERVER":
            return AgentGoal(
                tier=GoalTier.CIVIC_MANDATE,
                description="Demographic census and inequality auditing",
                target_type="AUDIT",
                urgency=0.8,
            )

        # Tier 4: Self-actualization fallback
        return AgentGoal(
            tier=GoalTier.SELF_ACTUALIZATION,
            description="Civic dialogue and regional observation",
            target_type="SPEAK",
            urgency=0.5,
        )

    @classmethod
    def generate_candidate_actions(
        cls,
        agent: BaseAgent,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Generate candidate actions according to agent's current goal and capabilities."""
        goal = cls.determine_goal(agent)
        candidates: List[Dict[str, Any]] = []

        # Always include REST as an option
        candidates.append({"type": "REST"})

        if goal.tier == GoalTier.HOMEOSTASIS:
            return [{"type": "REST"}]

        # Check for vote actions in inbox
        if agent.inbox:
            for msg in agent.inbox:
                payload = getattr(msg, "payload", {}) if hasattr(msg, "payload") else msg.get("payload", {})
                p_id = payload.get("proposal_id")
                if p_id:
                    candidates.append({
                        "type": "VOTE",
                        "payload": {"proposal_id": p_id, "choice": "AYE"},
                    })

        role_str = agent.role.value if isinstance(agent.role, CivicRole) else str(agent.role)

        if role_str == "MAYOR":
            candidates.append({
                "type": "PROPOSE",
                "payload": {
                    "title": "Establish Municipal Park",
                    "action_type": "REZONE",
                    "action_payload": {"x": (agent.x + 2) % 15, "y": (agent.y + 2) % 15, "zone": "PARK"},
                    "quorum": 3,
                },
            })
            candidates.append({
                "type": "SPEAK",
                "payload": {"content": "Municipal budget healthy. Civic services operating nominally.", "topic": "governance"},
            })

        elif role_str == "ARCHITECT":
            candidates.append({
                "type": "REZONE",
                "target": ((agent.x + 1) % 15, agent.y),
                "payload": {"zone": "COMMERCIAL"},
                "cost_funds": 50.0,
            })
            candidates.append({
                "type": "MOVE",
                "target": ((agent.x + 1) % 15, agent.y),
            })

        elif role_str == "ENGINEER":
            candidates.append({
                "type": "BUILD",
                "target": (agent.x, agent.y),
                "payload": {"building_type": "RESIDENTIAL", "materials_cost": 5.0},
            })
            candidates.append({
                "type": "MOVE",
                "target": (agent.x, (agent.y + 1) % 15),
            })

        elif role_str == "MERCHANT":
            candidates.append({
                "type": "TRADE",
                "payload": {"recipient_id": "treasury", "amount": 10.0, "resource": "funds"},
            })
            candidates.append({
                "type": "SPEAK",
                "payload": {"content": "Market trading open: exchange rates favorable.", "topic": "trade"},
            })

        elif role_str == "SCHOLAR":
            candidates.append({
                "type": "SPEAK",
                "payload": {"content": "Studying civic efficiency algorithms.", "topic": "research"},
            })
            candidates.append({
                "type": "MOVE",
                "target": ((agent.x + 1) % 15, (agent.y + 1) % 15),
            })

        elif role_str == "OBSERVER":
            candidates.append({
                "type": "MOVE",
                "target": ((agent.x + 1) % 15, (agent.y + 1) % 15),
            })
            candidates.append({
                "type": "SPEAK",
                "payload": {"content": "Census audit verified: systemic equilibrium maintained.", "topic": "audit"},
            })

        else:
            candidates.append({
                "type": "MOVE",
                "target": ((agent.x + 1) % 15, agent.y),
            })

        return candidates

    @classmethod
    def select_action(
        cls,
        agent: BaseAgent,
        candidate_actions: Optional[List[Dict[str, Any]]] = None,
        context: Optional[Dict[str, Any]] = None,
        temperature: float = 0.0,
    ) -> Dict[str, Any]:
        """
        Evaluate candidate actions with utility scoring and select best action.
        If temperature > 0.0, uses Boltzmann Softmax exploration.
        """
        actions = candidate_actions or cls.generate_candidate_actions(agent, context)
        if not actions:
            return {"type": "IDLE"}

        scored = rank_actions(agent, actions, context)

        if temperature <= 0.0 or len(scored) == 1:
            return scored[0][0]

        # Boltzmann Softmax exploration
        utilities = [score for _, score in scored]
        exp_u = [math.exp(u / temperature) for u in utilities]
        sum_exp = sum(exp_u)
        probs = [e / sum_exp for e in exp_u]

        r = random.random()
        cumulative = 0.0
        for (action, _), p in zip(scored, probs):
            cumulative += p
            if r <= cumulative:
                return action

        return scored[0][0]
