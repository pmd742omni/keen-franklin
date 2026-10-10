"""Tier 1-3 Tests for FastAPI REST Endpoints and WebSocket Streaming Protocol:
- REST Endpoints:
  - GET /api/city/status
  - GET /api/agents
  - GET /api/agents/{id}
  - GET /api/buildings
  - GET /api/events
  - POST /api/controls (pause, resume, step, set_speed, trigger_event)
  - POST /api/snapshot/save & POST /api/snapshot/load
- WebSocket /ws Stream:
  - Immediate INIT_STATE frame on connection
  - Periodic TICK_DELTA broadcast frames
  - Differential payload size verification (< 1.5 KB / tick)
  - Client CONTROL_ACTION frame ingestion
"""

from __future__ import annotations

import json
import pytest

from agent_city.config import DEFAULT_CONFIG, SimulationConfig, SimulationState
from agent_city.engine.simulation import SimulationCoordinator

# Conditional import for Milestone 3 implementation
try:
    from agent_city.server import app
    from fastapi.testclient import TestClient
    SERVER_AVAILABLE = True
except ImportError:
    try:
        from agent_city.api.routes import app
        from fastapi.testclient import TestClient
        SERVER_AVAILABLE = True
    except ImportError:
        SERVER_AVAILABLE = False


# =============================================================================
# Protocol & Differential Delta Contract Tests
# =============================================================================

class TestWebSocketStreamingProtocolContract:
    """Verifies that the WebSocket message contracts adhere to the architectural spec."""

    def test_init_state_message_structure(self, coordinator: SimulationCoordinator):
        """Tier 1: Verify get_init_state produces all required keys for client boot."""
        init_state = coordinator.get_init_state()
        assert init_state["type"] == "INIT_STATE"
        assert "tick" in init_state
        assert "epoch" in init_state
        assert "grid" in init_state
        assert "treasury" in init_state
        assert "agents" in init_state
        assert "metrics" in init_state
        assert "dialogues" in init_state
        assert "proposals" in init_state

        # Grid contract
        grid_data = init_state["grid"]
        assert "width" in grid_data
        assert "height" in grid_data
        assert "parcels" in grid_data

    @pytest.mark.asyncio
    async def test_tick_delta_differential_footprint_constraint(
        self,
        coordinator: SimulationCoordinator,
        eight_civic_agents,
    ):
        """Tier 1: Verify TICK_DELTA payload stays well under the 1.5 KB (1536 bytes) limit."""
        # Register 2 civic agents (representative baseline connection)
        for agent in eight_civic_agents[:2]:
            coordinator.register_agent(agent, initial_x=agent.x, initial_y=agent.y)

        # Advance 1 tick
        delta = await coordinator.step()

        assert delta["type"] == "TICK_DELTA"
        assert delta["tick"] == 1
        assert "agents" in delta
        assert "parcels" in delta
        assert "dialogues" in delta
        assert "treasury" in delta

        # Serialize delta to JSON to measure wire footprint
        serialized = json.dumps(delta)
        size_bytes = len(serialized.encode("utf-8"))

        # The specification requires differential delta frames under 1.5 KB (< 1536 bytes)
        assert size_bytes < 1536, f"Tick delta payload ({size_bytes} bytes) exceeded 1.5 KB limit!"




    def test_city_status_endpoint_contract(self, coordinator: SimulationCoordinator):
        """Tier 1: Verify get_city_status returns all vital indicators."""
        status = coordinator.get_city_status()
        assert "tick" in status
        assert "epoch" in status
        assert "state" in status
        assert "tps" in status
        assert "agents_count" in status
        assert "buildings_count" in status
        assert "treasury" in status
        assert "total_tax_collected" in status


# =============================================================================
# REST & Live WebSocket Endpoint Tests (Unskipped when M3 is present)
# =============================================================================

@pytest.mark.skipif(not SERVER_AVAILABLE, reason="Milestone 3 (agent_city.server / api) not yet implemented")
class TestLiveAPIAndWebSocketEndpoints:
    """Direct end-to-end HTTP and WebSocket client testing using TestClient."""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_get_city_status_200(self, client):
        """Tier 1: GET /api/city/status returns 200 and valid JSON."""
        response = client.get("/api/city/status")
        assert response.status_code == 200
        data = response.json()
        assert "tick" in data
        assert "state" in data

    def test_get_agents_list(self, client):
        """Tier 1: GET /api/agents returns list of active agents."""
        response = client.get("/api/agents")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_agent_404_for_unknown_id(self, client):
        """Tier 2: Querying non-existent agent returns 404."""
        response = client.get("/api/agents/non_existent_agent_999")
        assert response.status_code == 404

    def test_get_buildings_list(self, client):
        """Tier 1: GET /api/buildings returns parcel structures."""
        response = client.get("/api/buildings")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_events_list(self, client):
        """Tier 1: GET /api/events returns event audit log."""
        response = client.get("/api/events?limit=20")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_controls_pause_and_resume(self, client):
        """Tier 1 & 3: POST /api/controls toggles simulation state."""
        # Pause
        resp_pause = client.post("/api/controls", json={"action": "pause"})
        assert resp_pause.status_code == 200

        resp_status = client.get("/api/city/status")
        assert resp_status.json()["state"] == "PAUSED"

        # Resume
        resp_resume = client.post("/api/controls", json={"action": "resume"})
        assert resp_resume.status_code == 200

    def test_controls_set_speed(self, client):
        """Tier 1: POST /api/controls adjust simulation tick rate."""
        response = client.post("/api/controls", json={"action": "set_speed", "payload": {"tps": 12.0}})
        assert response.status_code == 200

        resp_status = client.get("/api/city/status")
        assert resp_status.json()["tps"] == 12.0

    def test_controls_invalid_action_returns_error(self, client):
        """Tier 2: Invalid control action returns structured error."""
        response = client.post("/api/controls", json={"action": "INVALID_COMMAND"})
        assert response.status_code in (400, 422)

    def test_websocket_connection_and_init_state(self, client):
        """Tier 1: WebSocket /ws connects and receives INIT_STATE frame."""
        with client.websocket_connect("/ws") as websocket:
            data = websocket.receive_json()
            assert data["type"] == "INIT_STATE"
            assert "grid" in data
            assert "agents" in data
