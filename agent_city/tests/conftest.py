"""Pytest configuration and shared fixtures for the agent_city test suite.

Supports all 4 testing tiers:
- Tier 1: Unit & Component Isolation fixtures
- Tier 2: Boundary and edge case configurations
- Tier 3: Cross-component integration fixtures
- Tier 4: Multi-agent E2E continuous simulation fixtures
"""

from __future__ import annotations

import asyncio
import os
import tempfile
import uuid
from typing import Any, Callable, Dict, List, Optional, Tuple

import pytest

from agent_city.config import (
    DEFAULT_CONFIG,
    MessageType,
    ProposalStatus,
    SimulationConfig,
    SimulationState,
    VoteChoice,
    ZoneType,
)
from agent_city.engine.economy import EconomySystem, ResourceLedger, Transaction
from agent_city.engine.grid import CityGrid, Parcel
from agent_city.engine.message_bus import AgentMessage, CivicProposal, MessageBus
from agent_city.engine.simulation import SimulationCoordinator


# =============================================================================
# Core Simulation Engine Fixtures
# =============================================================================

@pytest.fixture
def config() -> SimulationConfig:
    """Standard fast test configuration with a 16x16 grid."""
    return SimulationConfig(
        grid_width=16,
        grid_height=16,
        default_tps=10.0,
        min_tps=0.5,
        max_tps=25.0,
        ticks_per_epoch=20,
        initial_treasury_funds=5000.0,
        initial_treasury_energy=1000.0,
        initial_treasury_materials=500.0,
        default_sales_tax_rate=0.05,
        property_tax_per_building=10.0,
        zoning_permit_cost=50.0,
        default_agent_funds=150.0,
        default_agent_energy=100.0,
        default_agent_materials=20.0,
        energy_burn_idle=0.2,
        energy_burn_move=0.5,
        energy_burn_work=1.0,
        energy_regen_residential=2.5,
    )


@pytest.fixture
def large_config() -> SimulationConfig:
    """Full-size 32x32 configuration matching production defaults."""
    return SimulationConfig(
        grid_width=32,
        grid_height=32,
        default_tps=5.0,
        ticks_per_epoch=100,
    )


@pytest.fixture
def grid(config: SimulationConfig) -> CityGrid:
    """Fresh, clean 16x16 spatial grid with default terrain costs."""
    return CityGrid(
        width=config.grid_width,
        height=config.grid_height,
        terrain_costs=config.terrain_costs,
    )


@pytest.fixture
def economy(config: SimulationConfig) -> EconomySystem:
    """Fresh economy system with initial treasury reserves."""
    return EconomySystem(config=config)


@pytest.fixture
def message_bus() -> MessageBus:
    """Fresh in-memory message bus with default topic channels."""
    return MessageBus()


@pytest.fixture
def coordinator(config: SimulationConfig) -> SimulationCoordinator:
    """Fully initialized simulation coordinator with wired subsystems."""
    return SimulationCoordinator(config=config)


# =============================================================================
# Mock & Contract Agent Fixtures (Progressive Testability)
# =============================================================================

