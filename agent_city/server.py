"""FastAPI REST and WebSocket Streaming Server for Agent City Simulation.
Integrates live Windows 11 hardware telemetry and autonomous optimizer agents.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

# Ensure root and module directories are in sys.path
_current_dir = Path(__file__).resolve().parent
_parent_dir = _current_dir.parent
for _p in (str(_parent_dir), str(_current_dir)):
    if _p not in sys.path:
        sys.path.insert(0, _p)
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from agent_city.config import DEFAULT_CONFIG, SimulationConfig, SimulationState
from agent_city.engine.simulation import SimulationCoordinator
from agent_city.engine.system_metrics import SystemMetricsCollector
from agent_city.agents.optimizer_roles import (
    MemoryGovernorAgent,
    StorageReclaimerAgent,
    ProcessGovernorAgent,
    StartupGuardianAgent,
    PerformanceAuditorAgent,
)

# -----------------------------------------------------------------------------
# Active coordinator instance
coordinator: SimulationCoordinator = SimulationCoordinator(config=DEFAULT_CONFIG)

# Real Laptop Optimizer Agents
optimizer_agents = [
    MemoryGovernorAgent(),
    StorageReclaimerAgent(),
    ProcessGovernorAgent(),
    StartupGuardianAgent(),
    PerformanceAuditorAgent(),
]

def populate_default_civic_agents(coord: SimulationCoordinator) -> None:
    """Seed the simulation with default civic agents if empty."""
    if not coord.agents:
        try:
            from agent_city.agents.roles import (
                MayorAgent,
                ArchitectAgent,
                EngineerAgent,
                MerchantAgent,
                ScholarAgent,
                ObserverAgent,
            )
            civic_agents = [
                MayorAgent(agent_id="agent_mayor_1", name="Mayor Vance", position=(2, 2)),
                ArchitectAgent(agent_id="agent_architect_1", name="Architect Iris", position=(4, 4)),
                EngineerAgent(agent_id="agent_engineer_1", name="Engineer Tor", position=(6, 6)),
                MerchantAgent(agent_id="agent_merchant_1", name="Merchant Silas", position=(8, 8)),
                ScholarAgent(agent_id="agent_scholar_1", name="Scholar Lin", position=(12, 12)),
                ObserverAgent(agent_id="agent_observer_1", name="Observer Nova", position=(1, 14)),
            ]
            for a in civic_agents:
                coord.register_agent(
                    agent=a,
                    initial_x=a.position[0],
                    initial_y=a.position[1],
                    initial_funds=a.funds,
                    initial_energy=a.energy,
                )
        except Exception as e:
            print(f"[Server] Note: Default agent seeding deferred: {e}")

populate_default_civic_agents(coordinator)

# Connected WebSocket clients
active_websockets: set[WebSocket] = set()

async def telemetry_broadcaster_loop() -> None:
    """Continuously broadcast live hardware telemetry to connected WebSockets."""
    while True:
        try:
            await asyncio.sleep(1.0)
            if not active_websockets:
                continue

            mem = SystemMetricsCollector.get_memory_metrics()
            cpu = SystemMetricsCollector.get_cpu_metrics()
            storage = SystemMetricsCollector.get_storage_metrics()
            smoothness = SystemMetricsCollector.calculate_smoothness_index(
                cpu["overall_pct"], mem["free_mb"], storage["free_gb"]
            )

            frame = {
                "type": "HARDWARE_TELEMETRY",
                "tick": coordinator.current_tick,
                "hardware_telemetry": {
                    "memory": mem,
                    "cpu": cpu,
                    "storage": storage,
                    "smoothness_index": smoothness,
                    "top_processes": SystemMetricsCollector.get_top_processes(8),
                    "optimizer_agents": [a.model_dump() for a in optimizer_agents],
                },
            }

            disconnected = set()
            for ws in list(active_websockets):
                try:
                    await ws.send_json(frame)
                except Exception:
                    disconnected.add(ws)
            for ws in disconnected:
                active_websockets.discard(ws)
        except asyncio.CancelledError:
            break
        except Exception:
            await asyncio.sleep(1.0)


@asynccontextmanager
async def lifespan(app: FastAPI):
    broadcaster = asyncio.create_task(telemetry_broadcaster_loop())
    yield
    broadcaster.cancel()
    try:
        await broadcaster
    except asyncio.CancelledError:
        pass


app = FastAPI(title="Virtual Agent City API", version="1.0.0", lifespan=lifespan)

# Enable CORS for browser integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def broadcast_tick_delta(delta: Dict[str, Any]) -> None:
    """Broadcast tick delta frame to all active WebSocket connections."""
    if not active_websockets:
        return

    # Enrich with live hardware telemetry
    try:
        mem = SystemMetricsCollector.get_memory_metrics()
        cpu = SystemMetricsCollector.get_cpu_metrics()
        storage = SystemMetricsCollector.get_storage_metrics()
        smoothness = SystemMetricsCollector.calculate_smoothness_index(
            cpu["overall_pct"], mem["free_mb"], storage["free_gb"]
        )

        telemetry = {
            "memory": mem,
            "cpu": cpu,
            "storage": storage,
            "smoothness_index": smoothness,
            "top_processes": SystemMetricsCollector.get_top_processes(5),
            "optimizer_agents": [a.model_dump() for a in optimizer_agents],
        }

        # Autonomous evaluation by optimizer agents
        for agent in optimizer_agents:
            action_event = agent.deliberate_and_act(telemetry)
            if action_event:
                if "dialogues" not in delta:
                    delta["dialogues"] = []
                delta["dialogues"].append({
                    "tick": coordinator.current_tick,
                    "sender_id": agent.agent_id,
                    "sender_role": agent.role,
                    "content": action_event.get("speech", ""),
                })
                coordinator.active_events.append({
                    "tick": coordinator.current_tick,
                    "type": action_event.get("type", "OPTIMIZATION"),
                    "title": f"{agent.name} Action",
                    "description": action_event.get("speech", ""),
                })

        delta["hardware_telemetry"] = telemetry
    except Exception as e:
        print(f"[Server] Telemetry broadcast error: {e}")

    disconnected = set()
    for ws in list(active_websockets):
        try:
            await ws.send_json(delta)
        except Exception:
            disconnected.add(ws)
    for ws in disconnected:
        active_websockets.discard(ws)

# Register tick broadcast hook
coordinator.add_delta_callback(broadcast_tick_delta)


# -----------------------------------------------------------------------------
# REST Request Models
# -----------------------------------------------------------------------------
class ControlRequest(BaseModel):
    action: str
    payload: Optional[Dict[str, Any]] = None

class SnapshotRequest(BaseModel):
    filepath: Optional[str] = None


# -----------------------------------------------------------------------------
# REST Endpoints
# -----------------------------------------------------------------------------
@app.get("/api/city/status")
async def get_city_status() -> Dict[str, Any]:
    """Retrieve high-level simulation state, tick, economy, and metrics."""
    status = coordinator.get_city_status()

    # Enrich with live hardware telemetry
    try:
        mem = SystemMetricsCollector.get_memory_metrics()
        cpu = SystemMetricsCollector.get_cpu_metrics()
        storage = SystemMetricsCollector.get_storage_metrics()
        smoothness = SystemMetricsCollector.calculate_smoothness_index(
            cpu["overall_pct"], mem["free_mb"], storage["free_gb"]
        )
        status["hardware_telemetry"] = {
            "memory": mem,
            "cpu": cpu,
            "storage": storage,
            "smoothness_index": smoothness,
            "optimizer_agents": [a.model_dump() for a in optimizer_agents],
        }
    except Exception:
        pass

    return status

@app.get("/api/hardware")
async def get_hardware_telemetry() -> Dict[str, Any]:
    """Direct real-time hardware telemetry and diagnostics."""
    mem = SystemMetricsCollector.get_memory_metrics()
    cpu = SystemMetricsCollector.get_cpu_metrics()
    storage = SystemMetricsCollector.get_storage_metrics()
    smoothness = SystemMetricsCollector.calculate_smoothness_index(
        cpu["overall_pct"], mem["free_mb"], storage["free_gb"]
    )
    return {
        "memory": mem,
        "cpu": cpu,
        "storage": storage,
        "smoothness_index": smoothness,
        "top_processes": SystemMetricsCollector.get_top_processes(8),
        "optimizer_agents": [a.model_dump() for a in optimizer_agents],
    }

@app.get("/api/agents")
async def get_agents() -> List[Dict[str, Any]]:
    """Retrieve full list of active civic agents and subagents."""
    result: List[Dict[str, Any]] = []
    for a_id, agent in coordinator.agents.items():
        pos = coordinator.grid.find_agent_pos(a_id) or (0, 0)
        ledger = coordinator.economy.get_ledger(a_id)
        role = getattr(agent, "role", "CITIZEN")
        if hasattr(role, "value"):
            role = role.value
        state = getattr(agent, "state", "IDLE")
        if hasattr(state, "value"):
            state = state.value

        agent_data = {
            "id": a_id,
            "name": getattr(agent, "name", a_id),
            "role": str(role),
            "state": str(state),
            "x": pos[0],
            "y": pos[1],
            "energy": ledger.energy if ledger else 100.0,
            "funds": ledger.funds if ledger else 0.0,
            "materials": ledger.materials if ledger else 0.0,
            "parent_id": getattr(agent, "parent_id", None),
            "child_ids": list(getattr(agent, "child_ids", [])),
            "is_subagent": getattr(agent, "is_subagent", False),
        }
        result.append(agent_data)
    return result

@app.get("/api/agents/{agent_id}")
async def get_agent_detail(agent_id: str) -> Dict[str, Any]:
    """Retrieve detailed state, traits, and memory for a specific agent."""
    if agent_id not in coordinator.agents:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found.")
    
    agent = coordinator.agents[agent_id]
    pos = coordinator.grid.find_agent_pos(agent_id) or (0, 0)
    ledger = coordinator.economy.get_ledger(agent_id)
    role = getattr(agent, "role", "CITIZEN")
    role_str = role.value if hasattr(role, "value") else str(role)
    state = getattr(agent, "state", "IDLE")
    state_str = state.value if hasattr(state, "value") else str(state)

    traits_data = {}
    if hasattr(agent, "traits"):
        if hasattr(agent.traits, "model_dump"):
            traits_data = agent.traits.model_dump()
        elif hasattr(agent.traits, "to_dict"):
            traits_data = agent.traits.to_dict()

    return {
        "id": agent_id,
        "name": getattr(agent, "name", agent_id),
        "role": role_str,
        "state": state_str,
        "x": pos[0],
        "y": pos[1],
        "energy": ledger.energy if ledger else 100.0,
        "funds": ledger.funds if ledger else 0.0,
        "materials": ledger.materials if ledger else 0.0,
        "traits": traits_data,
        "parent_id": getattr(agent, "parent_id", None),
        "child_ids": list(getattr(agent, "child_ids", [])),
        "is_subagent": getattr(agent, "is_subagent", False),
    }

@app.get("/api/buildings")
async def get_buildings() -> List[Dict[str, Any]]:
    """Retrieve all physical structures and zoning on the grid."""
    buildings: List[Dict[str, Any]] = []
    for row in coordinator.grid._grid:
        for parcel in row:
            if parcel.building_id:
                buildings.append({
                    "id": parcel.building_id,
                    "type": parcel.building_type or "COMMERCIAL",
                    "x": parcel.x,
                    "y": parcel.y,
                    "tier": parcel.building_tier,
                    "zone": parcel.zone.value if hasattr(parcel.zone, "value") else str(parcel.zone),
                    "owner_id": parcel.owner_id,
                })
    return buildings

@app.get("/api/events")
async def get_events(limit: int = 50) -> List[Dict[str, Any]]:
    """Retrieve audit log of active and historical simulation events."""
    return list(coordinator.active_events)[-limit:]

@app.post("/api/controls")
async def post_controls(req: ControlRequest) -> Dict[str, Any]:
    """Execute operational control actions and laptop optimizations."""
    action_upper = req.action.upper()
    valid_actions = {
        "PAUSE", "RESUME", "STEP", "SET_SPEED", "TRIGGER_EVENT",
        "BOOST_MEMORY", "TRIM_MEMORY", "PURGE_STORAGE", "FULL_OPTIMIZE", "TRIM_PID"
    }
    if action_upper not in valid_actions:
        raise HTTPException(status_code=400, detail=f"Invalid action '{req.action}'. Allowed: {valid_actions}")

    payload = req.payload or {}
    opt_result = {}

    if action_upper == "PAUSE":
        coordinator.state = SimulationState.PAUSED
    elif action_upper == "RESUME":
        coordinator.state = SimulationState.RUNNING
    elif action_upper == "STEP":
        await coordinator.step()
    elif action_upper == "SET_SPEED":
        tps = float(payload.get("tps", coordinator.config.default_tps))
        coordinator.set_speed(tps)
    elif action_upper == "TRIGGER_EVENT":
        event_name = payload.get("event", "RESOURCE_WINDFALL")
        title = payload.get("title", f"Civic Event: {event_name}")
        desc = payload.get("description", "A major event has impacted the city.")
        coordinator.trigger_event(event_name, title, desc, payload)
    
    # Real Laptop Optimization Actions
    elif action_upper == "TRIM_PID":
        pid = int(payload.get("pid", 0))
        opt_result = SystemMetricsCollector.trim_process_by_pid(pid)
        coordinator.trigger_event(
            "PROCESS_TRIMMED",
            f"Process Trimming (PID {pid})",
            f"Flushed physical working set for PID {pid}.",
        )
    elif action_upper in ("BOOST_MEMORY", "TRIM_MEMORY"):
        opt_result = SystemMetricsCollector.trim_all_working_sets()
        coordinator.trigger_event(
            "MEMORY_OPTIMIZED",
            "Working Set Relief",
            f"Flushed {opt_result.get('freed_mb', 0)} MB from {opt_result.get('trimmed_processes', 0)} processes.",
        )
    elif action_upper == "PURGE_STORAGE":
        opt_result = SystemMetricsCollector.purge_temp_storage()
        coordinator.trigger_event(
            "STORAGE_RECLAIMED",
            "Storage Sweep & SSD TRIM",
            f"Cleaned {opt_result.get('cleaned_files', 0)} files (+{opt_result.get('reclaimed_mb', 0)} MB) & re-trimmed Drive C:.",
        )
    elif action_upper == "FULL_OPTIMIZE":
        mem_res = SystemMetricsCollector.trim_all_working_sets()
        store_res = SystemMetricsCollector.purge_temp_storage()
        opt_result = {
            "memory": mem_res,
            "storage": store_res,
        }
        coordinator.trigger_event(
            "FULL_OPTIMIZATION",
            "Full Laptop Optimization",
            f"Recovered {mem_res.get('freed_mb', 0)} MB RAM & {store_res.get('reclaimed_mb', 0)} MB disk space.",
        )

    return {
        "status": "ok",
        "action": action_upper,
        "state": coordinator.state.value if hasattr(coordinator.state, "value") else str(coordinator.state),
        "tps": coordinator.tps,
        "tick": coordinator.current_tick,
        "optimization_result": opt_result,
    }

@app.post("/api/snapshot/save")
async def save_snapshot(req: Optional[SnapshotRequest] = None) -> Dict[str, Any]:
    """Persist current simulation state to disk snapshot."""
    filepath = (req and req.filepath) or "city_snapshot.json"
    data = coordinator.to_dict()
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return {"status": "ok", "saved_to": filepath, "tick": coordinator.current_tick}

@app.post("/api/snapshot/load")
async def load_snapshot(req: Optional[SnapshotRequest] = None) -> Dict[str, Any]:
    """Restore simulation state from disk snapshot."""
    global coordinator
    filepath = (req and req.filepath) or "city_snapshot.json"
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail=f"Snapshot file '{filepath}' not found.")
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    coordinator = SimulationCoordinator.from_dict(data)
    coordinator.add_delta_callback(broadcast_tick_delta)
    return {"status": "ok", "loaded_from": filepath, "tick": coordinator.current_tick}


# -----------------------------------------------------------------------------
# WebSocket Streaming Protocol
# -----------------------------------------------------------------------------
@app.websocket("/ws")
async def websocket_stream(websocket: WebSocket) -> None:
    """Bidirectional WebSocket connection for live tick delta streaming."""
    await websocket.accept()
    active_websockets.add(websocket)

    try:
        # 1. Dispatch immediate INIT_STATE frame
        init_frame = coordinator.get_init_state()
        try:
            mem = SystemMetricsCollector.get_memory_metrics()
            cpu = SystemMetricsCollector.get_cpu_metrics()
            storage = SystemMetricsCollector.get_storage_metrics()
            init_frame["hardware_telemetry"] = {
                "memory": mem,
                "cpu": cpu,
                "storage": storage,
                "smoothness_index": SystemMetricsCollector.calculate_smoothness_index(
                    cpu["overall_pct"], mem["free_mb"], storage["free_gb"]
                ),
                "top_processes": SystemMetricsCollector.get_top_processes(8),
                "optimizer_agents": [a.model_dump() for a in optimizer_agents],
            }
        except Exception:
            pass

        await websocket.send_json(init_frame)

        # 2. Inbound message loop for client control actions
        while True:
            raw_text = await websocket.receive_text()
            try:
                msg = json.loads(raw_text)
                msg_type = msg.get("type", "").upper()
                if msg_type in ("CONTROL_ACTION", "CONTROL"):
                    action = msg.get("action", "")
                    payload = msg.get("payload", {})
                    await post_controls(ControlRequest(action=action, payload=payload))
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        pass
    finally:
        active_websockets.discard(websocket)


# -----------------------------------------------------------------------------
# Static Frontend Serving
# -----------------------------------------------------------------------------
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    @app.get("/", response_class=FileResponse)
    async def serve_index() -> FileResponse:
        return FileResponse(static_dir / "index.html")
else:
    @app.get("/", response_class=HTMLResponse)
    async def serve_fallback() -> str:
        return """
        <!DOCTYPE html>
        <html>
        <head><title>Agent Metropolis</title></head>
        <body>
            <h1>Agent Metropolis - Laptop Optimizer City</h1>
            <p>API Status: <a href="/api/city/status">/api/city/status</a></p>
            <p>Live Hardware: <a href="/api/hardware">/api/hardware</a></p>
        </body>
        </html>
        """
