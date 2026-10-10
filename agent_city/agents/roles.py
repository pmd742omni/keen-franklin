"""6 Civic Roles: Mayor, Architect, Engineer, Merchant, Scholar, Observer."""

from __future__ import annotations

import random
from typing import Any, Dict, List, Optional, Tuple

from pydantic import Field

from agent_city.agents.base import AgentState, BaseAgent, CivicRole, TraitVector


class MayorAgent(BaseAgent):
    """
    Executive leader managing municipal solvency, public policy, zoning referendums,
    and civic consensus.
    """
    role: CivicRole = CivicRole.MAYOR
    traits: TraitVector = Field(
        default_factory=lambda: TraitVector(
            diligence=0.8,
            innovation=0.4,
            sociability=0.9,
            thriftiness=0.7,
            altruism=0.8,
            adaptability=0.6,
            risk_tolerance=0.3,
        )
    )

    def get_speech(self, template_key: str = "general", **kwargs: Any) -> str:
        """Render contextual dialogue for speech bubbles."""
        funds = kwargs.get("funds", self.funds)
        sector = kwargs.get("sector", f"({self.x}, {self.y})")
        district = kwargs.get("district", "Central")
        templates = {
            "general": f"Treasury reserves healthy at ${funds:.1f}. Re-zoning Sector {sector} for commercial growth.",
            "referendum": f"Calling council referendum on public park expansion in district {district}.",
            "tax": f"Municipal tax sweep completed. Civic funds allocated for infrastructure.",
        }
        return templates.get(template_key, templates["general"])

    def deliberate(self) -> Optional[Dict[str, Any]]:
        self.state = AgentState.DELIBERATING

        # Homeostasis override
        if self.energy < 15.0:
            action = {"type": "REST"}
            self.state = AgentState.RESTING
            self.current_action = action
            self.memory.record_action(action)
            return action

        tick = self.last_perceived_context.get("tick", 0) if self.last_perceived_context else self.ticks_alive

        # Check for unvoted proposals in inbox
        if self.inbox:
            for msg in self.inbox:
                payload = getattr(msg, "payload", {}) if hasattr(msg, "payload") else msg.get("payload", {})
                p_id = payload.get("proposal_id")
                if p_id:
                    action = {
                        "type": "VOTE",
                        "payload": {"proposal_id": p_id, "choice": "AYE"},
                    }
                    self.state = AgentState.COMMUNICATING
                    self.current_action = action
                    self.memory.record_action(action)
                    return action

        # Sponsor referendum every 25 ticks
        if tick > 0 and tick % 25 == 2:
            action = {
                "type": "PROPOSE",
                "payload": {
                    "title": f"Civic Park Initiative {tick}",
                    "action_type": "REZONE",
                    "action_payload": {"x": (self.x + 2) % 15, "y": (self.y + 2) % 15, "zone": "PARK"},
                    "quorum": 3,
                },
            }
            self.state = AgentState.COMMUNICATING
            self.current_action = action
            self.memory.record_action(action)
            return action

        # Proclaim civic speech periodically
        if tick % 7 == 0:
            action = {
                "type": "SPEAK",
                "payload": {"content": self.get_speech("general"), "topic": "governance"},
            }
            self.state = AgentState.COMMUNICATING
            self.current_action = action
            self.memory.record_action(action)
            return action

        # Move or rest
        if self.energy < 60.0:
            action = {"type": "REST"}
            self.state = AgentState.RESTING
        else:
            action = {"type": "MOVE", "target": ((self.x + 1) % 15, self.y)}
            self.state = AgentState.MOVING

        self.current_action = action
        self.memory.record_action(action)
        return action


class ArchitectAgent(BaseAgent):
    """
    Urban planner creating blueprints, zoning parcels, and dispatching surveyor subagents.
    """
    role: CivicRole = CivicRole.ARCHITECT
    traits: TraitVector = Field(
        default_factory=lambda: TraitVector(
            diligence=0.7,
            innovation=0.9,
            sociability=0.5,
            thriftiness=0.4,
            altruism=0.6,
            adaptability=0.7,
            risk_tolerance=0.6,
        )
    )

    def get_speech(self, template_key: str = "general", **kwargs: Any) -> str:
        x, y = kwargs.get("x", self.x), kwargs.get("y", self.y)
        templates = {
            "general": f"Drafted blueprint for Level 2 Commercial Hub at ({x}, {y}). Seeking construction crew.",
            "surveyor": f"Dispatching Surveyor subagent to assess perimeter topography at ({x}, {y}).",
            "rezone": f"Rezoned parcel ({x}, {y}) to promote balanced structural density.",
        }
        return templates.get(template_key, templates["general"])

    def deliberate(self) -> Optional[Dict[str, Any]]:
        self.state = AgentState.DELIBERATING

        if self.energy < 15.0:
            action = {"type": "REST"}
            self.state = AgentState.RESTING
            self.current_action = action
            self.memory.record_action(action)
            return action

        tick = self.last_perceived_context.get("tick", 0) if self.last_perceived_context else self.ticks_alive

        # Rezone opportunity
        if tick % 15 == 1 and self.funds >= 50.0:
            target = ((self.x + 1) % 15, self.y)
            action = {
                "type": "REZONE",
                "target": target,
                "payload": {"zone": "COMMERCIAL"},
            }
            self.state = AgentState.EXECUTING
            self.current_action = action
            self.memory.record_action(action)
            return action

        # Periodic dialogue
        if tick % 8 == 0:
            action = {
                "type": "SPEAK",
                "payload": {"content": self.get_speech("general"), "topic": "construction"},
            }
            self.state = AgentState.COMMUNICATING
            self.current_action = action
            self.memory.record_action(action)
            return action

        # Movement
        action = {"type": "MOVE", "target": ((self.x + 1) % 15, self.y)}
        self.state = AgentState.MOVING
        self.current_action = action
        self.memory.record_action(action)
        return action


