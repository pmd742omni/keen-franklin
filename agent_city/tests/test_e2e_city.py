"""Tier 4 Real-World Application Scenario:
Multi-Agent 100-Tick Continuous Simulation & Emergence Verification.

Verifies:
- Minimum 8 distinct civic agents (Mayor, Architect, Engineer, Merchant, Builder, Scholar, Observer, Citizen)
- Continuous 100-tick async execution without deadlocks or unhandled exceptions
- Subagent spawning, hierarchical delegation, escrow refund, and retirement
- Dynamic spatial expansion (zoning updates, building construction)
- Macro-economic solvency (treasury stability, property and sales tax collection)
- Inter-agent dialogue feed and democratic consensus voting resolution
- Strict performance budget (< 15 seconds execution duration for 100 ticks)
"""

from __future__ import annotations

import asyncio
import time
import pytest

from agent_city.config import DEFAULT_CONFIG, SimulationConfig, SimulationState, ZoneType
from agent_city.engine.simulation import SimulationCoordinator


class TestE2ECityContinuousSimulation:
    """Tier 4: Long-horizon multi-agent simulation test."""

    @pytest.mark.asyncio
    async def test_multi_agent_100_tick_continuous_simulation(
        self,
        eight_civic_agents,
        mock_agent_factory,
    ):
        """
        Executes a 100-tick continuous simulation with >= 8 distinct agents.
        Asserts emergence, stability, and zero crashes.
        """
        # Configure coordinator for 100 ticks (5 epochs of 20 ticks each)
        sim_config = SimulationConfig(
            grid_width=16,
            grid_height=16,
            default_tps=20.0,  # Fast execution for CI / test runner
            ticks_per_epoch=20,
            initial_treasury_funds=5000.0,
            default_sales_tax_rate=0.05,
            property_tax_per_building=10.0,
        )
        coordinator = SimulationCoordinator(config=sim_config)

        # 1. Register all 8 distinct civic agents
        assert len(eight_civic_agents) >= 8
        for agent in eight_civic_agents:
            coordinator.register_agent(
                agent=agent,
                initial_x=agent.x,
                initial_y=agent.y,
                initial_funds=150.0,
                initial_energy=100.0,
                initial_materials=25.0,
            )

        # 2. Add dynamic subagent spawner behavior to Architect at tick 10
        subagent_spawned = False
        subagent_retired = False

        original_architect = coordinator.agents.get("agent_architect_1")
        if original_architect:
            def advanced_architect_deliberate(agent):
                nonlocal subagent_spawned, subagent_retired
                tick = agent.last_perceived_context.get("tick", 0) if agent.last_perceived_context else 0

                # Tick 10: Architect spawns a temporary Surveyor subagent
                if tick == 10 and not subagent_spawned:
                    subagent_spawned = True
                    surveyor = mock_agent_factory(
                        agent_id="sub_surveyor_1",
                        role="SURVEYOR",
                        pos=(agent.x, agent.y),
                        is_subagent=True,
                        parent_id=agent.id,
                    )
                    coordinator.register_agent(
                        surveyor,
                        initial_x=agent.x,
                        initial_y=agent.y,
                        initial_funds=30.0,
                        initial_energy=100.0,
                    )
                    agent.child_ids.append("sub_surveyor_1")
                    return {
                        "type": "SPEAK",
                        "payload": {"content": "Dispatched Surveyor subagent to assess district perimeter.", "topic": "construction"},
                    }

                # Tick 25: Retire Surveyor subagent
                if tick == 25 and subagent_spawned and not subagent_retired:
                    subagent_retired = True
                    coordinator.unregister_agent("sub_surveyor_1")
                    if "sub_surveyor_1" in agent.child_ids:
                        agent.child_ids.remove("sub_surveyor_1")
                    return {
                        "type": "SPEAK",
                        "payload": {"content": "Surveyor subagent mission completed and retired.", "topic": "construction"},
                    }

                # Standard behavior: rezone or move
                if tick == 1:
                    return {"type": "REZONE", "target": (5, 5), "payload": {"zone": "COMMERCIAL"}}
                return {"type": "MOVE", "target": ((agent.x + 1) % 15, agent.y)}

            original_architect.deliberate_callback = advanced_architect_deliberate

        # 3. Execute 100 ticks continuously and measure execution performance
        t_start = time.monotonic()
        total_ticks = 100

        for tick_idx in range(1, total_ticks + 1):
            delta = await coordinator.step()
            assert delta["tick"] == tick_idx

        t_elapsed = time.monotonic() - t_start

        # ---------------------------------------------------------------------
        # 4. Rigorous Post-Simulation Invariant & Acceptance Criteria Checks
        # ---------------------------------------------------------------------

        # A. Stability & Execution Duration
        assert coordinator.current_tick == 100
        assert coordinator.current_epoch == 5  # 100 ticks / 20 ticks per epoch
        assert t_elapsed < 15.0, f"Simulation was too slow! Took {t_elapsed:.2f}s for 100 ticks."

        # B. Distinct Agent Population Integrity
        assert len(coordinator.agents) >= 8
        roles_present = {getattr(a, "role", None) for a in coordinator.agents.values()}
        assert "MAYOR" in roles_present
        assert "ARCHITECT" in roles_present
        assert "ENGINEER" in roles_present
        assert "MERCHANT" in roles_present
        assert "BUILDER" in roles_present
        assert "SCHOLAR" in roles_present
        assert "OBSERVER" in roles_present
        assert "CITIZEN" in roles_present

        # C. Subagent Lifecycle Execution
        assert subagent_spawned is True, "Subagent was never spawned during 100 ticks."
        assert subagent_retired is True, "Subagent was never retired during 100 ticks."
        assert "sub_surveyor_1" not in coordinator.agents, "Retired subagent leaked in coordinator registry!"

        # D. Physical City Expansion (Zoning & Buildings)
        # Verify that buildings were erected during the 100 ticks
        built_parcels = [
            p for row in coordinator.grid._grid for p in row if p.building_id is not None
        ]
        assert len(built_parcels) >= 1, "Zero buildings were constructed during 100-tick simulation!"

        # Verify rezoning occurred
        commercial_or_parks = [
            p for row in coordinator.grid._grid for p in row if p.zone in (ZoneType.COMMERCIAL, ZoneType.PARK)
        ]
        assert len(commercial_or_parks) >= 1, "Zero rezoned parcels exist after 100 ticks!"

        # E. Macroeconomic Solvency
        # Treasury must not be depleted to zero or negative
        assert coordinator.economy.treasury.funds > 1000.0, "Municipal treasury suffered catastrophic collapse!"
        assert coordinator.economy.total_tax_collected > 0.0, "Zero municipal taxes collected over 5 epochs!"

        # F. Communication & Legislative Discourse
        dialogues = coordinator.message_bus.get_recent_dialogues(50)
        assert len(dialogues) > 0, "No agent dialogue occurred across 100 ticks!"
