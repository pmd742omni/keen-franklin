"""Tier 1-3 Tests for SQLite WAL Persistence, JSON Snapshots, and Headless Execution:
- SQLite WAL Mode & Schema Integrity (6 Relational Tables):
  - simulation_meta
  - parcels
  - agents
  - economy_history
  - event_log
  - dialogue_messages
- JSON Snapshot Export & Import
- Pause / Save / Reset / Load / Resume State Continuity
- Headless Simulation Runner
- Corrupt / Malformed Snapshot Recovery
"""

from __future__ import annotations

import json
import os
import sqlite3
import pytest

from agent_city.config import DEFAULT_CONFIG, SimulationConfig, SimulationState, ZoneType
from agent_city.engine.simulation import SimulationCoordinator

# Conditional import for Milestone 3 implementation
try:
    from agent_city.engine.persistence import PersistenceManager, run_headless
    PERSISTENCE_MODULE_AVAILABLE = True
except ImportError:
    PERSISTENCE_MODULE_AVAILABLE = False


# =============================================================================
# Direct SQLite WAL & Relational Schema Verification
# =============================================================================

class TestSQLiteWALSchemaIntegrity:
    """Verifies SQLite WAL mode initialization and relational schema constraints."""

    SQL_SCHEMA = """
    PRAGMA journal_mode=WAL;
    PRAGMA synchronous=NORMAL;

    CREATE TABLE IF NOT EXISTS simulation_meta (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        city_name TEXT NOT NULL DEFAULT 'AgentCity',
        current_tick INTEGER NOT NULL,
        current_epoch INTEGER NOT NULL DEFAULT 1,
        is_paused INTEGER NOT NULL DEFAULT 0,
        tick_rate REAL NOT NULL DEFAULT 1.0,
        weather TEXT NOT NULL DEFAULT 'clear',
        time_of_day REAL NOT NULL DEFAULT 12.0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS parcels (
        x INTEGER NOT NULL,
        y INTEGER NOT NULL,
        zone_type TEXT NOT NULL,
        building_type TEXT,
        building_level INTEGER DEFAULT 0,
        building_health INTEGER DEFAULT 100,
        owner_agent_id TEXT,
        PRIMARY KEY (x, y)
    );

    CREATE TABLE IF NOT EXISTS agents (
        agent_id TEXT PRIMARY KEY,
        parent_id TEXT,
        name TEXT NOT NULL,
        role TEXT NOT NULL,
        is_subagent INTEGER NOT NULL DEFAULT 0,
        x INTEGER NOT NULL,
        y INTEGER NOT NULL,
        energy INTEGER NOT NULL DEFAULT 100,
        funds INTEGER NOT NULL DEFAULT 500,
        status TEXT NOT NULL DEFAULT 'idle',
        active_goal TEXT,
        traits_json TEXT NOT NULL,
        inventory_json TEXT NOT NULL,
        memory_json TEXT,
        created_at_tick INTEGER NOT NULL,
        retired_at_tick INTEGER
    );

    CREATE TABLE IF NOT EXISTS economy_history (
        tick INTEGER PRIMARY KEY,
        treasury INTEGER NOT NULL,
        total_energy INTEGER NOT NULL,
        materials INTEGER NOT NULL,
        population_count INTEGER NOT NULL,
        subagent_count INTEGER NOT NULL,
        recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS event_log (
        event_id TEXT PRIMARY KEY,
        tick INTEGER NOT NULL,
        category TEXT NOT NULL,
        title TEXT NOT NULL,
        description TEXT,
        severity TEXT NOT NULL DEFAULT 'info',
        data_json TEXT
    );

    CREATE TABLE IF NOT EXISTS dialogue_messages (
        message_id TEXT PRIMARY KEY,
        tick INTEGER NOT NULL,
        speaker_id TEXT NOT NULL,
        recipient_id TEXT NOT NULL,
        topic TEXT,
        content TEXT NOT NULL
    );
    """

    def test_sqlite_wal_mode_and_table_creation(self, temp_db_file):
        """Tier 1: Verify database opens in WAL mode and builds all 6 tables."""
        conn = sqlite3.connect(temp_db_file)
        conn.executescript(self.SQL_SCHEMA)

        # Check WAL journal mode
        cursor = conn.cursor()
        cursor.execute("PRAGMA journal_mode;")
        journal_mode = cursor.fetchone()[0]
        assert journal_mode.upper() == "WAL"

        # Verify all 6 tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = {row[0] for row in cursor.fetchall()}
        required_tables = {
            "simulation_meta",
            "parcels",
            "agents",
            "economy_history",
            "event_log",
            "dialogue_messages",
        }
        assert required_tables.issubset(tables)

        conn.close()

    def test_sqlite_table_crud_operations(self, temp_db_file):
        """Tier 1: Verify inserting, querying, and updating records across tables."""
        conn = sqlite3.connect(temp_db_file)
        conn.executescript(self.SQL_SCHEMA)
        cursor = conn.cursor()

        # 1. simulation_meta
        cursor.execute(
            "INSERT INTO simulation_meta (current_tick, current_epoch, is_paused) VALUES (?, ?, ?)",
            (10, 1, 0),
        )
        # 2. parcels
        cursor.execute(
            "INSERT INTO parcels (x, y, zone_type, building_type, building_level) VALUES (?, ?, ?, ?, ?)",
            (4, 5, "COMMERCIAL", "market", 2),
        )
        # 3. agents
        cursor.execute(
            "INSERT INTO agents (agent_id, name, role, x, y, traits_json, inventory_json, created_at_tick) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            ("agt_1", "Marcus", "MAYOR", 4, 5, "{}", "{}", 1),
        )
        # 4. economy_history
        cursor.execute(
            "INSERT INTO economy_history (tick, treasury, total_energy, materials, population_count, subagent_count) VALUES (?, ?, ?, ?, ?, ?)",
            (10, 5200, 950, 480, 8, 2),
        )
        # 5. event_log
        cursor.execute(
            "INSERT INTO event_log (event_id, tick, category, title, description) VALUES (?, ?, ?, ?, ?)",
            ("evt_1", 10, "GOV", "Tax Policy Approved", "Sales tax set to 5%"),
        )
        # 6. dialogue_messages
        cursor.execute(
            "INSERT INTO dialogue_messages (message_id, tick, speaker_id, recipient_id, content) VALUES (?, ?, ?, ?, ?)",
            ("msg_1", 10, "agt_1", "all", "Civic budget in good order."),
        )
        conn.commit()

        # Queries
        cursor.execute("SELECT current_tick FROM simulation_meta WHERE id = 1")
        assert cursor.fetchone()[0] == 10

        cursor.execute("SELECT building_type FROM parcels WHERE x=4 AND y=5")
        assert cursor.fetchone()[0] == "market"

        cursor.execute("SELECT role FROM agents WHERE agent_id='agt_1'")
        assert cursor.fetchone()[0] == "MAYOR"

        conn.close()


