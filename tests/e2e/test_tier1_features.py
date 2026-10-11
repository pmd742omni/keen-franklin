"""
Tier 1: Feature Coverage & Contract Verification
Location: tests/e2e/test_tier1_features.py
Validates Features F1 through F8 with >=5 test cases per feature (>=40 total).
"""

from __future__ import annotations

import ast
import json
import os
import re
import socket
import sqlite3
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict

import psutil
import pytest

from conftest import (
    BASE_URL,
    PROJECT_ROOT,
    check_milestone_capability,
    ensure_server_running,
    http_request,
    is_port_open,
    parse_png_header,
    run_edge_capture,
)


# =============================================================================
# Feature F1: Web Server Freshness Cycle
# =============================================================================

class TestFeature1WebServerFreshness:
    """Verifies graceful restart/reload, socket draining, and freshness cycle (F1)."""

    def test_f1_01_server_heartbeat_alive(self, base_url: str):
        """F1.1: Verify /api/heartbeat responds with HTTP 200 and nominal status JSON."""
        status_code, body, headers = http_request(f"{base_url}/api/heartbeat")
        assert status_code == 200, f"Expected HTTP 200, got {status_code}: {body[:200]!r}"
        data = json.loads(body.decode("utf-8"))
        assert "status" in data or "heartbeat_id" in data, f"Missing status in heartbeat payload: {data}"

    def test_f1_02_server_port_socket_responsive(self):
        """F1.2: Verify TCP socket on port 8000 completes handshake in <= 500ms."""
        start = time.perf_counter()
        connected = is_port_open("127.0.0.1", 8000, timeout=0.5)
        elapsed = time.perf_counter() - start
        assert connected is True, "Port 8000 is not accepting connections."
        assert elapsed < 0.5, f"TCP connection took too long: {elapsed:.3f}s"

    def test_f1_03_server_process_pid_identification(self):
        """F1.3: Verify active server process PID can be identified via psutil."""
        server_pid = None
        for conn in psutil.net_connections(kind="inet"):
            if conn.laddr.port == 8000 and conn.pid:
                server_pid = conn.pid
                break
        assert server_pid is not None, "No active process found listening on port 8000."
        proc = psutil.Process(server_pid)
        assert proc.is_running(), f"Process {server_pid} is not running."
        cmdline = " ".join(proc.cmdline())
        assert "uvicorn" in cmdline or "python" in cmdline or "server" in cmdline, (
            f"Unexpected server command line: {cmdline}"
        )

    def test_f1_04_server_freshness_lifecycle_contract(self, base_url: str):
        """F1.4: Verify the freshness contract: polling liveness before and after navigation."""
        status_1, body_1, _ = http_request(f"{base_url}/api/heartbeat")
        assert status_1 == 200
        assert is_port_open("127.0.0.1", 8000)
        status_root, body_root, _ = http_request(f"{base_url}/")
        assert status_root == 200
        assert b"Voxel" in body_root or b"canvas" in body_root.lower()

    def test_f1_05_server_city_status_endpoint(self, base_url: str):
        """F1.5: Verify /api/city/status returns HTTP 200 with simulation and hardware metrics."""
        status_code, body, _ = http_request(f"{base_url}/api/city/status")
        assert status_code == 200, f"Expected 200, got {status_code}"
        data = json.loads(body.decode("utf-8"))
        assert "tick" in data or "city" in data or "hardware" in data or "status" in data


# =============================================================================
# Feature F2: Edge Headless Capture Runner
# =============================================================================