class MockAgent:
    """
    Contract-compliant mock agent implementing the BaseAgent interface.
    Allows testing engine, decision loop, and E2E simulation progressively
    both before and after concrete agent modules are integrated.
    """

    def __init__(
        self,
        agent_id: str,
        role: str = "CITIZEN",
        initial_pos: Tuple[int, int] = (0, 0),
        deliberate_callback: Optional[Callable[["MockAgent"], Optional[Dict[str, Any]]]] = None,
        is_subagent: bool = False,
        parent_id: Optional[str] = None,
    ):
        self.id: str = agent_id
        self.agent_id: str = agent_id
        self.role: str = role
        self.state: str = "IDLE"
        self.x: int = initial_pos[0]
        self.y: int = initial_pos[1]
        self.is_subagent: bool = is_subagent
        self.parent_id: Optional[str] = parent_id
        self.child_ids: List[str] = []
        self.inbox: List[AgentMessage] = []
        self.last_perceived_context: Optional[Dict[str, Any]] = None
        self.deliberate_callback: Optional[Callable[["MockAgent"], Optional[Dict[str, Any]]]] = deliberate_callback
        self.epoch_notifications: List[int] = []
        self.action_history: List[Dict[str, Any]] = []

    def receive_messages(self, messages: List[AgentMessage]) -> None:
        """Receive delivered messages from coordinator message bus."""
        self.inbox.extend(messages)

    def perceive(self, context: Dict[str, Any]) -> None:
        """Perceive environmental context at start of tick."""
        self.last_perceived_context = context
        self.state = "PERCEIVING"

    def deliberate(self) -> Optional[Dict[str, Any]]:
        """Formulate next action. Uses callback if provided, else returns IDLE."""
        self.state = "DELIBERATING"
        if self.deliberate_callback:
            action = self.deliberate_callback(self)
        else:
            action = {"type": "IDLE"}
        if action:
            self.action_history.append(action)
            act_type = action.get("type", "IDLE")
            if act_type == "MOVE":
                self.state = "MOVING"
            elif act_type in ("BUILD", "CONSTRUCT"):
                self.state = "EXECUTING"
            elif act_type in ("SPEAK", "BROADCAST"):
                self.state = "COMMUNICATING"
            elif act_type == "REST":
                self.state = "RESTING"
            else:
                self.state = "IDLE"
        return action

    def on_epoch(self, epoch: int) -> None:
        """Handle epoch transition notification."""
        self.epoch_notifications.append(epoch)


@pytest.fixture
def mock_agent_factory() -> Callable[..., MockAgent]:
    """Factory fixture to spawn customizable mock agents."""
    def _create(
        agent_id: Optional[str] = None,
        role: str = "CITIZEN",
        pos: Tuple[int, int] = (0, 0),
        callback: Optional[Callable[[MockAgent], Optional[Dict[str, Any]]]] = None,
        is_subagent: bool = False,
        parent_id: Optional[str] = None,
    ) -> MockAgent:
        uid = agent_id or f"mock_{role.lower()}_{uuid.uuid4().hex[:6]}"
        return MockAgent(
            agent_id=uid,
            role=role,
            initial_pos=pos,
            deliberate_callback=callback,
            is_subagent=is_subagent,
            parent_id=parent_id,
        )
    return _create