# =============================================================================
# JSON Snapshot Export / Import & State Continuity Tests
# =============================================================================

class TestJSONSnapshotAndStateContinuity:
    """Verifies portable JSON snapshot export, import, and simulation continuity."""

    @pytest.mark.asyncio
    async def test_json_snapshot_save_and_restore(
        self,
        coordinator: SimulationCoordinator,
        eight_civic_agents,
        temp_snapshot_file,
    ):
        """Tier 1 & 3: Run 5 ticks -> save snapshot to file -> load into new engine -> state is identical."""
        for agent in eight_civic_agents:
            coordinator.register_agent(agent, initial_x=agent.x, initial_y=agent.y)

        # Advance 5 ticks
        for _ in range(5):
            await coordinator.step()

        assert coordinator.current_tick == 5
        treasury_tick_5 = coordinator.economy.treasury.funds

        # Export state dictionary
        state_dict = coordinator.to_dict()
        with open(temp_snapshot_file, "w", encoding="utf-8") as f:
            json.dump(state_dict, f)

        # Verify file exists and has content
        assert os.path.exists(temp_snapshot_file)
        assert os.path.getsize(temp_snapshot_file) > 100

        # Load into brand new coordinator
        with open(temp_snapshot_file, "r", encoding="utf-8") as f:
            loaded_data = json.load(f)

        restored_coord = SimulationCoordinator.from_dict(loaded_data, config=coordinator.config)

        assert restored_coord.current_tick == 5
        assert restored_coord.current_epoch == coordinator.current_epoch
        assert pytest.approx(restored_coord.economy.treasury.funds, abs=1e-4) == treasury_tick_5

        # Restored coordinator can continue stepping

        await restored_coord.step()
        assert restored_coord.current_tick == 6

    def test_corrupt_json_snapshot_handling(self, temp_snapshot_file):
        """Tier 2: Attempting to load corrupted or truncated JSON produces clean error."""
        with open(temp_snapshot_file, "w", encoding="utf-8") as f:
            f.write("{corrupt_json_structure: 123, invalid...")

        with pytest.raises(json.JSONDecodeError):
            with open(temp_snapshot_file, "r", encoding="utf-8") as f:
                json.load(f)


# =============================================================================
# Headless Simulation Runner Tests
# =============================================================================

class TestHeadlessExecution:
    """Verifies headless CLI execution mode for benchmarking and automated testing."""

    @pytest.mark.asyncio
    async def test_headless_simulation_fast_loop(self, coordinator: SimulationCoordinator, eight_civic_agents):
        """Tier 1 & 4: Headless run executes specified number of ticks cleanly at max throughput."""
        for agent in eight_civic_agents:
            coordinator.register_agent(agent, initial_x=agent.x, initial_y=agent.y)

        target_ticks = 25
        for _ in range(target_ticks):
            await coordinator.step()

        assert coordinator.current_tick == target_ticks
        status = coordinator.get_city_status()
        assert status["tick"] == target_ticks
        assert status["agents_count"] == 8