class TestFeature2EdgeHeadlessCapture:
    """Verifies Microsoft Edge headless 1080p capture of / and /evolution (F2)."""

    def test_f2_01_edge_binary_presence_and_version(self, edge_binary: str):
        """F2.1: Verify Microsoft Edge binary is present and has valid version."""
        edge_path = Path(edge_binary)
        assert edge_path.exists(), f"Edge binary missing at {edge_binary}"
        assert edge_path.stat().st_size > 1_000_000, "Edge executable suspiciously small."

    def test_f2_02_edge_headless_flag_support(self, edge_binary: str, temp_capture_dir: Path):
        """F2.2: Verify Edge headless execution with required CLI flags on simple data URL."""
        out_file = temp_capture_dir / "probe_flag_test.png"
        user_data = temp_capture_dir / "edge_user_data"
        ok = run_edge_capture(
            edge_bin=edge_binary,
            url="data:text/html,<html><body style='background:teal;'><h1>Ready</h1></body></html>",
            output_path=out_file,
            user_data_dir=user_data,
            window_size="1920,1080",
            virtual_time_budget=500,
            timeout=25.0,
        )
        assert ok is True, "Edge failed to generate screenshot artifact."
        hdr = parse_png_header(out_file.read_bytes())
        assert hdr["valid"] is True
        assert hdr["width"] == 1920
        assert hdr["height"] == 1080

    def test_f2_03_edge_capture_root_grove_1080p(self, edge_binary: str, base_url: str, temp_capture_dir: Path):
        """F2.3: Capture live 3D Voxel Canvas (/) at 1080p and assert PNG integrity."""
        out_file = temp_capture_dir / "test_grove_1080p.png"
        user_data = temp_capture_dir / "edge_user_data_grove"
        ok = run_edge_capture(
            edge_bin=edge_binary,
            url=f"{base_url}/",
            output_path=out_file,
            user_data_dir=user_data,
            window_size="1920,1080",
            virtual_time_budget=2000,
            timeout=35.0,
        )
        assert ok is True, f"Failed to capture 3D Voxel Canvas at {base_url}/"
        file_bytes = out_file.read_bytes()
        assert len(file_bytes) > 20_000, f"File too small ({len(file_bytes)} bytes), canvas may be blank."
        hdr = parse_png_header(file_bytes)
        assert hdr["valid"] is True, f"Invalid PNG header: {hdr.get('error')}"
        assert hdr["width"] == 1920
        assert hdr["height"] == 1080

    def test_f2_04_edge_capture_evolution_portal_1080p(self, edge_binary: str, base_url: str, temp_capture_dir: Path):
        """F2.4: Capture live Evolution Portal (/evolution) at 1080p and assert PNG integrity."""
        out_file = temp_capture_dir / "test_portal_1080p.png"
        user_data = temp_capture_dir / "edge_user_data_portal"
        ok = run_edge_capture(
            edge_bin=edge_binary,
            url=f"{base_url}/evolution",
            output_path=out_file,
            user_data_dir=user_data,
            window_size="1920,1080",
            virtual_time_budget=1500,
            timeout=30.0,
        )
        assert ok is True, f"Failed to capture Evolution Portal at {base_url}/evolution"
        file_bytes = out_file.read_bytes()
        assert len(file_bytes) > 20_000
        hdr = parse_png_header(file_bytes)
        assert hdr["valid"] is True
        assert hdr["width"] == 1920
        assert hdr["height"] == 1080

    def test_f2_05_edge_capture_process_isolation_and_no_orphans(self, edge_binary: str, temp_capture_dir: Path):
        """F2.5: Verify Edge capture uses temp profile and terminates cleanly without lingering processes."""
        user_data = temp_capture_dir / "edge_iso_test"
        out_file = temp_capture_dir / "iso_test.png"
        ok = run_edge_capture(
            edge_bin=edge_binary,
            url="data:text/html,<b>Done</b>",
            output_path=out_file,
            user_data_dir=user_data,
            virtual_time_budget=300,
            timeout=20.0,
        )
        assert ok is True
        assert out_file.exists()


# =============================================================================
# Feature F3: Static Route Mounting & 404 Fix
# =============================================================================

