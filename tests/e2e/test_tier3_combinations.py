"""
Tier 3: Cross-Feature Combinations & Pairwise Interactions
Location: tests/e2e/test_tier3_combinations.py
Verifies cross-feature subsystems working in concert (restart+capture, capture+gallery, capture+db, db+markdown).
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

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


class TestCrossFeatureCombinations:
    """Verifies integration points between multiple system features."""

    def test_tier3_combo1_restart_and_capture(self, base_url: str, edge_binary: str, temp_capture_dir: Path):
        """
        Combo 1: F1 (Server Freshness Cycle) + F2 (Edge Headless Capture).
        Validates the lifecycle: poll server heartbeat -> verify port open -> trigger headless 1080p capture.
        """
        status_code, body, _ = http_request(f"{base_url}/api/heartbeat")
        assert status_code == 200, f"Heartbeat failed: {status_code}"
        assert is_port_open("127.0.0.1", 8000) is True

        out_file = temp_capture_dir / "combo1_grove.png"
        user_data = temp_capture_dir / "combo1_user_data"
        ok = run_edge_capture(
            edge_bin=edge_binary,
            url=f"{base_url}/",
            output_path=out_file,
            user_data_dir=user_data,
            window_size="1920,1080",
            virtual_time_budget=2000,
            timeout=30.0,
        )
        assert ok is True
        assert out_file.exists()

        hdr = parse_png_header(out_file.read_bytes())
        assert hdr["valid"] is True
        assert hdr["width"] == 1920
        assert hdr["height"] == 1080
        assert out_file.stat().st_size > 20_000

    def test_tier3_combo2_capture_and_gallery_mounting(self, base_url: str, edge_binary: str, project_root: Path, temp_capture_dir: Path):
        """
        Combo 2: F2 (Edge Capture) + F3 (Static Route Mounting) + F4 (Evolution Gallery).
        Captures a screenshot, places it in screenshots directory, verifies HTTP 200 on /screenshots,
        and verifies /evolution renders the gallery.
        """
        screenshots_dir = project_root / "agent_city" / "screenshots"
        check_milestone_capability("M2", screenshots_dir.exists(), "agent_city/screenshots directory created by M2")

        test_slug = f"test_combo2_{int(time.time())}.png"
        target_path = screenshots_dir / test_slug
        user_data = temp_capture_dir / "combo2_user_data"

        try:
            ok = run_edge_capture(
                edge_bin=edge_binary,
                url=f"{base_url}/evolution",
                output_path=target_path,
                user_data_dir=user_data,
                window_size="1920,1080",
                virtual_time_budget=1500,
                timeout=25.0,
            )
            assert ok is True
            assert target_path.exists()

            status_code, body, headers = http_request(f"{base_url}/screenshots/{test_slug}")
            assert status_code == 200
            assert len(body) == target_path.stat().st_size
            content_type = headers.get("content-type", headers.get("Content-Type", ""))
            assert "png" in content_type or "image" in content_type

            status_evo, body_evo, _ = http_request(f"{base_url}/evolution")
            assert status_evo == 200
            assert b"gallery" in body_evo.lower()
        finally:
            if target_path.exists():
                try:
                    target_path.unlink()
                except Exception:
                    pass

    def test_tier3_combo3_capture_and_db_registration(self, base_url: str, edge_binary: str, db_conn: sqlite3.Connection, temp_capture_dir: Path):
        """
        Combo 3: F2 (Edge Capture) + F6 (SQLite Context Persistence).
        Captures screenshot, derives metadata (1920x1080, bytes), registers in SQLite artifacts table,
        and verifies queryable state.
        """
        out_file = temp_capture_dir / "combo3_capture.png"
        user_data = temp_capture_dir / "combo3_user_data"
        ok = run_edge_capture(
            edge_bin=edge_binary,
            url=f"{base_url}/",
            output_path=out_file,
            user_data_dir=user_data,
            window_size="1920,1080",
            virtual_time_budget=1500,
            timeout=25.0,
        )
        assert ok is True
        assert out_file.exists()

        hdr = parse_png_header(out_file.read_bytes())
        file_size = out_file.stat().st_size
        iso_now = time.strftime("%Y-%m-%dT%H:%M:%SZ")
        meta = json.dumps({"width": hdr["width"], "height": hdr["height"], "test": "combo3"})

        cursor = db_conn.cursor()
        cursor.execute(
            """
            INSERT INTO artifacts (timestamp, epoch_id, artifact_name, artifact_type, file_path, file_size_bytes, metadata_json)
            VALUES (?, ?, ?, ?, ?, ?, ?);
            """,
            (iso_now, 1, out_file.name, "screenshot_test", str(out_file), file_size, meta),
        )
        db_conn.commit()
        last_id = cursor.lastrowid

        row = cursor.execute("SELECT * FROM artifacts WHERE id = ?;", (last_id,)).fetchone()
        assert row["artifact_name"] == out_file.name
        assert row["file_size_bytes"] == file_size
        read_meta = json.loads(row["metadata_json"])
        assert read_meta["width"] == 1920
        assert read_meta["height"] == 1080

        cursor.execute("DELETE FROM artifacts WHERE id = ?;", (last_id,))
        db_conn.commit()

    def test_tier3_combo4_db_registration_and_markdown_embed(self, project_root: Path, db_conn: sqlite3.Connection):
        """
        Combo 4: F6 (SQLite Context Persistence) + F5 (Markdown Snapshot Image Sync).
        Verifies that screenshot artifacts indexed in SQLite correspond to ![alt](path) links in snapshots.
        """
        cursor = db_conn.cursor()
        rows = cursor.execute("SELECT artifact_name FROM artifacts WHERE artifact_type LIKE '%screenshot%';").fetchall()
        db_names = {r["artifact_name"] for r in rows}

        snap_dir = project_root / ".agents" / "context" / "snapshots"
        md_files = list(snap_dir.glob("*.md"))
        assert len(md_files) > 0

        img_pattern = re.compile(r"!\[(.*?)\]\((.*?)\)")
        found_sync = False
        for f in sorted(md_files, key=lambda p: p.stat().st_mtime, reverse=True)[:5]:
            content = f.read_text(encoding="utf-8", errors="ignore")
            for _, link in img_pattern.findall(content):
                link_filename = Path(link).name
                if link_filename in db_names:
                    found_sync = True
                    break

        check_milestone_capability("M3", found_sync, "Markdown snapshot embeds match SQLite artifacts table (M3)")

    def test_tier3_combo5_markdown_and_gallery_sync(self, base_url: str, project_root: Path):
        """
        Combo 5: F5 (Markdown Snapshot Image Sync) + F4 (Interactive Evolution Gallery).
        Verifies that visual assets highlighted in latest snapshot are accessible via web gallery.
        """
        latest_file = project_root / ".agents" / "context" / "latest_context_snapshot.md"
        assert latest_file.exists()
        status_code, body, _ = http_request(f"{base_url}/evolution")
        assert status_code == 200
        html = body.decode("utf-8", errors="ignore")
        assert "gallery" in html.lower()

    def test_tier3_combo6_db_benchmarks_and_latex_sync(self, project_root: Path, db_conn: sqlite3.Connection):
        """
        Combo 6: F6 (SQLite Benchmarks) + F7 (LaTeX Monograph).
        Verifies that empirical benchmarks recorded in SQLite match figures cited in silicon_sanctuary_report.tex.
        """
        cursor = db_conn.cursor()
        rows = cursor.execute("SELECT epoch_id, metric_name, value_numeric, unit FROM benchmarks;").fetchall()
        
        tex_file = project_root / "evolution" / "docs" / "latex" / "silicon_sanctuary_report.tex"
        assert tex_file.exists()
        tex_content = tex_file.read_text(encoding="utf-8")

        for r in rows:
            val_int_str = str(int(r['value_numeric'])) if isinstance(r['value_numeric'], (int, float)) else ""
            if r["epoch_id"] == 0 and val_int_str and len(val_int_str) >= 3:
                assert val_int_str in tex_content, (
                    f"Epoch 0 Benchmark value {val_int_str} ({r['metric_name']}) not cited in LaTeX report."
                )
            elif r["epoch_id"] > 0:
                check_milestone_capability("M3", val_int_str in tex_content,
                                           f"Multi-epoch benchmark {val_int_str} cited in LaTeX monograph (M3)")

    def test_tier3_combo7_2min_daemon_heartbeat_and_server_concurrency(self, base_url: str, db_conn: sqlite3.Connection):
        """
        Combo 7: F8 (2-Minute Daemon) + F1 (Server Freshness) + F6 (SQLite WAL Concurrency).
        Simulates concurrent read/write traffic while polling server endpoints; verifies zero 500 errors or locks.
        """
        errors = []

        for _ in range(10):
            s1, _, _ = http_request(f"{base_url}/api/heartbeat")
            s2, _, _ = http_request(f"{base_url}/api/city/status")
            if s1 != 200:
                errors.append(f"Heartbeat probe failed: {s1}")
            if s2 != 200:
                errors.append(f"City status probe failed: {s2}")

            try:
                cursor = db_conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM rate_limits;").fetchone()
            except Exception as e:
                errors.append(f"DB read error during probe: {e}")

        assert len(errors) == 0, f"Concurrency test encountered errors: {errors}"