class EngineerAgent(BaseAgent):
    """
    Builder and maintenance specialist constructing buildings, paving roads,
    and repairing structural decay.
    """
    role: CivicRole = CivicRole.ENGINEER
    traits: TraitVector = Field(
        default_factory=lambda: TraitVector(
            diligence=0.9,
            innovation=0.5,
            sociability=0.4,
            thriftiness=0.6,
            altruism=0.7,
            adaptability=0.5,
            risk_tolerance=0.4,
        )
    )

    def get_speech(self, template_key: str = "general", **kwargs: Any) -> str:
        x, y = kwargs.get("x", self.x), kwargs.get("y", self.y)
        templates = {
            "general": f"Beginning foundation pour at ({x}, {y}). Consuming stone and steel.",
            "crew": f"Spawned Construction Crew to accelerate municipal infrastructure at ({x}, {y}).",
            "paving": f"Paving high-speed transit artery on coordinate ({x}, {y}).",
        }
        return templates.get(template_key, templates["general"])

    def deliberate(self) -> Optional[Dict[str, Any]]:
        self.state = AgentState.DELIBERATING

        if self.energy < 15.0:
            action = {"type": "REST"}
            self.state = AgentState.RESTING
            self.current_action = action
            self.memory.record_action(action)
            return action

        tick = self.last_perceived_context.get("tick", 0) if self.last_perceived_context else self.ticks_alive

        # Construct building every 10 ticks if materials available
        if tick % 10 == 3 and self.energy > 30.0:
            action = {
                "type": "BUILD",
                "target": (self.x, self.y),
                "payload": {
                    "building_id": f"build_{self.agent_id}_{tick}",
                    "building_type": "RESIDENTIAL",
                    "materials_cost": 5.0,
                },
            }
            self.state = AgentState.EXECUTING
            self.current_action = action
            self.memory.record_action(action)
            return action

        # Periodic dialogue
        if tick % 9 == 0:
            action = {
                "type": "SPEAK",
                "payload": {"content": self.get_speech("general"), "topic": "infrastructure"},
            }
            self.state = AgentState.COMMUNICATING
            self.current_action = action
            self.memory.record_action(action)
            return action

        # Move along vertical grid lines
        action = {"type": "MOVE", "target": (self.x, (self.y + 1) % 15)}
        self.state = AgentState.MOVING
        self.current_action = action
        self.memory.record_action(action)
        return action


class MerchantAgent(BaseAgent):
    """
    Trader operating market stalls, conducting resource arbitrage, and spawning couriers.
    """
    role: CivicRole = CivicRole.MERCHANT
    traits: TraitVector = Field(
        default_factory=lambda: TraitVector(
            diligence=0.8,
            innovation=0.6,
            sociability=0.8,
            thriftiness=0.8,
            altruism=0.3,
            adaptability=0.8,
            risk_tolerance=0.7,
        )
    )

    def get_speech(self, template_key: str = "general", **kwargs: Any) -> str:
        x, y = kwargs.get("x", self.x), kwargs.get("y", self.y)
        templates = {
            "general": f"Market stall ({x}, {y}) open: Buying Stone at $4, Selling Steel at $18.",
            "courier": f"Dispatched Courier subagent with cargo to client site ({x}, {y}).",
            "trade": f"Commercial transaction settled: liquidity maintained.",
        }
        return templates.get(template_key, templates["general"])

    def deliberate(self) -> Optional[Dict[str, Any]]:
        self.state = AgentState.DELIBERATING

        if self.energy < 15.0:
            action = {"type": "REST"}
            self.state = AgentState.RESTING
            self.current_action = action
            self.memory.record_action(action)
            return action

        tick = self.last_perceived_context.get("tick", 0) if self.last_perceived_context else self.ticks_alive

        # Execute commercial trade periodically
        if tick % 6 == 0 and self.funds >= 15.0:
            action = {
                "type": "TRADE",
                "payload": {
                    "recipient_id": "treasury",
                    "amount": 10.0,
                    "resource": "funds",
                    "description": "Commercial supply purchase",
                },
            }
            self.state = AgentState.EXECUTING
            self.current_action = action
            self.memory.record_action(action)
            return action

        # Market announcement
        if tick % 8 == 2:
            action = {
                "type": "SPEAK",
                "payload": {"content": self.get_speech("general"), "topic": "trade"},
            }
            self.state = AgentState.COMMUNICATING
            self.current_action = action
            self.memory.record_action(action)
            return action

        # Move to commercial district
        action = {"type": "MOVE", "target": ((self.x + 1) % 15, (self.y + 1) % 15)}
        self.state = AgentState.MOVING
        self.current_action = action
        self.memory.record_action(action)
        return action