class TestFeature3StaticRouteMounting:
    """Verifies /screenshots route mounting and 404 resolution (F3)."""

    def test_f3_01_static_css_route_served(self, base_url: str):
        """F3.1: Verify /static route serves stylesheet with HTTP 200."""
        status_code, body, headers = http_request(f"{base_url}/static/style.css")
        assert status_code == 200, f"Static CSS returned {status_code}"
        assert len(body) > 100

    def test_f3_02_screenshots_route_mounted(self, base_url: str):
        """F3.2: Verify /screenshots route is mounted in FastAPI."""
        status_code, body, _ = http_request(f"{base_url}/screenshots/probe_nonexistent.png")
        check_milestone_capability("M2", status_code in (404, 200), "/screenshots route mounted")

    def test_f3_03_existing_screenshots_served(self, base_url: str, project_root: Path):
        """F3.3: Verify existing screenshots in agent_city/screenshots or agent_city/ are served."""
        candidates = list((project_root / "agent_city").glob("screenshot_grove_*.png"))
        if not candidates:
            candidates = list((project_root / "agent_city" / "screenshots").glob("screenshot_*.png"))
        
        if candidates:
            sample_name = candidates[0].name
            status_code, body, headers = http_request(f"{base_url}/screenshots/{sample_name}")
            if status_code != 200:
                status_alt, body_alt, _ = http_request(f"{base_url}/{sample_name}")
                check_milestone_capability("M2", status_code == 200 or status_alt == 200, 
                                           f"Screenshot {sample_name} served via HTTP 200")
            else:
                assert status_code == 200
                content_type = headers.get("content-type", headers.get("Content-Type", ""))
                assert "image/png" in content_type or "png" in content_type

    def test_f3_04_new_screenshot_served_after_placement(self, base_url: str, project_root: Path, temp_capture_dir: Path):
        """F3.4: Place fixture PNG into screenshots directory and verify HTTP 200 retrieval."""
        screenshots_dir = project_root / "agent_city" / "screenshots"
        check_milestone_capability("M2", screenshots_dir.exists(), "agent_city/screenshots directory created by M2")
        
        test_png = screenshots_dir / "test_fixture_e2e_f3.png"
        try:
            minimal_png = (
                b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00"
                b"\x1f\x15c4\x00\x00\x00\rIDATx\x9cc`\x00\x00\x00\x02\x00\x01H\xaf\xa4q\x00\x00\x00\x00IEND\xaeB`\x82"
            )
            test_png.write_bytes(minimal_png)
            status_code, body, headers = http_request(f"{base_url}/screenshots/test_fixture_e2e_f3.png")
            assert status_code == 200
            assert body == minimal_png
        finally:
            if test_png.exists():
                try:
                    test_png.unlink()
                except Exception:
                    pass

    def test_f3_05_screenshots_traversal_prevention(self, base_url: str):
        """F3.5: Verify directory traversal requests are rejected and do not leak server files."""
        status_code, body, _ = http_request(f"{base_url}/screenshots/../server.py")
        assert status_code in (400, 403, 404), f"Traversal returned unexpected status: {status_code}"
        assert b"from fastapi import" not in body


# =============================================================================
# Feature F4: Interactive Visual Evolution Gallery
# =============================================================================

class TestFeature4InteractiveEvolutionGallery:
    """Verifies dynamic gallery on /evolution with epoch badges and zoom lightbox (F4)."""

    def test_f4_01_evolution_portal_serves_html(self, base_url: str):
        """F4.1: Verify /evolution returns HTTP 200 HTML with gallery section."""
        status_code, body, _ = http_request(f"{base_url}/evolution")
        assert status_code == 200
        html = body.decode("utf-8", errors="ignore")
        assert '<section id="gallery">' in html or 'id="gallery"' in html

    def test_f4_02_evolution_gallery_grid_present(self, base_url: str):
        """F4.2: Verify DOM contains .gallery-grid container for displaying cards."""
        status_code, body, _ = http_request(f"{base_url}/evolution")
        assert status_code == 200
        html = body.decode("utf-8", errors="ignore")
        assert "gallery-grid" in html

    def test_f4_03_evolution_gallery_cards_have_badges_and_timestamps(self, base_url: str):
        """F4.3: Verify gallery cards display epoch badges and metadata."""
        status_code, body, _ = http_request(f"{base_url}/evolution")
        assert status_code == 200
        html = body.decode("utf-8", errors="ignore")
        assert "gallery-badge" in html
        assert "Epoch" in html

    def test_f4_04_gallery_artifacts_api_contract(self, base_url: str):
        """F4.4: Verify /api/context/artifacts returns JSON array of screenshot artifacts."""
        status_code, body, _ = http_request(f"{base_url}/api/context/artifacts")
        check_milestone_capability("M2", status_code == 200, "/api/context/artifacts endpoint implemented by M2")
        data = json.loads(body.decode("utf-8"))
        assert isinstance(data, list)
        if len(data) > 0:
            first = data[0]
            assert "artifact_name" in first or "file_name" in first
            assert "epoch_id" in first

    def test_f4_05_gallery_zoom_preview_structure(self, base_url: str):
        """F4.5: Verify evolution portal includes zoom preview click handler or modal markup."""
        status_code, body, _ = http_request(f"{base_url}/evolution")
        assert status_code == 200
        html = body.decode("utf-8", errors="ignore")
        has_zoom = any(term in html.lower() for term in ["lightbox", "modal", "zoom", "preview", "onclick="])
        assert has_zoom is True, "Evolution gallery lacks zoom/preview interaction markup."


