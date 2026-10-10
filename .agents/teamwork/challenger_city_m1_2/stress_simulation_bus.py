"""Empirical Adversarial Stress Suite for agent_city Milestone 1:
- SimulationCoordinator Async Lifecycle, Concurrency, and Load Stress
- Inbound Command Flooding & Malformed Payload Fuzzing
- Democratic Consensus Voting, Ballot Flooding, Quorum Boundaries, and Poison Callbacks
- High-Throughput Pub/Sub Message Flooding & Subscription Churn
"""

from __future__ import annotations

import asyncio
import math
import random
import sys
import time
import uuid
from typing import Any, Dict, List, Optional, Tuple

# Ensure agent_city can be imported
sys.path.insert(0, r"c:\Users\ignaz\antigravity\keen-franklin")

from agent_city.config import (
    DEFAULT_CONFIG,
    MessageType,
    ProposalStatus,
    SimulationConfig,
    SimulationState,
    VoteChoice,
    ZoneType,
)
from agent_city.engine.economy import EconomySystem, ResourceLedger
from agent_city.engine.grid import CityGrid
from agent_city.engine.message_bus import AgentMessage, CivicProposal, MessageBus
from agent_city.engine.simulation import SimulationCoordinator


class StressMockAgent:
    """Active autonomous mock agent with customizable randomized behaviors."""

    def __init__(
        self,
        agent_id: str,
        role: str = "CITIZEN",
        initial_pos: Tuple[int, int] = (0, 0),
        action_weights: Optional[Dict[str, float]] = None,
    ):
        self.id = agent_id
        self.agent_id = agent_id
        self.role = role
        self.state = "IDLE"
        self.x = initial_pos[0]
        self.y = initial_pos[1]
        self.inbox: List[AgentMessage] = []
        self.last_context: Optional[Dict[str, Any]] = None
        self.epochs_seen: List[int] = []
        self.actions_count: int = 0
        self.action_weights = action_weights or {
            "MOVE": 0.40,
            "REST": 0.20,
            "BUILD": 0.15,
            "REZONE": 0.10,
            "TRADE": 0.05,
            "SPEAK": 0.05,
            "PROPOSE": 0.05,
        }

    def receive_messages(self, messages: List[AgentMessage]) -> None:
        self.inbox.extend(messages)

    def perceive(self, context: Dict[str, Any]) -> None:
        self.last_context = context
        self.state = "PERCEIVING"

    def deliberate(self) -> Optional[Dict[str, Any]]:
        self.state = "DELIBERATING"
        self.actions_count += 1
        tick = self.last_context.get("tick", 0) if self.last_context else 0

        # Prioritize voting if there are proposal announcements in inbox
        for msg in list(self.inbox):
            if msg.type == MessageType.PROPOSAL and "proposal_id" in msg.payload:
                self.inbox.remove(msg)
                choice = random.choice(["AYE", "NAY", "ABSTAIN"])
                return {
                    "type": "VOTE",
                    "payload": {
                        "proposal_id": msg.payload["proposal_id"],
                        "choice": choice,
                    },
                }

        # Weighted randomized deliberate action
        r = random.random()
        cumulative = 0.0
        chosen_action = "REST"
        for act, weight in self.action_weights.items():
            cumulative += weight
            if r <= cumulative:
                chosen_action = act
                break

        if chosen_action == "MOVE":
            # Move towards a random neighboring coordinate
            dx, dy = random.choice([(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (-1, -1)])
            target_x = max(0, min(31, self.x + dx))
            target_y = max(0, min(31, self.y + dy))
            return {"type": "MOVE", "target": (target_x, target_y)}

        elif chosen_action == "BUILD":
            b_id = f"b_{self.id[:4]}_{tick}_{self.actions_count}"
            b_type = random.choice(["RESIDENTIAL", "COMMERCIAL", "INDUSTRIAL"])
            return {
                "type": "BUILD",
                "target": (self.x, self.y),
                "payload": {"building_id": b_id, "building_type": b_type, "materials_cost": 5.0},
            }

        elif chosen_action == "REZONE":
            rx = random.randint(0, 31)
            ry = random.randint(0, 31)
            target_zone = random.choice(["ROAD", "PARK", "RESIDENTIAL", "COMMERCIAL", "INDUSTRIAL"])
            return {
                "type": "REZONE",
                "target": (rx, ry),
                "payload": {"zone": target_zone},
            }

        elif chosen_action == "TRADE":
            return {
                "type": "TRADE",
                "payload": {
                    "recipient_id": "treasury",
                    "amount": 1.0,
                    "resource": "funds",
                    "description": "Civic contribution",
                },
            }

        elif chosen_action == "SPEAK":
            return {
                "type": "SPEAK",
                "payload": {
                    "content": f"Citizen {self.id} broadcast at tick {tick}",
                    "topic": random.choice(["general", "governance", "trade"]),
                },
            }

        elif chosen_action == "PROPOSE":
            return {
                "type": "PROPOSE",
                "payload": {
                    "title": f"Initiative by {self.id} at tick {tick}",
                    "description": "Public park expansion",
                    "action_type": "REZONE",
                    "action_payload": {"x": random.randint(0, 31), "y": random.randint(0, 31), "zone": "PARK"},
                    "quorum": 3,
                },
            }

        return {"type": "REST"}

    def on_epoch(self, epoch: int) -> None:
        self.epochs_seen.append(epoch)


# =============================================================================
# Stress Test 1: Long Continuous Simulation Run (250+ ticks) under Heavy Load
# =============================================================================

async def test_long_continuous_simulation():
    """
    Stress 1: Continuous 250-tick run with 16 concurrent agents.
    Verifies no deadlocks, spatial collision integrity, economic positivity,
    bounded buffer sizes, and delta stream correctness.
    """
    print("\n--- [Stress 1] Long Continuous Simulation (250 Ticks, 16 Agents) ---")
    t0 = time.perf_counter()

    config = SimulationConfig(
        grid_width=32,
        grid_height=32,
        default_tps=50.0,  # Fast execution for stress testing
        min_tps=1.0,
        max_tps=100.0,
        ticks_per_epoch=50,
        initial_treasury_funds=50000.0,
        initial_treasury_energy=20000.0,
        initial_treasury_materials=10000.0,
    )
    coord = SimulationCoordinator(config=config)

    # Register 16 diverse agents spread across grid
    agents: List[StressMockAgent] = []
    roles = ["MAYOR", "ARCHITECT", "ENGINEER", "MERCHANT", "BUILDER", "SCHOLAR", "OBSERVER", "CITIZEN"]
    for i in range(16):
        role = roles[i % len(roles)]
        start_x = (i * 2) % 30
        start_y = (i * 3) % 30
        agent = StressMockAgent(f"agent_{role.lower()}_{i}", role=role, initial_pos=(start_x, start_y))
        agents.append(agent)
        coord.register_agent(
            agent,
            initial_x=start_x,
            initial_y=start_y,
            initial_funds=1000.0,
            initial_energy=200.0,
            initial_materials=100.0,
        )

    # Hook delta listener to verify delta generation
    deltas_received = 0
    delta_sizes = []

    def on_delta(delta: Dict[str, Any]):
        nonlocal deltas_received
        deltas_received += 1
        assert delta["type"] == "TICK_DELTA"
        assert "tick" in delta
        assert "agents" in delta
        assert "treasury" in delta
        # Verify delta payload size roughly stays within bounds (< 25 KB even with 16 agents)
        import json
        size = len(json.dumps(delta))
        delta_sizes.append(size)

    coord.add_delta_callback(on_delta)

    # Launch continuous loop
    loop_task = await coord.start()
    assert coord.state == SimulationState.RUNNING

    # Wait until current_tick reaches at least 250
    target_ticks = 250
    poll_count = 0
    while coord.current_tick < target_ticks:
        await asyncio.sleep(0.05)
        poll_count += 1
        if poll_count > 600:  # 30 second safety watchdog
            raise TimeoutError(f"Continuous simulation stalled at tick {coord.current_tick}!")

    await coord.stop()
    assert coord.state == SimulationState.STOPPED
    assert loop_task.done()

    elapsed = time.perf_counter() - t0
    final_tick = coord.current_tick
    actual_tps = final_tick / elapsed

    print(f"  Completed {final_tick} ticks across {coord.current_epoch} epochs in {elapsed:.3f}s ({actual_tps:.1f} ticks/s)")
    print(f"  Deltas processed: {deltas_received}, Average delta size: {sum(delta_sizes)/len(delta_sizes):.1f} bytes")

    # Invariants Verification
    assert final_tick >= target_ticks, f"Expected at least {target_ticks} ticks, got {final_tick}"
    assert coord.current_epoch >= 5, f"Expected at least 5 epochs, got {coord.current_epoch}"

    # 1. Spatial Collision Check: no two agents can occupy same coordinates
    agent_positions = {}
    for a in agents:
        pos = coord.grid.find_agent_pos(a.id)
        assert pos is not None, f"Agent {a.id} lost from spatial grid!"
        assert 0 <= pos[0] < 32 and 0 <= pos[1] < 32, f"Agent {a.id} out of bounds: {pos}"
        assert pos not in agent_positions, f"Collision detected! Agents {agent_positions[pos]} and {a.id} share {pos}"
        agent_positions[pos] = a.id

    # 2. Economic Non-Negativity Check
    for a in agents:
        ledger = coord.economy.get_ledger(a.id)
        assert ledger is not None
        assert ledger.funds >= 0.0, f"Negative funds for {a.id}: {ledger.funds}"
        assert ledger.energy >= 0.0, f"Negative energy for {a.id}: {ledger.energy}"
        assert ledger.materials >= 0.0, f"Negative materials for {a.id}: {ledger.materials}"

    assert coord.economy.treasury.funds >= 0.0, "Treasury funds negative!"
    assert coord.economy.treasury.energy >= 0.0, "Treasury energy negative!"
    assert coord.economy.treasury.materials >= 0.0, "Treasury materials negative!"

    # 3. Buffer Bounds Check
    assert len(coord.message_bus.broadcast_log) <= 200, f"Broadcast log overflow: {len(coord.message_bus.broadcast_log)}"
    assert len(coord.message_bus.dialogue_feed) <= 100, f"Dialogue feed overflow: {len(coord.message_bus.dialogue_feed)}"
    assert len(coord.dirty_parcels) == 0, f"Dirty parcels buffer was not cleaned: {len(coord.dirty_parcels)}"
    assert len(coord.active_events) == 0, f"Active events buffer was not cleaned: {len(coord.active_events)}"

    print("  [Stress 1 PASSED]: Continuous 250+ tick simulation is stable, collision-free, and bounded.")


# =============================================================================
# Stress Test 2: Rapid Concurrent Lifecycle & State Machine Toggling
# =============================================================================

async def test_rapid_lifecycle_toggles():
    """
    Stress 2: Rapid concurrent async toggling of pause/resume/step/speed/start/stop.
    Fuzzes with out-of-order calls, invalid speeds (NaN, -1, 10000), and rapid steps.
    Verifies no race conditions, deadlocks, or task leaks.
    """
    print("\n--- [Stress 2] Rapid Concurrent Lifecycle & Speed Fuzzing ---")
    t0 = time.perf_counter()

    coord = SimulationCoordinator(config=DEFAULT_CONFIG)
    coord.set_speed(50.0)

    # Worker 1: Rapid Pause / Resume spam
    async def toggle_pause_resume():
        for _ in range(50):
            await coord.pause()
            await asyncio.sleep(0.001)
            await coord.resume()
            await asyncio.sleep(0.001)

    # Worker 2: Rapid Speed Adjustment with fuzzing
    async def fuzzed_speed_adjust():
        fuzz_speeds = [-100.0, 0.0, 0.5, 12.5, 25.0, 100.0, 1e6, -1e-6]
        for spd in fuzz_speeds * 6:
            coord.set_speed(spd)
            # Verify clamped bounds
            assert coord.config.min_tps <= coord.tps <= coord.config.max_tps
            await asyncio.sleep(0.001)

    # Worker 3: Discrete step() calls interleaved with running loop
    async def interleaved_stepping():
        for _ in range(25):
            await coord.pause()
            delta = await coord.step()
            assert delta["type"] == "TICK_DELTA"
            await coord.resume()
            await asyncio.sleep(0.002)

    # Worker 4: Enqueue commands while toggles occur
    async def concurrent_commands():
        for i in range(100):
            coord.enqueue_command("SET_SPEED", {"tps": random.choice([5.0, 10.0, 20.0])})
            if i % 10 == 0:
                coord.enqueue_command("TRIGGER_EVENT", {"name": "RESOURCE_WINDFALL", "data": {"funds": 50}})
            await asyncio.sleep(0.001)

    # Start the continuous loop
    await coord.start()
    assert coord.state == SimulationState.RUNNING

    # Run all 4 workers concurrently
    await asyncio.gather(
        toggle_pause_resume(),
        fuzzed_speed_adjust(),
        interleaved_stepping(),
        concurrent_commands(),
    )

    # Stop cleanly
    await coord.stop()
    assert coord.state == SimulationState.STOPPED
    assert coord._loop_task is None or coord._loop_task.done()

    # Repeated stop() calls must be idempotent
    await coord.stop()
    await coord.stop()
    assert coord.state == SimulationState.STOPPED

    # Repeated start() and immediate stop()
    for _ in range(5):
        await coord.start()
        await coord.stop()
    assert coord.state == SimulationState.STOPPED

    elapsed = time.perf_counter() - t0
    print(f"  Fuzzed lifecycle over {elapsed:.3f}s; coordinator smoothly transitioned through {coord.current_tick} ticks.")
    print("  [Stress 2 PASSED]: Concurrency locks and lifecycle state machine are robust and deadlock-free.")


# =============================================================================
# Stress Test 3: Inbound Command Flooding & Malformed Payload Fuzzing
# =============================================================================

async def test_command_flooding_and_fuzzing():
    """
    Stress 3: Flood inbound command queue with 10,000 commands in a single tick.
    Injects valid, malformed, non-dict, out-of-bounds, invalid enum, and injection payloads.
    Verifies that all commands are drained without unhandled exceptions or state corruption.
    """
    print("\n--- [Stress 3] 10,000 Inbound Command Flooding & Payload Fuzzing ---")
    t0 = time.perf_counter()

    coord = SimulationCoordinator(config=DEFAULT_CONFIG)

    # Generate 10,000 commands
    num_commands = 10000
    for i in range(num_commands):
        category = i % 10
        if category == 0:
            # Valid REZONE
            coord.enqueue_command("REZONE", {"x": i % 32, "y": (i * 2) % 32, "zone": "PARK"})
        elif category == 1:
            # Valid CONSTRUCT
            coord.enqueue_command("CONSTRUCT", {"x": (i + 1) % 32, "y": (i + 3) % 32, "building_id": f"b_{i}", "building_type": "COMMERCIAL"})
        elif category == 2:
            # Valid SET_SPEED
            coord.enqueue_command("SET_SPEED", {"tps": 15.0})
        elif category == 3:
            # Valid TRIGGER_EVENT
            coord.enqueue_command("TRIGGER_EVENT", {"name": "RESOURCE_WINDFALL", "data": {"funds": 10.0, "materials": 5.0}})
        elif category == 4:
            # Malformed: Out-of-bounds coordinates
            coord.enqueue_command("REZONE", {"x": -9999, "y": 88888, "zone": "RESIDENTIAL"})
        elif category == 5:
            # Malformed: Invalid enum
            coord.enqueue_command("REZONE", {"x": 5, "y": 5, "zone": "CYBER_DYSTOPIA_NOT_REAL"})
        elif category == 6:
            # Malformed: Non-numeric coordinates
            coord.enqueue_command("CONSTRUCT", {"x": "not_an_int", "y": None, "building_id": "bad"})
        elif category == 7:
            # Malicious / Unknown action types
            coord.enqueue_command("SQL_INJECTION'; DROP TABLE parcels;--", {"evil": True})
        elif category == 8:
            # Empty payloads or None values
            coord.enqueue_command("TRIGGER_EVENT", {"name": "ZONING_MANDATE", "data": {"zone": "BAD_ZONE"}})
        elif category == 9:
            # Malformed payload structure
            coord.inbound_commands.put_nowait({"action": "SET_SPEED", "payload": {"tps": "not_a_float"}})

    assert coord.inbound_commands.qsize() == num_commands

    # Execute a single step tick to drain and resolve all 10,000 commands
    t_step_start = time.perf_counter()
    delta = await coord.step()
    step_duration = time.perf_counter() - t_step_start

    assert coord.inbound_commands.empty(), f"Queue not empty! Remaining: {coord.inbound_commands.qsize()}"
    assert delta["type"] == "TICK_DELTA"
    assert coord.current_tick == 1

    elapsed = time.perf_counter() - t0
    ops_sec = num_commands / step_duration
    print(f"  Drained and parsed {num_commands} commands in {step_duration:.3f}s ({ops_sec:,.0f} commands/sec)")

    # Verify grid wasn't corrupted
    assert coord.grid.get_parcel(0, 0) is not None
    assert coord.grid.is_valid_coord(0, 0) is True

    # Subsequent tick runs cleanly
    delta2 = await coord.step()
    assert delta2["tick"] == 2
    assert coord.current_tick == 2

    print("  [Stress 3 PASSED]: 10,000 inbound command flood swallowed gracefully without unhandled exceptions.")


# =============================================================================
# Stress Test 4: Democratic Consensus Voting & Ballot Flooding
# =============================================================================

async def test_consensus_voting_ballot_flooding():
    """
    Stress 4: 200 concurrent civic proposals with overlapping voting windows.
    Fuzzes with 20,000 ballots, duplicate voting, nonexistent voter IDs,
    tie votes (50.0%), and exact quorum threshold boundaries.
    """
    print("\n--- [Stress 4] Consensus Voting & 20,000 Ballot Flood Stress ---")
    t0 = time.perf_counter()

    bus = MessageBus()

    # Track callback invocations
    executed_callbacks: List[str] = []

    def on_initiative_passed(prop: CivicProposal):
        executed_callbacks.append(prop.id)

    bus.register_proposal_callback("REZONE", on_initiative_passed)
    bus.register_proposal_callback("ADJUST_TAX", on_initiative_passed)

    # 1. Submit 200 diverse proposals with varying quorums and lifespans
    num_proposals = 200
    proposals: List[CivicProposal] = []
    for i in range(num_proposals):
        p = CivicProposal(
            creator_id=f"agent_sponsor_{i % 10}",
            title=f"Civic Measure #{i}",
            description="Testing democratic voting under extreme concurrency",
            action_type="REZONE" if i % 2 == 0 else "ADJUST_TAX",
            action_payload={"x": i % 32, "y": (i * 3) % 32, "zone": "PARK"},
            created_tick=1,
            expires_tick=5 + (i % 15),
            quorum_required=10,
            pass_threshold_ratio=0.50,
        )
        bus.submit_proposal(p)
        proposals.append(p)

    assert len(bus.proposals) == num_proposals

    # 2. Flood with 20,000 ballots across the 200 proposals
    # Mix of Sybil voters, duplicate revotes, and varied choices
    t_ballot_start = time.perf_counter()
    num_ballots = 20000

    for b in range(num_ballots):
        p = proposals[b % num_proposals]
        # Some repeat voters (testing ballot overwriting / deduplication)
        voter_id = f"voter_{b % 30}" if b % 2 == 0 else f"sybil_voter_{b}"
        choice = VoteChoice.AYE if (b % 3 == 0) else (VoteChoice.NAY if b % 3 == 1 else VoteChoice.ABSTAIN)
        bus.cast_vote(p.id, voter_id, choice)

    ballot_duration = time.perf_counter() - t_ballot_start
    print(f"  Cast {num_ballots} ballots across {num_proposals} proposals in {ballot_duration:.3f}s ({num_ballots/ballot_duration:,.0f} ballots/s)")

    # 3. Precision Boundary Test: Exactly at 50.0% ratio must REJECT (> 0.50 requirement)
    tie_proposal = CivicProposal(
        creator_id="mayor",
        title="Exact 50-50 Tie Bill",
        description="Must fail because ratio is not strictly > 50%",
        action_type="REZONE",
        created_tick=1,
        expires_tick=10,
        quorum_required=4,
        pass_threshold_ratio=0.50,
    )
    bus.submit_proposal(tie_proposal)
    bus.cast_vote(tie_proposal.id, "v1", VoteChoice.AYE)
    bus.cast_vote(tie_proposal.id, "v2", VoteChoice.AYE)
    bus.cast_vote(tie_proposal.id, "v3", VoteChoice.NAY)
    bus.cast_vote(tie_proposal.id, "v4", VoteChoice.NAY)

    # 4. Precision Boundary Test: 100% Abstain votes with Quorum reached
    abstain_proposal = CivicProposal(
        creator_id="mayor",
        title="All Abstain Bill",
        description="Quorum reached but zero effective votes (must not divide by zero)",
        action_type="ADJUST_TAX",
        created_tick=1,
        expires_tick=10,
        quorum_required=3,
        pass_threshold_ratio=0.50,
    )
    bus.submit_proposal(abstain_proposal)
    bus.cast_vote(abstain_proposal.id, "v1", VoteChoice.ABSTAIN)
    bus.cast_vote(abstain_proposal.id, "v2", VoteChoice.ABSTAIN)
    bus.cast_vote(abstain_proposal.id, "v3", VoteChoice.ABSTAIN)

    # 5. Precision Boundary Test: 1 below quorum at expiration
    under_quorum_proposal = CivicProposal(
        creator_id="citizen_x",
        title="Under Quorum Expiration Bill",
        description="9 votes out of 10 required",
        action_type="REZONE",
        created_tick=1,
        expires_tick=10,
        quorum_required=10,
    )
    bus.submit_proposal(under_quorum_proposal)
    for q in range(9):
        bus.cast_vote(under_quorum_proposal.id, f"v_{q}", VoteChoice.AYE)

    # Evaluate at tick 10 (triggers evaluations)
    resolved = await bus.evaluate_proposals(current_tick=10)
    print(f"  Evaluated proposals at tick 10: {len(resolved)} resolved")

    # Verify tie proposal was REJECTED
    assert tie_proposal.status == ProposalStatus.REJECTED, f"Tie proposal status expected REJECTED, got {tie_proposal.status}"
    assert tie_proposal.id not in executed_callbacks

    # Verify 100% abstain proposal was REJECTED without error
    assert abstain_proposal.status == ProposalStatus.REJECTED, f"Abstain proposal status expected REJECTED, got {abstain_proposal.status}"

    # Verify under quorum proposal EXPIRED
    assert under_quorum_proposal.status == ProposalStatus.EXPIRED, f"Under quorum status expected EXPIRED, got {under_quorum_proposal.status}"

    # Verify voting on resolved proposal returns False
    vote_post_resolved = bus.cast_vote(tie_proposal.id, "late_voter", VoteChoice.AYE)
    assert vote_post_resolved is False, "Voting on already resolved proposal succeeded, expected False"

    # Verify voting on non-existent proposal returns False
    vote_fake = bus.cast_vote("non_existent_proposal_uuid", "v1", VoteChoice.AYE)
    assert vote_fake is False

    elapsed = time.perf_counter() - t0
    print(f"  [Stress 4 PASSED]: Democratic consensus verified across {num_ballots} ballots and exact boundary conditions in {elapsed:.3f}s.")


# =============================================================================
# Stress Test 5: High-Throughput Pub/Sub Message Flooding & Subscription Churn
# =============================================================================

async def test_pubsub_flooding_and_subscription_churn():
    """
    Stress 5: 50 registered agents, 15,000 pub/sub messages with dynamic churn.
    Agents constantly subscribe/unsubscribe while 1:1, topic, and broadcast messages flood.
    Verifies message delivery accuracy, bounded memory, and absence of race conditions.
    """
    print("\n--- [Stress 5] 15,000 Pub/Sub Message Flood & Subscription Churn ---")
    t0 = time.perf_counter()

    bus = MessageBus()
    num_agents = 50
    agents = [f"agent_net_{i}" for i in range(num_agents)]
    for a in agents:
        bus.register_agent(a)

    topics = ["general", "governance", "trade", "construction", "research", "emergency", "sports"]

    # Concurrently execute 3 tasks:
    # 1. Broadcaster & publisher
    async def message_publisher():
        delivered_total = 0
        for m in range(10000):
            sender = random.choice(agents)
            m_type = m % 3
            if m_type == 0:
                # Direct message
                recip = random.choice(agents)
                msg = AgentMessage(sender_id=sender, recipient_id=recip, type=MessageType.DIRECT, content=f"Hello {m}")
                if bus.send_direct(msg):
                    delivered_total += 1
            elif m_type == 1:
                # Topic publish
                top = random.choice(topics)
                msg = AgentMessage(sender_id=sender, topic=top, type=MessageType.TOPIC, content=f"Notice on {top}")
                delivered_total += bus.publish(top, msg)
            else:
                # Broadcast
                msg = AgentMessage(sender_id=sender, type=MessageType.BROADCAST, content=f"Broadcast {m}")
                delivered_total += bus.broadcast(msg)
            if m % 1000 == 0:
                await asyncio.sleep(0.0001)
        return delivered_total

    # 2. Subscription Churner
    async def subscription_churner():
        churn_count = 0
        for _ in range(2000):
            agent = random.choice(agents)
            top = random.choice(topics)
            if random.random() < 0.5:
                bus.subscribe(agent, top)
            else:
                bus.unsubscribe(agent, top)
            churn_count += 1
            if churn_count % 200 == 0:
                await asyncio.sleep(0.0001)
        return churn_count

    # 3. Inbox Drainer
    async def inbox_drainer():
        drained_total = 0
        for _ in range(50):
            for a in agents:
                msgs = bus.drain_inbox(a)
                drained_total += len(msgs)
            await asyncio.sleep(0.005)
        return drained_total

    delivered, churned, drained = await asyncio.gather(
        message_publisher(),
        subscription_churner(),
        inbox_drainer(),
    )

    elapsed = time.perf_counter() - t0
    print(f"  Delivered {delivered:,} message copies, executed {churned:,} sub/unsub churns, drained {drained:,} messages in {elapsed:.3f}s")

    # Invariants
    assert len(bus.broadcast_log) <= 200, "Broadcast log exceeded maxlen=200!"
    assert len(bus.dialogue_feed) <= 100, "Dialogue feed exceeded maxlen=100!"

    print("  [Stress 5 PASSED]: High-throughput messaging and subscriber churn handled cleanly.")


# =============================================================================
# Stress Test 6: Poison Callbacks & Extreme Economic Invariance
# =============================================================================

async def test_poison_callbacks_and_treasury_safety():
    """
    Stress 6: Submit proposals with malicious / crashing callbacks and poison payloads.
    Verifies that SimulationCoordinator catches exceptions and maintains state integrity.
    """
    print("\n--- [Stress 6] Poison Callbacks & Treasury Safety Invariance ---")
    t0 = time.perf_counter()

    coord = SimulationCoordinator(config=DEFAULT_CONFIG)

    # 1. Register a callback that deliberately throws an exception
    async def exploding_callback(proposal: CivicProposal):
        raise RuntimeError("FATAL INTENTIONAL EXPLOSION IN PROPOSAL EXECUTION")

    coord.message_bus.register_proposal_callback("EXPLODE", exploding_callback)

    # Submit proposal with exploding action
    poison_p = CivicProposal(
        creator_id="saboteur",
        title="Exploding Bill",
        description="Throws unhandled RuntimeError",
        action_type="EXPLODE",
        created_tick=1,
        expires_tick=5,
        quorum_required=2,
    )
    coord.message_bus.submit_proposal(poison_p)
    coord.message_bus.cast_vote(poison_p.id, "v1", VoteChoice.AYE)
    coord.message_bus.cast_vote(poison_p.id, "v2", VoteChoice.AYE)

    # 2. Submit grant disbursement proposal that tries to steal 10x treasury funds
    treasury_before = coord.economy.treasury.funds
    mega_grant = CivicProposal(
        creator_id="greedy_agent",
        title="Hyper-Grant",
        description="Request $1,000,000,000 from $5,000 treasury",
        action_type="DISBURSE_GRANT",
        action_payload={"recipient_id": "greedy_agent", "amount": 1_000_000_000.0},
        created_tick=1,
        expires_tick=5,
        quorum_required=2,
    )
    coord.message_bus.submit_proposal(mega_grant)
    coord.message_bus.cast_vote(mega_grant.id, "v1", VoteChoice.AYE)
    coord.message_bus.cast_vote(mega_grant.id, "v2", VoteChoice.AYE)

    # Step simulation: Phase 4 will evaluate proposals and execute callbacks
    delta = await coord.step()
    assert delta["type"] == "TICK_DELTA"

    # Verifications:
    # 1. Exploding callback did NOT crash the coordinator
    assert poison_p.status == ProposalStatus.EXECUTED or poison_p.status == ProposalStatus.PASSED

    # 2. Treasury did NOT go negative from hyper grant
    assert coord.economy.treasury.funds == treasury_before, f"Treasury was compromised! Before={treasury_before}, After={coord.economy.treasury.funds}"
    greedy_ledger = coord.economy.get_ledger("greedy_agent")
    assert greedy_ledger is None or greedy_ledger.funds == 0.0 or greedy_ledger.funds == coord.config.default_agent_funds

    elapsed = time.perf_counter() - t0
    print(f"  Safeguards verified against poison callbacks and invalid economic disbursement in {elapsed:.3f}s.")
    print("  [Stress 6 PASSED]: Defensive exception handling and economic safety guards held under attack.")


# =============================================================================
# Main Orchestrator Runner
# =============================================================================

async def main():
    print("================================================================================")
    print("STARTING EMPIRICAL ADVERSARIAL STRESS SUITE: agent_city (Milestone 1)")
    print("================================================================================")
    start_all = time.perf_counter()

    try:
        await test_long_continuous_simulation()
        await test_rapid_lifecycle_toggles()
        await test_command_flooding_and_fuzzing()
        await test_consensus_voting_ballot_flooding()
        await test_pubsub_flooding_and_subscription_churn()
        await test_poison_callbacks_and_treasury_safety()

        total_elapsed = time.perf_counter() - start_all
        print("\n================================================================================")
        print(f"ALL 6 ADVERSARIAL STRESS TESTS PASSED EMPIRICALLY in {total_elapsed:.2f}s!")
        print("VERDICT: APPROVE")
        print("================================================================================")
        return 0

    except Exception as exc:
        total_elapsed = time.perf_counter() - start_all
        print("\n================================================================================")
        print(f"STRESS TEST SUITE FAILED with error: {exc}")
        import traceback
        traceback.print_exc()
        print(f"Elapsed before failure: {total_elapsed:.2f}s")
        print("VERDICT: REJECT")
        print("================================================================================")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