@pytest.fixture
def eight_civic_agents(mock_agent_factory: Callable[..., MockAgent]) -> List[MockAgent]:
    """
    Set of 8 distinct civic agents fulfilling the project acceptance criteria:
    Mayor, Architect, Engineer, Merchant, Builder, Scholar, Observer, Citizen.
    Configured with realistic behaviors (moving, proposing, building, trading, resting).
    """
    agents: List[MockAgent] = []

    # 1. Mayor (Spiritual leader, issues referendums and collects taxes)
    def mayor_deliberate(agent: MockAgent) -> Dict[str, Any]:
        tick = agent.last_perceived_context.get("tick", 0) if agent.last_perceived_context else 0
        if tick == 2:
            return {
                "type": "PROPOSE",
                "payload": {
                    "title": "Establish City Park",
                    "action_type": "REZONE",
                    "action_payload": {"x": 5, "y": 5, "zone": "PARK"},
                    "quorum": 3,
                },
            }
        elif tick == 4:
            return {
                "type": "SPEAK",
                "payload": {"content": "Civic prosperity is on the rise!", "topic": "governance"},
            }
        return {"type": "REST"}

    # 2. Architect (Plans and rezones parcels)
    def architect_deliberate(agent: MockAgent) -> Dict[str, Any]:
        tick = agent.last_perceived_context.get("tick", 0) if agent.last_perceived_context else 0
        if tick == 1:
            return {
                "type": "REZONE",
                "target": (6, 6),
                "payload": {"zone": "COMMERCIAL"},
            }
        return {"type": "MOVE", "target": (agent.x + 1 if agent.x < 14 else 2, agent.y)}

    # 3. Engineer (Constructs infrastructure & public works)
    def engineer_deliberate(agent: MockAgent) -> Dict[str, Any]:
        tick = agent.last_perceived_context.get("tick", 0) if agent.last_perceived_context else 0
        if tick % 5 == 1:
            return {
                "type": "BUILD",
                "target": (agent.x, agent.y),
                "payload": {
                    "building_id": f"infra_{tick}",
                    "building_type": "INDUSTRIAL",
                    "materials_cost": 5.0,
                },
            }
        return {"type": "MOVE", "target": (agent.x, agent.y + 1 if agent.y < 14 else 2)}

    # 4. Merchant (Trades commodities and pays sales taxes)
    def merchant_deliberate(agent: MockAgent) -> Dict[str, Any]:
        tick = agent.last_perceived_context.get("tick", 0) if agent.last_perceived_context else 0
        if tick % 3 == 0:
            return {
                "type": "TRADE",
                "payload": {
                    "recipient_id": "agent_engineer_1",
                    "amount": 20.0,
                    "resource": "funds",
                    "description": "Purchased refined construction parts",
                },
            }
        return {"type": "SPEAK", "payload": {"content": "Fresh goods in the market!", "topic": "trade"}}

    # 5. Builder (Erects residential housing)
    def builder_deliberate(agent: MockAgent) -> Dict[str, Any]:
        tick = agent.last_perceived_context.get("tick", 0) if agent.last_perceived_context else 0
        if tick == 3:
            return {
                "type": "BUILD",
                "target": (agent.x, agent.y),
                "payload": {
                    "building_id": "housing_block_1",
                    "building_type": "RESIDENTIAL",
                    "materials_cost": 8.0,
                },
            }
        return {"type": "REST"}

    # 6. Scholar (Votes on proposals and researches)
    def scholar_deliberate(agent: MockAgent) -> Dict[str, Any]:
        # If there's an active proposal in inbox, vote AYE
        for msg in agent.inbox:
            if msg.type == MessageType.PROPOSAL and "proposal_id" in msg.payload:
                return {
                    "type": "VOTE",
                    "payload": {
                        "proposal_id": msg.payload["proposal_id"],
                        "choice": "AYE",
                    },
                }
        return {"type": "SPEAK", "payload": {"content": "Studying urban growth dynamics.", "topic": "research"}}

    # 7. Observer (Monitors census, wanders the grid)
    def observer_deliberate(agent: MockAgent) -> Dict[str, Any]:
        # Walk diagonal zig-zag
        nx = (agent.x + 1) % 15
        ny = (agent.y + 1) % 15
        return {"type": "MOVE", "target": (nx, ny)}

    # 8. Citizen (Consumes energy, rests at home, votes)
    def citizen_deliberate(agent: MockAgent) -> Dict[str, Any]:
        for msg in agent.inbox:
            if msg.type == MessageType.PROPOSAL and "proposal_id" in msg.payload:
                return {
                    "type": "VOTE",
                    "payload": {
                        "proposal_id": msg.payload["proposal_id"],
                        "choice": "AYE",
                    },
                }
        return {"type": "REST"}

    agents.append(mock_agent_factory("agent_mayor_1", "MAYOR", (2, 2), mayor_deliberate))
    agents.append(mock_agent_factory("agent_architect_1", "ARCHITECT", (4, 4), architect_deliberate))
    agents.append(mock_agent_factory("agent_engineer_1", "ENGINEER", (6, 6), engineer_deliberate))
    agents.append(mock_agent_factory("agent_merchant_1", "MERCHANT", (8, 8), merchant_deliberate))
    agents.append(mock_agent_factory("agent_builder_1", "BUILDER", (10, 10), builder_deliberate))
    agents.append(mock_agent_factory("agent_scholar_1", "SCHOLAR", (12, 12), scholar_deliberate))
    agents.append(mock_agent_factory("agent_observer_1", "OBSERVER", (1, 14), observer_deliberate))
    agents.append(mock_agent_factory("agent_citizen_1", "CITIZEN", (14, 1), citizen_deliberate))

    return agents


# =============================================================================
# Persistence & Temporary Files Fixtures
# =============================================================================

@pytest.fixture
def temp_db_file():
    """Create a temporary SQLite database file path and clean up after test."""
    fd, path = tempfile.mkstemp(suffix=".db", prefix="test_city_")
    os.close(fd)
    yield path
    if os.path.exists(path):
        try:
            os.remove(path)
        except OSError:
            pass


@pytest.fixture
def temp_snapshot_file():
    """Create a temporary JSON snapshot file path and clean up after test."""
    fd, path = tempfile.mkstemp(suffix=".json", prefix="test_snapshot_")
    os.close(fd)
    yield path
    if os.path.exists(path):
        try:
            os.remove(path)
        except OSError:
            pass