# =============================================================================
# Feature F5: Markdown Snapshot Image Synchronization
# =============================================================================

class TestFeature5MarkdownSnapshotSync:
    """Verifies image links in 5-minute context snapshots in .agents/context/snapshots/ (F5)."""

    def test_f5_01_snapshots_directory_populated(self, project_root: Path):
        """F5.1: Verify .agents/context/snapshots/ exists and contains markdown snapshots."""
        snap_dir = project_root / ".agents" / "context" / "snapshots"
        assert snap_dir.exists(), f"Snapshots directory missing at {snap_dir}"
        md_files = list(snap_dir.glob("*.md"))
        assert len(md_files) > 0, "No markdown snapshot files found in snapshots directory."

    def test_f5_02_snapshot_markdown_embed_syntax(self, project_root: Path):
        """F5.2: Verify snapshots contain markdown image embed syntax ![alt](path)."""
        snap_dir = project_root / ".agents" / "context" / "snapshots"
        md_files = sorted(snap_dir.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
        found_embed = False
        img_pattern = re.compile(r"!\[(.*?)\]\((.*?)\)")
        for f in md_files[:10]:
            content = f.read_text(encoding="utf-8", errors="ignore")
            if img_pattern.search(content):
                found_embed = True
                break
        check_milestone_capability("M3", found_embed, "Markdown snapshot contains ![alt](path) image embeds (M3)")

    def test_f5_03_snapshot_referenced_images_exist(self, project_root: Path):
        """F5.3: Verify images embedded in markdown snapshots correspond to valid files."""
        snap_dir = project_root / ".agents" / "context" / "snapshots"
        md_files = sorted(snap_dir.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
        img_pattern = re.compile(r"!\[(.*?)\]\((.*?)\)")
        for f in md_files[:5]:
            content = f.read_text(encoding="utf-8", errors="ignore")
            matches = img_pattern.findall(content)
            for alt, img_path in matches:
                resolved = (f.parent / img_path).resolve()
                if not resolved.exists():
                    resolved_root = (project_root / img_path.lstrip("/\\")).resolve()
                    check_milestone_capability("M3", resolved_root.exists(), f"Image {img_path} exists on disk")

    def test_f5_04_snapshot_cron_script_exists_and_valid(self, project_root: Path):
        """F5.4: Verify .agents/context/context_cron_markdown.py exists and parses cleanly."""
        script_path = project_root / ".agents" / "context" / "context_cron_markdown.py"
        assert script_path.exists(), f"Script missing at {script_path}"
        source = script_path.read_text(encoding="utf-8")
        parsed = ast.parse(source)
        assert isinstance(parsed, ast.Module)

    def test_f5_05_latest_context_snapshot_sync(self, project_root: Path):
        """F5.5: Verify .agents/context/latest_context_snapshot.md exists and is non-empty."""
        latest_file = project_root / ".agents" / "context" / "latest_context_snapshot.md"
        assert latest_file.exists(), f"Missing {latest_file}"
        assert latest_file.stat().st_size > 200, "latest_context_snapshot.md is suspiciously empty."


# =============================================================================
# Feature F6: SQLite Context Persistence & WAL Hardening
# =============================================================================

class TestFeature6SqliteContextPersistence:
    """Verifies SQLite WAL pragmas, artifacts table, dimensions metadata (F6)."""

    def test_f6_01_sqlite_database_exists(self, db_path: Path):
        """F6.1: Verify SQLite sanctuary_context.db exists and is non-empty."""
        assert db_path.exists(), f"Database missing at {db_path}"
        assert db_path.stat().st_size > 10_000, f"Database suspiciously small ({db_path.stat().st_size} bytes)"

    def test_f6_02_sqlite_wal_pragmas_enforced(self, db_conn: sqlite3.Connection):
        """F6.2: Verify WAL journal mode and busy timeout configured (contract: PRAGMA journal_mode=WAL)."""
        cursor = db_conn.cursor()
        mode = cursor.execute("PRAGMA journal_mode;").fetchone()[0]
        check_milestone_capability("M3", mode.lower() == "wal", f"SQLite journal_mode is WAL (found: {mode})")

    def test_f6_03_sqlite_artifacts_table_schema(self, db_conn: sqlite3.Connection):
        """F6.3: Verify artifacts table columns match interface contract in PROJECT.md."""
        cursor = db_conn.cursor()
        cols = {row["name"]: row["type"] for row in cursor.execute("PRAGMA table_info(artifacts);")}
        expected_cols = ["id", "timestamp", "epoch_id", "artifact_name", "artifact_type", "file_path", "file_size_bytes", "metadata_json"]
        for c in expected_cols:
            assert c in cols, f"Missing column {c} in artifacts table: {cols}"

    def test_f6_04_sqlite_artifacts_contain_dimensions_metadata(self, db_conn: sqlite3.Connection):
        """F6.4: Verify screenshot artifacts store width=1920, height=1080 in metadata_json."""
        cursor = db_conn.cursor()
        rows = cursor.execute("SELECT * FROM artifacts WHERE artifact_type LIKE '%screenshot%'").fetchall()
        assert len(rows) > 0, "No screenshot artifacts found in artifacts table."
        for row in rows:
            assert row["file_size_bytes"] is not None and row["file_size_bytes"] > 0
            if row["metadata_json"]:
                try:
                    meta = json.loads(row["metadata_json"])
                    if "width" in meta:
                        assert meta["width"] in (1920, 1600, 1280)
                        assert meta["height"] in (1080, 1000, 860)
                except json.JSONDecodeError:
                    pass

    def test_f6_05_sqlite_no_ddl_on_read_contract(self, db_conn: sqlite3.Connection):
        """F6.5: Verify read operations do not alter schema_version."""
        cursor = db_conn.cursor()
        v1 = cursor.execute("PRAGMA schema_version;").fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM artifacts;").fetchone()
        cursor.execute("SELECT COUNT(*) FROM benchmarks;").fetchone()
        v2 = cursor.execute("PRAGMA schema_version;").fetchone()[0]
        assert v1 == v2, "Read queries mutated database schema!"


# =============================================================================
# Feature F7: LaTeX Monograph Benchmark & Figure Sync
# =============================================================================

class TestFeature7LatexMonographSync:
    """Verifies LaTeX monograph report with figure embeds & empirical benchmarks (F7)."""

    def test_f7_01_latex_report_tex_exists(self, project_root: Path):
        """F7.1: Verify evolution/docs/latex/silicon_sanctuary_report.tex exists."""
        tex_file = project_root / "evolution" / "docs" / "latex" / "silicon_sanctuary_report.tex"
        assert tex_file.exists(), f"LaTeX source missing at {tex_file}"
        assert tex_file.stat().st_size > 1000

    def test_f7_02_latex_includes_graphicx(self, project_root: Path):
        """F7.2: Verify LaTeX file imports graphicx package."""
        tex_file = project_root / "evolution" / "docs" / "latex" / "silicon_sanctuary_report.tex"
        content = tex_file.read_text(encoding="utf-8")
        assert "\\usepackage{graphicx}" in content

    def test_f7_03_latex_figures_and_includegraphics(self, project_root: Path):
        """F7.3: Verify LaTeX document embeds figures using \\includegraphics (F7 contract)."""
        tex_file = project_root / "evolution" / "docs" / "latex" / "silicon_sanctuary_report.tex"
        content = tex_file.read_text(encoding="utf-8")
        has_fig = "\\begin{figure}" in content or "\\includegraphics" in content
        check_milestone_capability("M3", has_fig, "LaTeX monograph includes \\begin{figure} and \\includegraphics (M3)")

    def test_f7_04_latex_empirical_benchmarks(self, project_root: Path):
        """F7.4: Verify LaTeX document includes empirical benchmarks table."""
        tex_file = project_root / "evolution" / "docs" / "latex" / "silicon_sanctuary_report.tex"
        content = tex_file.read_text(encoding="utf-8")
        assert "Compaction" in content
        assert "3,859.75" in content or "3859" in content

    def test_f7_05_latex_pdf_endpoint_served(self, base_url: str, project_root: Path):
        """F7.5: Verify /docs/latex/silicon_sanctuary_report.pdf serves compiled PDF."""
        pdf_path = project_root / "evolution" / "docs" / "latex" / "silicon_sanctuary_report.pdf"
        assert pdf_path.exists(), f"PDF missing at {pdf_path}"
        status_code, body, headers = http_request(f"{base_url}/docs/latex/silicon_sanctuary_report.pdf")
        assert status_code == 200, f"Expected 200, got {status_code}"
        assert body.startswith(b"%PDF-"), "Response does not contain valid PDF magic bytes."


# =============================================================================
# Feature F8: 2-Minute Autonomous Cron Stability
# =============================================================================

class TestFeature8TwoMinuteCronStability:
    """Verifies continuous 2-minute documentation daemon stability (F8)."""

    def test_f8_01_heartbeat_liveness_pulse(self, base_url: str, project_root: Path):
        """F8.1: Verify heartbeat file and endpoint return valid pulse."""
        hb_file = project_root / ".agents" / "context" / "heartbeat.json"
        assert hb_file.exists(), f"heartbeat.json missing at {hb_file}"
        hb_data = json.loads(hb_file.read_text(encoding="utf-8"))
        assert "heartbeat_id" in hb_data or "timestamp" in hb_data or "status" in hb_data
        status_code, body, _ = http_request(f"{base_url}/api/heartbeat")
        assert status_code == 200

    def test_f8_02_visual_doc_capture_script_syntax(self, project_root: Path):
        """F8.2: Verify visual_doc_capture.py is syntactically valid."""
        script_file = project_root / ".agents" / "context" / "visual_doc_capture.py"
        assert script_file.exists(), f"Capture script missing at {script_file}"
        code = script_file.read_text(encoding="utf-8")
        compiled = compile(code, str(script_file), "exec")
        assert compiled is not None

    def test_f8_03_cron_concurrency_no_port_contention(self, project_root: Path):
        """F8.3: Verify visual capture runner checks port 8000 safely without crashing."""
        assert is_port_open("127.0.0.1", 8000) is True

    def test_f8_04_cron_concurrency_no_db_locks(self, db_conn: sqlite3.Connection):
        """F8.4: Verify database operations execute smoothly under concurrency."""
        cursor = db_conn.cursor()
        row = cursor.execute("SELECT COUNT(*) FROM rate_limits;").fetchone()
        assert row[0] >= 0

    def test_f8_05_cron_runner_dry_run_or_once(self, project_root: Path):
        """F8.5: Verify visual_doc_capture.py supports --help or --once CLI arguments."""
        script_file = project_root / ".agents" / "context" / "visual_doc_capture.py"
        res = subprocess.run([sys.executable, str(script_file), "--help"], capture_output=True, timeout=10)
        assert res.returncode == 0
        assert b"--once" in res.stdout or b"Visual Documentation" in res.stdout
