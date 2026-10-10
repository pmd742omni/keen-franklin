"""6-Phase Asynchronous Simulation Coordinator managing city lifecycle, agents, and state deltas."""

from __future__ import annotations

import asyncio
import inspect
import time
import uuid
from typing import Callable, Dict, List, Optional, Tuple, Any

from agent_city.config import (
    DEFAULT_CONFIG,
    MessageType,
    ProposalStatus,
    SimulationConfig,
    SimulationState,
    VoteChoice,
    ZoneType,
)
from agent_city.engine.economy import EconomySystem
from agent_city.engine.grid import CityGrid, Parcel
from agent_city.engine.message_bus import AgentMessage, CivicProposal, MessageBus


class SimulationCoordinator:
    """
    Central orchestration engine for the Virtual City.
    Executes a deterministic 6-phase asynchronous tick loop:
      Phase 1: Inbound Command & Message Ingestion
      Phase 2: Agent Perception & Deliberation
      Phase 3: Spatial Movement & Action Resolution
      Phase 4: Environmental & Economic Lifecycle
      Phase 5: State Delta Compilation & Broadcast Hooks
      Phase 6: Timing Regulation & Drift Compensation
    """

    def __init__(self, config: Optional[SimulationConfig] = None):
        self.config: SimulationConfig = config or DEFAULT_CONFIG
        self.state: SimulationState = SimulationState.STOPPED
        self.current_tick: int = 0
        self.current_epoch: int = 0
        self.tps: float = self.config.default_tps

        # Subsystems
        self.grid: CityGrid = CityGrid(
            width=self.config.grid_width,
            height=self.config.grid_height,
            terrain_costs=self.config.terrain_costs,
        )
        self.economy: EconomySystem = EconomySystem(self.config)
        self.message_bus: MessageBus = MessageBus()

        # Agent registry: agent_id -> Agent object
        self.agents: Dict[str, Any] = {}

        # Asynchronous queues and synchronization
        self.inbound_commands: asyncio.Queue[Dict[str, Any]] = asyncio.Queue()
        self.delta_callbacks: List[Callable[[Dict[str, Any]], Any]] = []
        self._lock: asyncio.Lock = asyncio.Lock()
        self._loop_task: Optional[asyncio.Task] = None
        self._step_event: asyncio.Event = asyncio.Event()

        # Metrics & transient state
        self.active_events: List[Dict[str, Any]] = []
        self.dirty_parcels: set[Tuple[int, int]] = set()
        self.tick_overruns: int = 0
        self.last_tick_duration_ms: float = 0.0

        # Wire built-in proposal actions to city execution callbacks
        self._register_default_proposal_callbacks()

    def _register_default_proposal_callbacks(self) -> None:
        """Connect legislative proposal outcomes to physical city modifications."""
        async def on_rezone_passed(proposal: CivicProposal) -> None:
            x = proposal.action_payload.get("x")
            y = proposal.action_payload.get("y")
            zone_str = proposal.action_payload.get("zone")
            if x is not None and y is not None and zone_str:
                try:
                    new_zone = ZoneType(zone_str)
                    self.grid.set_zone(int(x), int(y), new_zone)
                    self.dirty_parcels.add((int(x), int(y)))
                except ValueError:
                    pass

        async def on_tax_adjust_passed(proposal: CivicProposal) -> None:
            new_rate = proposal.action_payload.get("sales_tax_rate")
            if new_rate is not None:
                self.economy.sales_tax_rate = max(0.0, min(0.25, float(new_rate)))

        async def on_grant_passed(proposal: CivicProposal) -> None:
            target = proposal.action_payload.get("recipient_id")
            amount = proposal.action_payload.get("amount", 0.0)
            if target and amount > 0:
                self.economy.disburse_grant(
                    recipient_id=target,
                    amount=float(amount),
                    tick=self.current_tick,
                    description=f"Legislative Grant: {proposal.title}",
                )

        self.message_bus.register_proposal_callback("REZONE", on_rezone_passed)
        self.message_bus.register_proposal_callback("ADJUST_TAX", on_tax_adjust_passed)
        self.message_bus.register_proposal_callback("DISBURSE_GRANT", on_grant_passed)

    # =========================================================================
    # Agent Registration & Lifecycle Hooks
    # =========================================================================

    def register_agent(
        self,
        agent: Any,
        initial_x: Optional[int] = None,
        initial_y: Optional[int] = None,
        initial_funds: Optional[float] = None,
        initial_energy: Optional[float] = None,
        initial_materials: Optional[float] = None,
    ) -> None:
        """
        Register an agent into the simulation. Sets up grid positioning,
        message bus mailboxes, and economic ledger accounts.
        """
        agent_id = getattr(agent, "id", None) or getattr(agent, "agent_id", str(id(agent)))
        self.agents[agent_id] = agent

        # Economy account
        self.economy.register_account(
            account_id=agent_id,
            funds=initial_funds,
            energy=initial_energy,
            materials=initial_materials,
        )

        # Message bus mailbox
        self.message_bus.register_agent(agent_id)

        # Position on grid if provided
        pos_x = initial_x if initial_x is not None else getattr(agent, "x", None)
        pos_y = initial_y if initial_y is not None else getattr(agent, "y", None)

        if pos_x is not None and pos_y is not None:
            # Find closest passable tile if target is blocked
            if self.grid.can_move_to(pos_x, pos_y, agent_id):
                self.grid.teleport_occupant(pos_x, pos_y, agent_id)
            else:
                placed = False
                for r in range(1, 5):
                    for dx in range(-r, r + 1):
                        for dy in range(-r, r + 1):
                            nx, ny = pos_x + dx, pos_y + dy
                            if self.grid.can_move_to(nx, ny, agent_id):
                                self.grid.teleport_occupant(nx, ny, agent_id)
                                pos_x, pos_y = nx, ny
                                placed = True
                                break
                        if placed:
                            break

            # Sync position back to agent object if mutable
            if hasattr(agent, "x"):
                agent.x = pos_x
            if hasattr(agent, "y"):
                agent.y = pos_y

    def unregister_agent(self, agent_id: str) -> Optional[Any]:
        """Unregister and clean up an agent from the simulation."""
        self.grid.remove_occupant(agent_id)
        self.message_bus.unregister_agent(agent_id)
        self.economy.unregister_account(agent_id)
        return self.agents.pop(agent_id, None)

    def add_delta_callback(
        self,
        callback: Callable[[Dict[str, Any]], Any],
    ) -> None:
        """Register a callback invoked at Phase 5 with the tick delta."""
        self.delta_callbacks.append(callback)

    def remove_delta_callback(
        self,
        callback: Callable[[Dict[str, Any]], Any],
    ) -> None:
        """Remove a previously registered delta callback."""
        if callback in self.delta_callbacks:
            self.delta_callbacks.remove(callback)

    # =========================================================================
    # Lifecycle Controls: Start, Stop, Pause, Resume, Speed
    # =========================================================================

    async def start(self) -> asyncio.Task:
        """Start the background simulation loop task."""
        async with self._lock:
            if self.state == SimulationState.RUNNING:
                return self._loop_task  # type: ignore

            self.state = SimulationState.RUNNING
            self._loop_task = asyncio.create_task(self._simulation_loop())
            return self._loop_task

    async def stop(self) -> None:
        """Stop and terminate the simulation loop task."""
        async with self._lock:
            self.state = SimulationState.STOPPED
            if self._loop_task and not self._loop_task.done():
                self._loop_task.cancel()
                try:
                    await self._loop_task
                except asyncio.CancelledError:
                    pass
            self._loop_task = None

    async def pause(self) -> None:
        """Pause the continuous simulation loop."""
        async with self._lock:
            if self.state == SimulationState.RUNNING:
                self.state = SimulationState.PAUSED

    async def resume(self) -> None:
        """Resume running after being paused."""
        async with self._lock:
            if self.state == SimulationState.PAUSED:
                self.state = SimulationState.RUNNING

    async def step(self) -> Dict[str, Any]:
        """
        Advance the simulation by exactly one tick.
        Can be invoked directly when paused or in stepping mode.
        """
        async with self._lock:
            prior_state = self.state
            self.state = SimulationState.STEPPING
            delta = await self.step_tick()
            self.state = prior_state if prior_state != SimulationState.STEPPING else SimulationState.PAUSED
            return delta

    def set_speed(self, tps: float) -> float:
        """Dynamically set the simulation rate in ticks per second."""
        self.tps = max(self.config.min_tps, min(self.config.max_tps, float(tps)))
        return self.tps

    def enqueue_command(
        self,
        action: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Queue an external command from REST or WebSocket API."""
        self.inbound_commands.put_nowait({
            "action": action.upper(),
            "payload": payload or {},
        })

    def trigger_event(
        self,
        event_name: str,
        title: str,
        description: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Inject a manual or emergent city event."""
        pld = payload or {}
        event_data = {
            "id": str(uuid.uuid4())[:8],
            "tick": self.current_tick,
            "type": event_name.upper(),
            "title": title,
            "description": description,
            "payload": pld,
        }
        self.active_events.append(event_data)

        # Built-in event logic
        if event_name.upper() == "RESOURCE_WINDFALL":
            funds_add = float(pld.get("funds", 1000.0))
            materials_add = float(pld.get("materials", 250.0))
            self.economy.treasury.deposit(funds=funds_add, materials=materials_add)
            self.message_bus.broadcast(
                AgentMessage(
                    tick=self.current_tick,
                    sender_id="treasury",
                    sender_role="TREASURER",
                    content=f"RESOURCE WINDFALL! Municipal treasury received +${funds_add} and +{materials_add} materials.",
                )
            )
        elif event_name.upper() == "ZONING_MANDATE":
            target_zone = ZoneType(pld.get("zone", "PARK"))
            count = int(pld.get("count", 4))
            rezoned = 0
            for row in self.grid._grid:
                for parcel in row:
                    if parcel.zone == ZoneType.WILDERNESS and rezoned < count:
                        self.grid.set_zone(parcel.x, parcel.y, target_zone)
                        self.dirty_parcels.add((parcel.x, parcel.y))
                        rezoned += 1
            self.message_bus.broadcast(
                AgentMessage(
                    tick=self.current_tick,
                    sender_id="city_council",
                    sender_role="COUNCIL",
                    content=f"ZONING MANDATE: Rezoned {rezoned} parcels to {target_zone.value}.",
                )
            )

        return event_data

    # =========================================================================
    # The 6-Phase Asynchronous Tick Coordinator
    # =========================================================================

    async def _simulation_loop(self) -> None:
        """Continuous async loop executing ticks according to target TPS."""
        while self.state != SimulationState.STOPPED:
            if self.state == SimulationState.PAUSED:
                await asyncio.sleep(0.05)
                continue

            start_time = time.monotonic()
            await self.step_tick()
            elapsed = time.monotonic() - start_time
            self.last_tick_duration_ms = elapsed * 1000.0

            # Phase 6: Drift Compensation & Timing Control
            target_interval = 1.0 / self.tps
            sleep_duration = max(0.0, target_interval - elapsed)
            if elapsed > target_interval:
                self.tick_overruns += 1

            if sleep_duration > 0:
                await asyncio.sleep(sleep_duration)

    async def step_tick(self) -> Dict[str, Any]:
        """
        Execute one discrete simulation tick through all 6 phases.
        Returns the compiled State Delta dictionary.
        """
        self.current_tick += 1
        t_start = time.monotonic()

        # =====================================================================
        # Phase 1: Inbound Command & Message Ingestion
        # =====================================================================
        await self._phase_1_ingest_commands()

        # =====================================================================
        # Phase 2: Agent Perception & Deliberation
        # =====================================================================
        agent_actions = await self._phase_2_perceive_and_deliberate()

        # =====================================================================
        # Phase 3: Spatial Movement & Action Resolution
        # =====================================================================
        resolved_actions = await self._phase_3_resolve_actions(agent_actions)

        # =====================================================================
        # Phase 4: Environmental & Economic Lifecycle
        # =====================================================================
        await self._phase_4_lifecycle_updates()

        # =====================================================================
        # Phase 5: State Delta Compilation & Broadcast Hooks
        # =====================================================================
        delta = self._phase_5_compile_delta(resolved_actions)
        await self._phase_5_broadcast_delta(delta)

        # Cleanup transient tick buffers
        self.dirty_parcels.clear()
        self.active_events.clear()

        self.last_tick_duration_ms = (time.monotonic() - t_start) * 1000.0
        return delta

    async def _phase_1_ingest_commands(self) -> None:
        """Drain and execute external commands from inbound queue."""
        while not self.inbound_commands.empty():
            try:
                cmd = self.inbound_commands.get_nowait()
                action = cmd.get("action", "")
                payload = cmd.get("payload", {})

                if action == "PAUSE":
                    self.state = SimulationState.PAUSED
                elif action == "RESUME":
                    self.state = SimulationState.RUNNING
                elif action == "SET_SPEED":
                    new_tps = payload.get("tps")
                    if new_tps is not None:
                        self.set_speed(float(new_tps))
                elif action == "TRIGGER_EVENT":
                    self.trigger_event(
                        event_name=payload.get("name", "CUSTOM_EVENT"),
                        title=payload.get("title", "City Event"),
                        description=payload.get("description", ""),
                        payload=payload.get("data", {}),
                    )
                elif action == "REZONE":
                    x, y = payload.get("x"), payload.get("y")
                    zone_str = payload.get("zone")
                    if x is not None and y is not None and zone_str:
                        self.grid.set_zone(int(x), int(y), ZoneType(zone_str))
                        self.dirty_parcels.add((int(x), int(y)))
                elif action == "CONSTRUCT":
                    x, y = payload.get("x"), payload.get("y")
                    b_id = payload.get("building_id", str(uuid.uuid4())[:8])
                    b_type = payload.get("building_type", "COMMERCIAL")
                    if x is not None and y is not None:
                        self.grid.set_building(
                            int(x), int(y), building_id=b_id, building_type=b_type
                        )
                        self.dirty_parcels.add((int(x), int(y)))
            except Exception as e:
                print(f"[SimulationCoordinator] Error processing command: {e}")

    async def _phase_2_perceive_and_deliberate(self) -> List[Tuple[str, Any]]:
        """
        Poll all active agents to perceive neighborhood and deliberate decisions.
        Returns a list of (agent_id, proposed_action).
        """
        actions: List[Tuple[str, Any]] = []

        for agent_id, agent in list(self.agents.items()):
            try:
                # 1. Deliver pending messages to agent inbox
                inbox_msgs = self.message_bus.drain_inbox(agent_id)
                if hasattr(agent, "receive_messages"):
                    res = agent.receive_messages(inbox_msgs)
                    if inspect.isawaitable(res):
                        await res

                # 2. Perception context
                pos = self.grid.find_agent_pos(agent_id)
                context = {
                    "tick": self.current_tick,
                    "epoch": self.current_epoch,
                    "position": pos,
                    "ledger": self.economy.get_ledger(agent_id),
                    "treasury": self.economy.treasury,
                    "active_events": self.active_events,
                }

                if hasattr(agent, "perceive"):
                    res = agent.perceive(context)
                    if inspect.isawaitable(res):
                        await res

                # 3. Deliberation
                action = None
                if hasattr(agent, "deliberate"):
                    res = agent.deliberate()
                    action = await res if inspect.isawaitable(res) else res

                if action is not None:
                    actions.append((agent_id, action))

            except Exception as e:
                print(f"[SimulationCoordinator] Error in agent {agent_id} deliberation: {e}")

        return actions

    async def _phase_3_resolve_actions(
        self,
        agent_actions: List[Tuple[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Validate and execute proposed agent actions, resolving spatial collisions
        and updating economy and grid state atomically.
        """
        resolved: List[Dict[str, Any]] = []

        for agent_id, action in agent_actions:
            agent = self.agents.get(agent_id)
            if not agent:
                continue

            # Standardize action structure (supports dict, dataclass, or Pydantic model)
            act_type = (
                action.get("type")
                if isinstance(action, dict)
                else getattr(action, "type", getattr(action, "action_type", "IDLE"))
            )
            act_type = str(act_type).upper()

            act_target = (
                action.get("target")
                if isinstance(action, dict)
                else getattr(action, "target", getattr(action, "target_pos", None))
            )

            act_payload = (
                action.get("payload")
                if isinstance(action, dict)
                else getattr(action, "payload", {})
            )

            # -----------------------------------------------------------------
            # 1. MOVEMENT ACTION
            # -----------------------------------------------------------------
            if act_type in ("MOVE", "STEP"):
                pos = self.grid.find_agent_pos(agent_id)
                if pos and act_target:
                    tx, ty = int(act_target[0]), int(act_target[1])
                    ledger = self.economy.get_or_create_ledger(agent_id)
                    if ledger.energy < self.config.energy_burn_move:
                        resolved.append({
                            "agent_id": agent_id,
                            "action": "MOVE",
                            "status": "EXHAUSTED",
                            "from": pos,
                            "target": (tx, ty),
                        })
                        continue
                    success = self.grid.move_occupant(pos[0], pos[1], tx, ty, agent_id)
                    if success:
                        if hasattr(agent, "x"):
                            agent.x = tx
                        if hasattr(agent, "y"):
                            agent.y = ty
                        # Burn moving energy
                        self.economy.consume_agent_energy(
                            agent_id, self.config.energy_burn_move, self.current_tick
                        )
                        resolved.append({
                            "agent_id": agent_id,
                            "action": "MOVE",
                            "status": "SUCCESS",
                            "from": pos,
                            "to": (tx, ty),
                        })
                    else:
                        resolved.append({
                            "agent_id": agent_id,
                            "action": "MOVE",
                            "status": "BLOCKED",
                            "from": pos,
                            "target": (tx, ty),
                        })

            # -----------------------------------------------------------------
            # 2. CONSTRUCT / BUILD ACTION
            # -----------------------------------------------------------------
            elif act_type in ("BUILD", "CONSTRUCT"):
                pos = self.grid.find_agent_pos(agent_id)
                target = act_target or pos
                if target:
                    bx, by = int(target[0]), int(target[1])
                    ledger = self.economy.get_or_create_ledger(agent_id)
                    if ledger.energy < self.config.energy_burn_work:
                        resolved.append({
                            "agent_id": agent_id,
                            "action": "BUILD",
                            "status": "EXHAUSTED",
                        })
                        continue
                    mat_cost = float(act_payload.get("materials_cost", 10.0))

                    if ledger.withdraw(materials=mat_cost):
                        b_id = act_payload.get("building_id", str(uuid.uuid4())[:8])
                        b_type = act_payload.get("building_type", "RESIDENTIAL")
                        parcel = self.grid.set_building(
                            bx, by, building_id=b_id, building_type=b_type
                        )
                        if parcel:
                            parcel.metadata["owner_id"] = agent_id
                        self.dirty_parcels.add((bx, by))
                        self.economy.consume_agent_energy(
                            agent_id, self.config.energy_burn_work, self.current_tick
                        )
                        resolved.append({
                            "agent_id": agent_id,
                            "action": "BUILD",
                            "status": "SUCCESS",
                            "position": (bx, by),
                            "building_id": b_id,
                        })
                    else:
                        resolved.append({
                            "agent_id": agent_id,
                            "action": "BUILD",
                            "status": "INSUFFICIENT_MATERIALS",
                        })

            # -----------------------------------------------------------------
            # 3. REZONE ACTION
            # -----------------------------------------------------------------
            elif act_type == "REZONE":
                target = act_target
                zone_str = act_payload.get("zone")
                if target and zone_str:
                    rx, ry = int(target[0]), int(target[1])
                    fee = self.config.zoning_permit_cost
                    ledger = self.economy.get_or_create_ledger(agent_id)
                    if ledger.withdraw(funds=fee):
                        self.economy.treasury.deposit(funds=fee)
                        new_zone = ZoneType(zone_str)
                        self.grid.set_zone(rx, ry, new_zone)
                        self.dirty_parcels.add((rx, ry))
                        resolved.append({
                            "agent_id": agent_id,
                            "action": "REZONE",
                            "status": "SUCCESS",
                            "target": (rx, ry),
                            "zone": new_zone.value,
                        })
                    else:
                        resolved.append({
                            "agent_id": agent_id,
                            "action": "REZONE",
                            "status": "INSUFFICIENT_FUNDS",
                        })

            # -----------------------------------------------------------------
            # 4. TRADE ACTION
            # -----------------------------------------------------------------
            elif act_type == "TRADE":
                recipient_id = act_payload.get("recipient_id")
                amount = float(act_payload.get("amount", 0.0))
                resource = act_payload.get("resource", "funds")
                if recipient_id and amount > 0:
                    tx = self.economy.transfer(
                        sender_id=agent_id,
                        recipient_id=recipient_id,
                        amount=amount,
                        resource=resource,
                        category="COMMERCIAL_TRADE",
                        tick=self.current_tick,
                        description=act_payload.get("description", "Commercial Trade"),
                    )
                    status = "SUCCESS" if tx else "FAILED"
                    resolved.append({
                        "agent_id": agent_id,
                        "action": "TRADE",
                        "status": status,
                        "recipient": recipient_id,
                        "amount": amount,
                    })

            # -----------------------------------------------------------------
            # 5. REST / RECHARGE ACTION
            # -----------------------------------------------------------------
            elif act_type == "REST":
                pos = self.grid.find_agent_pos(agent_id)
                regen = self.config.energy_regen_residential
                if pos:
                    parcel = self.grid.get_parcel(pos[0], pos[1])
                    if parcel and parcel.zone == ZoneType.RESIDENTIAL:
                        regen *= 1.5
                new_energy = self.economy.replenish_agent_energy(
                    agent_id, regen, self.current_tick
                )
                resolved.append({
                    "agent_id": agent_id,
                    "action": "REST",
                    "status": "SUCCESS",
                    "energy": new_energy,
                })

            # -----------------------------------------------------------------
            # 6. COMMUNICATION / SPEECH ACTION
            # -----------------------------------------------------------------
            elif act_type in ("SPEAK", "BROADCAST", "MESSAGE"):
                content = act_payload.get("content", "")
                role = getattr(agent, "role", "CITIZEN")
                msg = AgentMessage(
                    tick=self.current_tick,
                    sender_id=agent_id,
                    sender_role=str(role),
                    content=content,
                    topic=act_payload.get("topic", "general"),
                )
                if act_payload.get("recipient_id"):
                    msg.recipient_id = act_payload["recipient_id"]
                    self.message_bus.send_direct(msg)
                else:
                    self.message_bus.broadcast(msg)
                resolved.append({
                    "agent_id": agent_id,
                    "action": "SPEAK",
                    "status": "SUCCESS",
                })

            # -----------------------------------------------------------------
            # 7. PROPOSAL / VOTING ACTION
            # -----------------------------------------------------------------
            elif act_type == "PROPOSE":
                proposal = CivicProposal(
                    creator_id=agent_id,
                    title=act_payload.get("title", "Civic Initiative"),
                    description=act_payload.get("description", ""),
                    action_type=act_payload.get("action_type", "REZONE"),
                    action_payload=act_payload.get("action_payload", {}),
                    created_tick=self.current_tick,
                    expires_tick=self.current_tick + self.config.default_proposal_duration_ticks,
                    quorum_required=act_payload.get("quorum", 3),
                )
                self.message_bus.submit_proposal(proposal)
                resolved.append({
                    "agent_id": agent_id,
                    "action": "PROPOSE",
                    "status": "SUCCESS",
                    "proposal_id": proposal.id,
                })

            elif act_type == "VOTE":
                p_id = act_payload.get("proposal_id")
                choice_str = act_payload.get("choice", "AYE").upper()
                if p_id and hasattr(VoteChoice, choice_str):
                    success = self.message_bus.cast_vote(
                        proposal_id=p_id,
                        voter_id=agent_id,
                        vote=VoteChoice[choice_str],
                    )
                    resolved.append({
                        "agent_id": agent_id,
                        "action": "VOTE",
                        "status": "SUCCESS" if success else "FAILED",
                        "proposal_id": p_id,
                    })

        return resolved

    async def _phase_4_lifecycle_updates(self) -> None:
        """
        Execute environmental updates, idle metabolism, building production,
        consensus ballot resolution, and epoch boundary accounting.
        """
        # 1. Idle energy burn for agents
        for agent_id in self.agents.keys():
            self.economy.consume_agent_energy(
                agent_id, self.config.energy_burn_idle, self.current_tick
            )

        # 2. Building resource yields (e.g. Industrial generates materials)
        for row in self.grid._grid:
            for parcel in row:
                if parcel.building_id:
                    if parcel.zone == ZoneType.INDUSTRIAL:
                        self.economy.treasury.deposit(materials=0.2, energy=0.1)
                    elif parcel.zone == ZoneType.COMMERCIAL:
                        self.economy.treasury.deposit(funds=0.1)

        # 3. Evaluate consensus proposals
        await self.message_bus.evaluate_proposals(self.current_tick)

        # 4. Epoch boundary check
        if (
            self.current_tick > 0
            and self.current_tick % self.config.ticks_per_epoch == 0
        ):
            await self._run_epoch_transition()

    async def _run_epoch_transition(self) -> None:
        """Triggered every ticks_per_epoch ticks."""
        self.current_epoch += 1

        # 1. Municipal Property Tax Assessment
        parcels_with_buildings: List[Tuple[str, str]] = []
        for row in self.grid._grid:
            for p in row:
                if p.building_id:
                    owner = p.metadata.get("owner_id", "public")
                    parcels_with_buildings.append((owner, p.building_id))

        taxes_collected = self.economy.collect_property_taxes(
            parcels_with_buildings, self.current_tick
        )

        # 2. Infrastructure maintenance deduction
        maintenance_cost = len(parcels_with_buildings) * 2.0
        self.economy.charge_maintenance(
            maintenance_cost, self.current_tick, "City Infrastructure Maintenance"
        )

        # 3. Epoch notification to agents
        for agent in self.agents.values():
            if hasattr(agent, "on_epoch"):
                try:
                    res = agent.on_epoch(self.current_epoch)
                    if inspect.isawaitable(res):
                        await res
                except Exception as e:
                    print(f"[SimulationCoordinator] Error in agent epoch transition: {e}")

        # Broadcast Epoch event
        self.trigger_event(
            event_name="EPOCH_TRANSITION",
            title=f"Epoch {self.current_epoch} Commenced",
            description=f"Property taxes collected: ${taxes_collected}. Maintenance: ${maintenance_cost}.",
            payload={"epoch": self.current_epoch, "tax_collected": taxes_collected},
        )

    def get_tick_delta(
        self,
        resolved_actions: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Compile compact differential state delta for frontend WebSocket streaming (< 1.5 KB)."""
        return self._phase_5_compile_delta(resolved_actions or [])

    def _phase_5_compile_delta(
        self,
        resolved_actions: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Compile compact differential state delta for frontend WebSocket streaming.
        Target footprint: < 1.5 KB per tick.
        """
        # Active agents snapshot (compact)
        agent_deltas: List[Dict[str, Any]] = []
        for agent_id, agent in self.agents.items():
            pos = self.grid.find_agent_pos(agent_id)
            ledger = self.economy.get_ledger(agent_id)
            ad: Dict[str, Any] = {
                "id": agent_id,
                "role": getattr(agent, "role", "CITIZEN"),
                "state": getattr(agent, "state", "IDLE"),
                "x": pos[0] if pos else 0,
                "y": pos[1] if pos else 0,
                "energy": round(ledger.energy, 1) if ledger else 100.0,
                "funds": round(ledger.funds, 1) if ledger else 0.0,
            }
            cur_act = getattr(agent, "current_action", None)
            if cur_act is not None:
                ad["current_action"] = cur_act
            agent_deltas.append(ad)

        # Changed parcels (compact, max 10)
        parcel_deltas: List[Dict[str, Any]] = []
        for x, y in list(self.dirty_parcels)[:10]:
            p = self.grid.get_parcel(x, y)
            if p is not None:
                pd: Dict[str, Any] = {
                    "x": p.x,
                    "y": p.y,
                    "zone": p.zone.value if hasattr(p.zone, "value") else str(p.zone),
                    "passable": p.passable,
                }
                if p.building_id:
                    pd["building_id"] = p.building_id
                    pd["building_type"] = p.building_type
                if p.occupant_id:
                    pd["occupant_id"] = p.occupant_id
                parcel_deltas.append(pd)

        # Recent dialogues (capped at rolling max 5)
        new_dialogues = [
            msg.to_dict()
            for msg in self.message_bus.dialogue_feed
            if msg.tick == self.current_tick
        ][-5:]

        # Active proposals (capped at max 5)
        active_proposals = [
            p.to_dict()
            for p in self.message_bus.proposals.values()
            if p.status == ProposalStatus.ACTIVE
        ][:5]

        # Compact resolved actions (capped at max 5)
        compact_resolved = [
            {
                "agent_id": ra.get("agent_id"),
                "action": ra.get("action"),
                "status": ra.get("status"),
            }
            for ra in resolved_actions[-5:]
        ]

        return {
            "type": "TICK_DELTA",
            "tick": self.current_tick,
            "epoch": self.current_epoch,
            "tps": self.tps,
            "state": self.state.value,
            "agents": agent_deltas,
            "parcels": parcel_deltas,
            "dialogues": new_dialogues,
            "events": list(self.active_events)[:5],
            "proposals": active_proposals,
            "treasury": self.economy.treasury.to_dict(),
            "resolved_actions": compact_resolved,
            "metrics": {
                "active_agents": len(self.agents),
                "duration_ms": round(self.last_tick_duration_ms, 2),
                "tick_overruns": self.tick_overruns,
            },
        }

    async def _phase_5_broadcast_delta(self, delta: Dict[str, Any]) -> None:
        """Invoke registered delta streaming callbacks."""
        for callback in list(self.delta_callbacks):
            try:
                res = callback(delta)
                if inspect.isawaitable(res):
                    await res
            except Exception as e:
                print(f"[SimulationCoordinator] Delta callback error: {e}")

    # =========================================================================
    # State Snapshot & Summary Endpoints
    # =========================================================================

    def get_init_state(self) -> Dict[str, Any]:
        """Produce complete state initialization snapshot for new client connections."""
        return {
            "type": "INIT_STATE",
            "tick": self.current_tick,
            "epoch": self.current_epoch,
            "tps": self.tps,
            "state": self.state.value,
            "config": self.config.model_dump(mode="json"),
            "grid": self.grid.to_dict(),
            "treasury": self.economy.treasury.to_dict(),
            "metrics": self.economy.get_metrics(),
            "dialogues": self.message_bus.get_recent_dialogues(50),
            "proposals": [p.to_dict() for p in self.message_bus.proposals.values()],
            "agents": [
                {
                    "id": a_id,
                    "role": getattr(agent, "role", "CITIZEN"),
                    "state": getattr(agent, "state", "IDLE"),
                    "x": self.grid.find_agent_pos(a_id)[0] if self.grid.find_agent_pos(a_id) else 0,
                    "y": self.grid.find_agent_pos(a_id)[1] if self.grid.find_agent_pos(a_id) else 0,
                    "energy": self.economy.get_or_create_ledger(a_id).energy,
                    "funds": self.economy.get_or_create_ledger(a_id).funds,
                    "materials": self.economy.get_or_create_ledger(a_id).materials,
                }
                for a_id, agent in self.agents.items()
            ],
        }

    def get_city_status(self) -> Dict[str, Any]:
        """Produce high-level operational status summary for REST API."""
        building_count = sum(
            1 for row in self.grid._grid for p in row if p.building_id is not None
        )
        return {
            "tick": self.current_tick,
            "epoch": self.current_epoch,
            "state": self.state.value,
            "tps": self.tps,
            "agents_count": len(self.agents),
            "buildings_count": building_count,
            "treasury": self.economy.treasury.to_dict(),
            "total_tax_collected": self.economy.total_tax_collected,
            "recent_events": list(self.active_events),
            "tick_overruns": self.tick_overruns,
        }

    # =========================================================================
    # Serialization
    # =========================================================================

    def to_dict(self) -> Dict[str, Any]:
        """Export complete coordinator state for durable persistence."""
        return {
            "tick": self.current_tick,
            "epoch": self.current_epoch,
            "tps": self.tps,
            "state": self.state.value,
            "grid": self.grid.to_dict(),
            "economy": self.economy.to_dict(),
            "message_bus": self.message_bus.to_dict(),
        }

    @classmethod
    def from_dict(
        cls,
        data: Dict[str, Any],
        config: Optional[SimulationConfig] = None,
    ) -> SimulationCoordinator:
        """Construct coordinator from serialized snapshot."""
        cfg = config or DEFAULT_CONFIG
        coord = cls(config=cfg)
        coord.current_tick = data.get("tick", 0)
        coord.current_epoch = data.get("epoch", 0)
        coord.tps = data.get("tps", cfg.default_tps)
        coord.state = SimulationState(data.get("state", SimulationState.PAUSED.value))

        if "grid" in data:
            coord.grid = CityGrid.from_dict(data["grid"])
        if "economy" in data:
            coord.economy = EconomySystem.from_dict(data["economy"], config=cfg)
        if "message_bus" in data:
            coord.message_bus = MessageBus.from_dict(data["message_bus"])

        return coord
