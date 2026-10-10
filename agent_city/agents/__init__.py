"""Agents package exports and civic agent factory functions."""

from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional, Tuple, Union

from agent_city.agents.base import (
    AgentAction,
    AgentGoal,
    AgentMemory,
    AgentState,
    BaseAgent,
    CivicRole,
    GoalTier,
    ResourceType,
    TraitVector,
)
from agent_city.agents.decision import (
    DecisionEngine,
    evaluate_utility,
    rank_actions,
)
from agent_city.agents.evolution import (
    GenerativeEvolutionEngine,
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

__all__ = [
    # Base Models & Enums
    "AgentState",
    "CivicRole",
    "ResourceType",
    "GoalTier",
    "TraitVector",
    "AgentMemory",
    "AgentGoal",
    "AgentAction",
    "BaseAgent",
    # Decision Engine
    "evaluate_utility",
    "rank_actions",
    "DecisionEngine",
    # 6 Core Civic Roles
    "MayorAgent",
    "ArchitectAgent",
    "EngineerAgent",
    "MerchantAgent",
    "ScholarAgent",
    "ObserverAgent",
    # Subagents & Contracts
    "DelegationStatus",
    "DelegationContract",
    "SurveyorAgent",
    "ConstructionCrewAgent",
    "ResearchAssistantAgent",
    "CourierAgent",
    "DistrictSupervisorAgent",
    "SubagentSpawner",
    "SubagentManager",
    # Generative Evolution
    "calculate_fitness",
    "evolve_traits",
    "mutate_traits",
    "GenerativeEvolutionEngine",
    # Factory Functions
    "create_agent",
    "create_subagent",
    "create_civic_council",
]

ROLE_CLASS_MAP = {
    CivicRole.MAYOR: MayorAgent,
    "MAYOR": MayorAgent,
    CivicRole.ARCHITECT: ArchitectAgent,
    "ARCHITECT": ArchitectAgent,
    CivicRole.ENGINEER: EngineerAgent,
    "ENGINEER": EngineerAgent,
    CivicRole.MERCHANT: MerchantAgent,
    "MERCHANT": MerchantAgent,
    CivicRole.SCHOLAR: ScholarAgent,
    "SCHOLAR": ScholarAgent,
    CivicRole.OBSERVER: ObserverAgent,
    "OBSERVER": ObserverAgent,
    CivicRole.SURVEYOR: SurveyorAgent,
    "SURVEYOR": SurveyorAgent,
    CivicRole.CONSTRUCTION_CREW: ConstructionCrewAgent,
    "CONSTRUCTION_CREW": ConstructionCrewAgent,
    CivicRole.RESEARCH_ASSISTANT: ResearchAssistantAgent,
    "RESEARCH_ASSISTANT": ResearchAssistantAgent,
    CivicRole.COURIER: CourierAgent,
    "COURIER": CourierAgent,
    CivicRole.DISTRICT_SUPERVISOR: DistrictSupervisorAgent,
    "DISTRICT_SUPERVISOR": DistrictSupervisorAgent,
}


def create_agent(
    role: Union[CivicRole, str],
    agent_id: Optional[str] = None,
    name: Optional[str] = None,
    position: Tuple[int, int] = (0, 0),
    **kwargs: Any,
) -> BaseAgent:
    """Factory helper to instantiate a fully configured civic agent."""
    role_key = role if isinstance(role, CivicRole) else CivicRole(str(role).upper())
    agent_cls = ROLE_CLASS_MAP.get(role_key, BaseAgent)

    uid = agent_id or f"agt_{str(role_key.value).lower()}_{uuid.uuid4().hex[:6]}"
    agent_name = name or f"{str(role_key.value).capitalize()} {uid[-4:]}"

    return agent_cls(
        agent_id=uid,
        name=agent_name,
        role=role_key,
        position=position,
        **kwargs,
    )


def create_subagent(
    parent_id: str,
    role: Union[CivicRole, str],
    task: str = "",
    target_coords: Optional[Tuple[int, int]] = None,
    budget: Optional[Union[Dict[str, float], float]] = None,
    **kwargs: Any,
) -> BaseAgent:
    """Factory helper to spawn a specialized subagent bound to a parent."""
    spawner = SubagentSpawner()
    return spawner.spawn(
        parent_id=parent_id,
        role=role,
        task=task,
        target_coords=target_coords,
        budget=budget,
        **kwargs,
    )


def create_civic_council() -> List[BaseAgent]:
    """Instantiate the 6 standard civic founding leaders."""
    return [
        MayorAgent(agent_id="agt_mayor_1", name="Mayor Augustus", position=(2, 2)),
        ArchitectAgent(agent_id="agt_architect_1", name="Architect Brunelleschi", position=(4, 4)),
        EngineerAgent(agent_id="agt_engineer_1", name="Engineer Tesla", position=(6, 6)),
        MerchantAgent(agent_id="agt_merchant_1", name="Merchant Medici", position=(8, 8)),
        ScholarAgent(agent_id="agt_scholar_1", name="Scholar Hypatia", position=(10, 10)),
        ObserverAgent(agent_id="agt_observer_1", name="Observer Herodotus", position=(12, 12)),
    ]