class ScholarAgent(BaseAgent):
    """
    Researcher unlocking technology tree upgrades, polling sentiment, and voting on proposals.
    """
    role: CivicRole = CivicRole.SCHOLAR
    traits: TraitVector = Field(
        default_factory=lambda: TraitVector(
            diligence=0.8,
            innovation=0.95,
            sociability=0.6,
            thriftiness=0.5,
            altruism=0.8,
            adaptability=0.7,
            risk_tolerance=0.5,
        )
    )

    def get_speech(self, template_key: str = "general", **kwargs: Any) -> str:
        epoch = kwargs.get("epoch", 1)
        templates = {
            "general": "Research breakthrough: 'Reinforced Masonry' complete! Durability +25%.",
            "assistant": "Deploying Research Assistant to poll civic happiness across wards.",
            "archive": f"Archived annals of epoch {epoch} into city records.",
        }
        return templates.get(template_key, templates["general"])

    def deliberate(self) -> Optional[Dict[str, Any]]:
        self.state = AgentState.DELIBERATING

        if self.energy < 15.0:
            action = {"type": "REST"}
            self.state = AgentState.RESTING
            self.current_action = action
            self.memory.record_action(action)
            return action

        # Vote on any active proposal in inbox
        if self.inbox:
            for msg in self.inbox:
                payload = getattr(msg, "payload", {}) if hasattr(msg, "payload") else msg.get("payload", {})
                p_id = payload.get("proposal_id")
                if p_id:
                    action = {
                        "type": "VOTE",
                        "payload": {"proposal_id": p_id, "choice": "AYE"},
                    }
                    self.state = AgentState.COMMUNICATING
                    self.current_action = action
                    self.memory.record_action(action)
                    return action

        tick = self.last_perceived_context.get("tick", 0) if self.last_perceived_context else self.ticks_alive

        # Publish scientific finding
        if tick % 7 == 1:
            action = {
                "type": "SPEAK",
                "payload": {"content": self.get_speech("general"), "topic": "research"},
            }
            self.state = AgentState.COMMUNICATING
            self.current_action = action
            self.memory.record_action(action)
            return action

        # Rest or move
        if self.energy < 70.0:
            action = {"type": "REST"}
            self.state = AgentState.RESTING
        else:
            action = {"type": "MOVE", "target": ((self.x + 1) % 15, self.y)}
            self.state = AgentState.MOVING

        self.current_action = action
        self.memory.record_action(action)
        return action


class ObserverAgent(BaseAgent):
    """
    Impartial auditor conducting censuses, inequality tracking, and bottleneck profiling.
    """
    role: CivicRole = CivicRole.OBSERVER
    traits: TraitVector = Field(
        default_factory=lambda: TraitVector(
            diligence=0.95,
            innovation=0.3,
            sociability=0.5,
            thriftiness=0.9,
            altruism=0.9,
            adaptability=0.6,
            risk_tolerance=0.1,
        )
    )

    def get_speech(self, template_key: str = "general", **kwargs: Any) -> str:
        pop = kwargs.get("pop", 8)
        gini = kwargs.get("gini", 0.32)
        templates = {
            "general": f"Census Update: {pop} active agents. Wealth Gini coefficient at {gini:.2f}.",
            "congestion": "Transit Warning: High pedestrian congestion observed at city crossroads.",
            "audit": "System audit confirmed: zero deadlocks and healthy treasury reserves.",
        }
        return templates.get(template_key, templates["general"])

    def deliberate(self) -> Optional[Dict[str, Any]]:
        self.state = AgentState.DELIBERATING

        if self.energy < 15.0:
            action = {"type": "REST"}
            self.state = AgentState.RESTING
            self.current_action = action
            self.memory.record_action(action)
            return action

        tick = self.last_perceived_context.get("tick", 0) if self.last_perceived_context else self.ticks_alive

        # Census announcement
        if tick % 10 == 0:
            action = {
                "type": "SPEAK",
                "payload": {"content": self.get_speech("general"), "topic": "audit"},
            }
            self.state = AgentState.COMMUNICATING
            self.current_action = action
            self.memory.record_action(action)
            return action

        # Wandering surveillance trajectory
        nx = (self.x + 1) % 15
        ny = (self.y + 1) % 15
        action = {"type": "MOVE", "target": (nx, ny)}
        self.state = AgentState.MOVING
        self.current_action = action
        self.memory.record_action(action)
        return action
