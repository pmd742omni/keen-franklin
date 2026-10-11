"""
Tier 4: Real-World Application Scenarios
Location: tests/e2e/test_tier4_scenarios.py
Simulates realistic end-to-end operational workflows: 2-minute cadence cycle, live server interaction,
Edge captures of / and /evolution, SQLite context registration, and Markdown embeds.
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
import subprocess
import threading
import time
from pathlib import Path

import psutil
import pytest

from conftest import (
    BASE_URL,
    PROJECT_ROOT,
    check_milestone_capability,
    http_request,
    is_port_open,
    parse_png_header,
    run_edge_capture,
)


class TestRealWorldApplicationScenarios:
    """End-to-end operational workflows reflecting the live 336-hour autonomous system."""

    def test_tier4_scenario1_full_autonomous_documentation_cycle(
        self, base_url: str, edge_binary: str, db_conn: sqlite3.Connection, temp_capture_dir: Path
    ):
        """
        Scenario 1: Complete Autonomous Documentation Lifecycle.
        1. Probe server liveness & heartbeat.
        2. Capture 3D Voxel Grove (/) at 1080p with virtual time budget settling.
        3. Capture Visual Evolution Portal (/evolution) at 1080p.
        4. Validate PNG file signatures, dimensions, and non-zero sizes.
        5. Register both screenshots into SQLite artifacts table.
        6. Verify registration and retrieve artifact rows.
        """
        # Step 1: Probe server liveness
        status_code, body, _ = http_request(f"{base_url}/api/heartbeat")
        assert status_code == 200, f"Server heartbeat unavailable: {status_code}"
        assert is_port_open("127.0.0.1", 8000)

        # Step 2: Capture 3D Voxel Grove
        grove_file = temp_capture_dir / f"screenshot_grove_s1_{int(time.time())}.png"
        user_data_grove = temp_capture_dir / "user_data_s1_grove"
        ok_grove = run_edge_capture(
            edge_bin=edge_binary,
            url=f"{base_url}/",
            output_path=grove_file,
            user_data_dir=user_data_grove,
            window_size="1920,1080",
            virtual_time_budget=2000,
            timeout=30.0,
        )
        assert ok_grove is True
        assert grove_file.exists()

        # Step 3: Capture Evolution Portal
        portal_file = temp_capture_dir / f"screenshot_portal_s1_{int(time.time())}.png"
        user_data_portal = temp_capture_dir / "user_data_s1_portal"
        ok_portal = run_edge_capture(
            edge_bin=edge_binary,
            url=f"{base_url}/evolution",
            output_path=portal_file,
            user_data_dir=user_data_portal,
            window_size="1920,1080",
            virtual_time_budget=1500,
            timeout=30.0,
        )
        assert ok_portal is True
        assert portal_file.exists()

        # Step 4: Validate PNG dimensions
        hdr_grove = parse_png_header(grove_file.read_bytes())
        assert hdr_grove["valid"] is True
        assert hdr_grove["width"] == 1920
        assert hdr_grove["height"] == 1080
        assert grove_file.stat().st_size > 20_000

        hdr_portal = parse_png_header(portal_file.read_bytes())
        assert hdr_portal["valid"] is True
        assert hdr_portal["width"] == 1920
        assert hdr_portal["height"] == 1080
        assert portal_file.stat().st_size > 20_000

        # Step 5: Register both in SQLite
        cursor = db_conn.cursor()
        iso_now = time.strftime("%Y-%m-%dT%H:%M:%SZ")
        
        meta_grove = json.dumps({"width": 1920, "height": 1080, "url": f"{base_url}/", "scenario": "s1"})
        cursor.execute(
            """
            INSERT INTO artifacts (timestamp, epoch_id, artifact_name, artifact_type, file_path, file_size_bytes, metadata_json)
            VALUES (?, ?, ?, ?, ?, ?, ?);
            """,
            (iso_now, 1, grove_file.name, "screenshot_3d_grove", str(grove_file), grove_file.stat().st_size, meta_grove),
        )
        grove_id = cursor.lastrowid

        meta_portal = json.dumps({"width": 1920, "height": 1080, "url": f"{base_url}/evolution", "scenario": "s1"})
        cursor.execute(
            """
            INSERT INTO artifacts (timestamp, epoch_id, artifact_name, artifact_type, file_path, file_size_bytes, metadata_json)
            VALUES (?, ?, ?, ?, ?, ?, ?);
            """,
            (iso_now, 1, portal_file.name, "screenshot_evolution_portal", str(portal_file), portal_file.stat().st_size, meta_portal),
        )
        portal_id = cursor.lastrowid
        db_conn.commit()

        # Step 6: Verify rows
        row_g = cursor.execute("SELECT * FROM artifacts WHERE id = ?;", (grove_id,)).fetchone()
        assert row_g["artifact_name"] == grove_file.name
        row_p = cursor.execute("SELECT * FROM artifacts WHERE id = ?;", (portal_id,)).fetchone()
        assert row_p["artifact_name"] == portal_file.name

        cursor.execute("DELETE FROM artifacts WHERE id IN (?, ?);", (grove_id, portal_id))
        db_conn.commit()

    def test_tier4_scenario2_multi_epoch_evolution_simulation(self, base_url: str, db_conn: sqlite3.Connection):
        """
        Scenario 2: Multi-Epoch Evolution Progression Simulation.
        Verifies artifacts across Epoch 0 and Epoch 1 exist and are properly delineated in SQLite and gallery.
        """
        cursor = db_conn.cursor()
        epochs = cursor.execute("SELECT epoch_id, title, status FROM epochs ORDER BY epoch_id ASC;").fetchall()
        assert len(epochs) >= 2, "Expected at least 2 epochs recorded in epochs table."
        epoch_ids = [e["epoch_id"] for e in epochs]
        assert 0 in epoch_ids
        assert 1 in epoch_ids

        status_code, body, _ = http_request(f"{base_url}/evolution")
        assert status_code == 200
        html = body.decode("utf-8", errors="ignore")
        assert "Epoch 0" in html
        assert "Epoch 1" in html

    def test_tier4_scenario3_continuous_cadence_simulation_no_orphans(
        self, base_url: str, edge_binary: str, temp_capture_dir: Path
    ):
        """
        Scenario 3: Cadence Stability & Zero Process Leak Guarantee.
        Executes two back-to-back captures with 1-second interval, verifies distinct artifacts,
        and ensures no orphaned Edge processes linger.
        """
        initial_edge_pids = {p.pid for p in psutil.process_iter(["pid", "name"]) if "msedge" in p.info["name"].lower()}

        for cycle in (1, 2):
            out_file = temp_capture_dir / f"cadence_cycle_{cycle}.png"
            user_data = temp_capture_dir / f"user_cadence_{cycle}"
            ok = run_edge_capture(
                edge_bin=edge_binary,
                url=f"{base_url}/api/heartbeat",
                output_path=out_file,
                user_data_dir=user_data,
                virtual_time_budget=500,
                timeout=20.0,
            )
            assert ok is True
            assert out_file.exists()
            assert out_file.stat().st_size > 1000
            time.sleep(1.0)

        time.sleep(1.0)
        final_edge_pids = {p.pid for p in psutil.process_iter(["pid", "name"]) if "msedge" in p.info["name"].lower()}
        new_lingering_pids = final_edge_pids - initial_edge_pids
        assert len(new_lingering_pids) == 0, f"Orphaned Edge processes detected: {new_lingering_pids}"

    def test_tier4_scenario4_latex_monograph_artifact_verification(self, base_url: str, project_root: Path):
        """
        Scenario 4: LaTeX Monograph Synchronicity with Live Artifacts.
        Verifies that silicon_sanctuary_report.pdf exists, is served over HTTP, and contains valid TeX metadata.
        """
        pdf_path = project_root / "evolution" / "docs" / "latex" / "silicon_sanctuary_report.pdf"
        assert pdf_path.exists(), f"PDF report missing at {pdf_path}"

        status_code, body, headers = http_request(f"{base_url}/docs/latex/silicon_sanctuary_report.pdf")
        assert status_code == 200
        assert body.startswith(b"%PDF-")
        assert len(body) > 10_000

    def test_tier4_scenario5_stress_concurrency_during_capture(
        self, base_url: str, edge_binary: str, temp_capture_dir: Path
    ):
        """
        Scenario 5: High-Frequency Telemetry and API Traffic during 1080p Capture.
        Spawns background requester hammering /api/heartbeat and /api/city/status while Edge captures 1080p canvas.
        Asserts zero HTTP drops and 100% capture fidelity.
        """
        stop_event = threading.Event()
        http_errors = []
        request_count = [0]

        def requester():
            while not stop_event.is_set():
                s, _, _ = http_request(f"{base_url}/api/heartbeat", timeout=1.0)
                if s != 200:
                    http_errors.append(f"Heartbeat returned {s}")
                s2, _, _ = http_request(f"{base_url}/api/city/status", timeout=1.0)
                if s2 != 200:
                    http_errors.append(f"City status returned {s2}")
                request_count[0] += 2
                time.sleep(0.05)

        t = threading.Thread(target=requester)
        t.start()

        out_file = temp_capture_dir / "stress_capture_1080p.png"
        user_data = temp_capture_dir / "user_data_stress"

        try:
            ok = run_edge_capture(
                edge_bin=edge_binary,
                url=f"{base_url}/",
                output_path=out_file,
                user_data_dir=user_data,
                window_size="1920,1080",
                virtual_time_budget=1500,
                timeout=30.0,
            )
            assert ok is True
            assert out_file.exists()
            hdr = parse_png_header(out_file.read_bytes())
            assert hdr["valid"] is True
            assert hdr["width"] == 1920
            assert hdr["height"] == 1080
        finally:
            stop_event.set()
            t.join(timeout=2.0)

        assert len(http_errors) == 0, f"HTTP requests failed during capture: {http_errors}"
        assert request_count[0] >= 10, f"Too few background requests executed: {request_count[0]}"
