#!/usr/bin/env python3
"""
Silicon Sanctuary — Autonomous Context Management Engine
Location: .agents/context/context_manager.py
Zero-external-dependency SQLite context and memory broker for multi-agent evolution.
"""

import os
import sqlite3
import json
import time
from datetime import datetime
from pathlib import Path

DB_DIR = Path(__file__).parent
DB_PATH = DB_DIR / "sanctuary_context.db"

def get_connection():
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    """Initializes the relational context database schemas."""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # 1. Timeline & Epochs Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS epochs (
                epoch_id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                phase TEXT NOT NULL,
                started_at TEXT NOT NULL,
                completed_at TEXT,
                status TEXT NOT NULL DEFAULT 'pending',
                deliverables_json TEXT,
                summary TEXT
            );
        """)

        # 2. Benchmark Telemetry Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS benchmarks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                epoch_id INTEGER,
                metric_name TEXT NOT NULL,
                value_numeric REAL NOT NULL,
                unit TEXT NOT NULL,
                notes TEXT
            );
        """)

        # 3. Rate Limit & Context Health Meter
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rate_limits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                tokens_used INTEGER,
                tokens_headroom_pct REAL,
                step_index INTEGER,
                rate_limit_state TEXT NOT NULL,
                notes TEXT
            );
        """)

        # 4. Multi-Agent Memory & Deliberation Log
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                agent_name TEXT NOT NULL,
                memory_type TEXT NOT NULL,
                key TEXT NOT NULL,
                content_json TEXT NOT NULL
            );
        """)

        # 5. Evolution Artifact Registry
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS artifacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                epoch_id INTEGER,
                artifact_name TEXT NOT NULL,
                artifact_type TEXT NOT NULL,
                file_path TEXT NOT NULL,
                file_size_bytes INTEGER,
                metadata_json TEXT
            );
        """)

        conn.commit()

class ContextManager:
    """High-level Python API for managing persistent evolution context."""

    def __init__(self, db_path=None):
        self.db_path = db_path or DB_PATH
        init_database()

    def record_epoch(self, epoch_id, title, phase, status="active", deliverables=None, summary=""):
        with get_connection() as conn:
            cursor = conn.cursor()
            now = datetime.now().isoformat()
            cursor.execute("""
                INSERT INTO epochs (epoch_id, title, phase, started_at, status, deliverables_json, summary)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(epoch_id) DO UPDATE SET
                    title=excluded.title,
                    phase=excluded.phase,
                    status=excluded.status,
                    deliverables_json=excluded.deliverables_json,
                    summary=excluded.summary;
            """, (epoch_id, title, phase, now, status, json.dumps(deliverables or []), summary))
            conn.commit()

    def log_benchmark(self, metric_name, value, unit, epoch_id=None, notes=""):
        with get_connection() as conn:
            cursor = conn.cursor()
            now = datetime.now().isoformat()
            cursor.execute("""
                INSERT INTO benchmarks (timestamp, epoch_id, metric_name, value_numeric, unit, notes)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (now, epoch_id, metric_name, float(value), unit, notes))
            conn.commit()

    def log_rate_limit(self, tokens_used=0, headroom_pct=100.0, step_index=0, state="healthy", notes=""):
        with get_connection() as conn:
            cursor = conn.cursor()
            now = datetime.now().isoformat()
            cursor.execute("""
                INSERT INTO rate_limits (timestamp, tokens_used, tokens_headroom_pct, step_index, rate_limit_state, notes)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (now, tokens_used, headroom_pct, step_index, state, notes))
            conn.commit()

    def save_memory(self, agent_name, memory_type, key, content):
        with get_connection() as conn:
            cursor = conn.cursor()
            now = datetime.now().isoformat()
            content_str = json.dumps(content) if isinstance(content, (dict, list)) else str(content)
            cursor.execute("""
                INSERT INTO agent_memories (timestamp, agent_name, memory_type, key, content_json)
                VALUES (?, ?, ?, ?, ?)
            """, (now, agent_name, memory_type, key, content_str))
            conn.commit()

    def register_artifact(self, artifact_name, artifact_type, file_path, epoch_id=None, metadata=None):
        path_obj = Path(file_path)
        size = path_obj.stat().st_size if path_obj.exists() else 0
        with get_connection() as conn:
            cursor = conn.cursor()
            now = datetime.now().isoformat()
            cursor.execute("""
                INSERT INTO artifacts (timestamp, epoch_id, artifact_name, artifact_type, file_path, file_size_bytes, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (now, epoch_id, artifact_name, artifact_type, str(file_path), size, json.dumps(metadata or {})))
            conn.commit()

    def get_summary(self):
        with get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM epochs")
            total_epochs = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM benchmarks")
            total_benchmarks = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM agent_memories")
            total_memories = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM artifacts")
            total_artifacts = cursor.fetchone()[0]

            cursor.execute("SELECT * FROM benchmarks ORDER BY id DESC LIMIT 10")
            recent_benchmarks = [dict(r) for r in cursor.fetchall()]

            cursor.execute("SELECT * FROM artifacts ORDER BY id DESC LIMIT 10")
            recent_artifacts = [dict(r) for r in cursor.fetchall()]

            cursor.execute("SELECT * FROM epochs WHERE status = 'active' ORDER BY epoch_id DESC LIMIT 1")
            active_epoch = cursor.fetchone()

            return {
                "database_path": str(self.db_path),
                "counts": {
                    "epochs": total_epochs,
                    "benchmarks": total_benchmarks,
                    "memories": total_memories,
                    "artifacts": total_artifacts,
                },
                "active_epoch": dict(active_epoch) if active_epoch else None,
                "recent_benchmarks": recent_benchmarks,
                "recent_artifacts": recent_artifacts,
            }

    def get_benchmarks(self, limit=50):
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM benchmarks ORDER BY id DESC LIMIT ?", (limit,))
            return [dict(r) for r in cursor.fetchall()]

if __name__ == "__main__":
    cm = ContextManager()
    # Seed baseline epoch and benchmarks
    cm.record_epoch(0, "Polyglot Native Core Genesis", "Genesis", status="completed", summary="C-Kernel, Rust Sentinel, Java Bridge compiled and tested.")
    cm.record_epoch(1, "Topography Refinement & Botanical Sculpting Pass 2", "Refinement", status="active", summary="Volumetric Sakura cloud canopy and Ginkgo 16.0, 10.5 relocation.")
    cm.log_benchmark("RAM Reclaimed (C-Kernel)", 3859.75, "MB", epoch_id=0, notes="Win32 psapi K32EmptyWorkingSet compaction")
    cm.log_benchmark("Compaction Latency", 3398.77, "ms", epoch_id=0, notes="Scanned 297 processes, trimmed 129")
    cm.log_rate_limit(tokens_used=125000, headroom_pct=88.5, state="nominal", notes="Session operating within healthy window")
    cm.register_artifact("screenshot_grove_v5.png", "screenshot", "agent_city/screenshot_grove_v5.png", epoch_id=0)
    cm.register_artifact("screenshot_grove_v6.png", "screenshot", "agent_city/screenshot_grove_v6.png", epoch_id=1)
    cm.register_artifact("screenshot_grove_v7.png", "screenshot", "agent_city/screenshot_grove_v7.png", epoch_id=1)
    print("Context database initialized and seeded successfully.")
    print(json.dumps(cm.get_summary(), indent=2))
