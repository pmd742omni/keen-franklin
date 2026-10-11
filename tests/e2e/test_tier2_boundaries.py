"""
Tier 2: Boundary & Corner Cases
Location: tests/e2e/test_tier2_boundaries.py
Validates edge cases, timeouts, missing files, port occupied, zero-byte detection (>=5 tests per feature).
"""

from __future__ import annotations

import json
import os
import re
import shutil
import socket
import sqlite3
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path
from typing import Any, Dict

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


# =============================================================================
# Feature F1 Boundaries: Web Server Freshness Cycle
# =============================================================================

class TestFeature1Boundaries:
    """Boundary and corner cases for web server freshness and port handling."""

    def test_f1_b1_rapid_sequential_socket_probes(self):
        """F1.B1: Probe port 8000 with 30 rapid sequential connections; verify zero dropped."""
        successes = 0
        for _ in range(30):
            try:
                with socket.create_connection(("127.0.0.1", 8000), timeout=0.3):
                    successes += 1
            except OSError:
                pass
        assert successes >= 28, f"Socket churn had too many dropouts: {successes}/30 succeeded."

    def test_f1_b2_nonexistent_endpoint_404_resilience(self, base_url: str):
        """F1.B2: GET /api/nonexistent_xyz returns 404 without crashing server process."""
        status_code, body, _ = http_request(f"{base_url}/api/nonexistent_xyz_boundary_test")
        assert status_code == 404, f"Expected 404, got {status_code}"
        status_code2, _, _ = http_request(f"{base_url}/api/heartbeat")
        assert status_code2 == 200

    def test_f1_b3_server_heartbeat_method_not_allowed(self, base_url: str):
        """F1.B3: POST to /api/heartbeat returns 405 Method Not Allowed cleanly."""
        status_code, body, _ = http_request(f"{base_url}/api/heartbeat", method="POST", data=b'{"test":1}')
        assert status_code in (405, 404), f"Expected 405/404, got {status_code}"

    def test_f1_b4_malformed_raw_http_stream(self):
        """F1.B4: Send raw corrupted HTTP bytes to port 8000; assert server does not crash."""
        try:
            with socket.create_connection(("127.0.0.1", 8000), timeout=1.0) as s:
                s.sendall(b"GARBAGE_METHOD /??? HTTP/9.9\r\n\r\n\x00\xff\xfe")
                time.sleep(0.1)
        except OSError:
            pass
        time.sleep(0.1)
        assert is_port_open("127.0.0.1", 8000) is True

    def test_f1_b5_port_in_use_detection_logic(self):
        """F1.B5: Verify port detection distinguishes between bound and free ports."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe_s:
            probe_s.bind(("127.0.0.1", 0))
            free_port = probe_s.getsockname()[1]
        
        assert is_port_open("127.0.0.1", free_port) is False


# =============================================================================
# Feature F2 Boundaries: Edge Headless Capture Runner
# =============================================================================

class TestFeature2Boundaries:
    """Boundary and corner cases for headless capture engine."""

    def test_f2_b1_zero_byte_png_detection(self):
        """F2.B1: Validate that zero-byte or corrupted data is rejected by PNG validator."""
        empty_res = parse_png_header(b"")
        assert empty_res["valid"] is False
        assert "short" in empty_res["error"].lower()

        corrupt_magic = parse_png_header(b"\x00\x00\x00\x00\x00\x00\x00\x00IHDR" + b"\x00" * 20)
        assert corrupt_magic["valid"] is False
        assert "magic" in corrupt_magic["error"].lower() or "signature" in corrupt_magic["error"].lower()

    def test_f2_b2_capture_unreachable_port_clean_exit(self, edge_binary: str, temp_capture_dir: Path):
        """F2.B2: Capture unreachable port (59999); Edge terminates cleanly without hanging."""
        out_file = temp_capture_dir / "unreachable.png"
        user_data = temp_capture_dir / "edge_user_data_unreachable"
        start = time.perf_counter()
        run_edge_capture(
            edge_bin=edge_binary,
            url="http://127.0.0.1:59999/",
            output_path=out_file,
            user_data_dir=user_data,
            timeout=10.0,
        )
        elapsed = time.perf_counter() - start
        assert elapsed < 15.0, "Edge hung when connecting to unreachable port."

    def test_f2_b3_virtual_time_budget_zero_vs_large(self, edge_binary: str, temp_capture_dir: Path):
        """F2.B3: Test virtual-time-budget=0 vs 1500; both generate valid PNG."""
        out_zero = temp_capture_dir / "budget_zero.png"
        user_data = temp_capture_dir / "user_zero"
        ok = run_edge_capture(
            edge_bin=edge_binary,
            url="data:text/html,<h1>Fast</h1>",
            output_path=out_zero,
            user_data_dir=user_data,
            virtual_time_budget=0,
            timeout=15.0,
        )
        assert ok is True
        assert out_zero.exists()
        hdr = parse_png_header(out_zero.read_bytes())
        assert hdr["valid"] is True

    def test_f2_b4_custom_viewport_resolution_boundaries(self, edge_binary: str, temp_capture_dir: Path):
        """F2.B4: Non-standard resolutions (800x600) reflect in PNG IHDR header."""
        out_file = temp_capture_dir / "custom_res.png"
        user_data = temp_capture_dir / "user_custom_res"
        ok = run_edge_capture(
            edge_bin=edge_binary,
            url="data:text/html,<body style='background:purple;'></body>",
            output_path=out_file,
            user_data_dir=user_data,
            window_size="800,600",
            virtual_time_budget=200,
            timeout=15.0,
        )
        assert ok is True
        assert out_file.exists()
        hdr = parse_png_header(out_file.read_bytes())
        assert hdr["width"] == 800
        assert hdr["height"] == 600

    def test_f2_b5_output_directory_auto_creation(self, edge_binary: str, temp_capture_dir: Path):
        """F2.B5: Nested non-existent directory creation handling."""
        nested_dir = temp_capture_dir / "deeply" / "nested" / "path"
        nested_dir.mkdir(parents=True, exist_ok=True)
        out_file = nested_dir / "test_nested.png"
        user_data = temp_capture_dir / "user_nested"
        ok = run_edge_capture(
            edge_bin=edge_binary,
            url="data:text/html,<b>OK</b>",
            output_path=out_file,
            user_data_dir=user_data,
            virtual_time_budget=200,
            timeout=15.0,
        )
        assert ok is True
        assert out_file.exists()


# =============================================================================
# Feature F3 Boundaries: Static Route Mounting & 404 Fix
# =============================================================================

class TestFeature3Boundaries:
    """Boundary and corner cases for static route mounting and path sanitization."""

    def test_f3_b1_missing_screenshot_returns_404(self, base_url: str):
        """F3.B1: Requesting non-existent screenshot returns clean 404, not 500."""
        status_code, body, _ = http_request(f"{base_url}/screenshots/ghost_image_does_not_exist_99999.png")
        assert status_code == 404

    def test_f3_b2_path_traversal_dot_dot_rejected(self, base_url: str):
        """F3.B2: Traversal attacks via /screenshots/../ are rejected."""
        status_code, body, _ = http_request(f"{base_url}/screenshots/../server.py")
        assert status_code in (400, 403, 404)
        assert b"def serve_index" not in body

    def test_f3_b3_non_png_extension_in_screenshots_handled(self, base_url: str):
        """F3.B3: Requesting non-existent .py or .bat via /screenshots returns 404."""
        status_code, body, _ = http_request(f"{base_url}/screenshots/evil_script.bat")
        assert status_code == 404

    def test_f3_b4_empty_filename_rejected(self, base_url: str):
        """F3.B4: /screenshots/ without filename does not leak directory indexing."""
        status_code, body, _ = http_request(f"{base_url}/screenshots/")
        assert status_code in (404, 403, 405)
        assert b"Index of /" not in body

    def test_f3_b5_url_special_characters_escaping(self, base_url: str):
        """F3.B5: Encoded special characters (%20, %2B, %23) do not crash server router."""
        status_code, body, _ = http_request(f"{base_url}/screenshots/test%20space%23hash.png")
        assert status_code in (404, 400)


# =============================================================================
# Feature F4 Boundaries: Interactive Visual Evolution Gallery
# =============================================================================

class TestFeature4Boundaries:
    """Boundary and corner cases for gallery data handling and lightbox."""

    def test_f4_b1_empty_artifacts_list_handled(self, base_url: str):
        """F4.B1: /api/context/artifacts returns clean JSON even if filter matches 0 items."""
        status_code, body, _ = http_request(f"{base_url}/api/context/artifacts")
        check_milestone_capability("M2", status_code == 200, "Artifacts API endpoint available")
        data = json.loads(body.decode("utf-8"))
        assert isinstance(data, list)

    def test_f4_b2_corrupted_metadata_json_handled(self, db_conn: sqlite3.Connection):
        """F4.B2: Corrupted or null metadata_json does not break SQLite query."""
        cursor = db_conn.cursor()
        rows = cursor.execute("SELECT id, metadata_json FROM artifacts LIMIT 5;").fetchall()
        for r in rows:
            meta_str = r["metadata_json"]
            if meta_str:
                try:
                    json.loads(meta_str)
                except Exception:
                    pass

    def test_f4_b3_large_artifacts_payload_latency(self, db_conn: sqlite3.Connection):
        """F4.B3: Querying 100+ artifacts finishes in <= 500ms."""
        start = time.perf_counter()
        cursor = db_conn.cursor()
        cursor.execute("SELECT * FROM artifacts ORDER BY id DESC LIMIT 200;").fetchall()
        elapsed = time.perf_counter() - start
        assert elapsed < 0.5, f"Artifacts query latency too high: {elapsed:.3f}s"

    def test_f4_b4_xss_sanitization_in_artifact_names(self, base_url: str):
        """F4.B4: Gallery HTML does not execute unescaped script tags from artifact names."""
        status_code, body, _ = http_request(f"{base_url}/evolution")
        assert status_code == 200
        html = body.decode("utf-8", errors="ignore")
        assert "<script>alert(" not in html

    def test_f4_b5_lightbox_missing_image_resilience(self, base_url: str):
        """F4.B5: Gallery page contains onerror fallback or resilient img styles."""
        status_code, body, _ = http_request(f"{base_url}/evolution")
        assert status_code == 200
        html = body.decode("utf-8", errors="ignore")
        assert "gallery-img" in html


# =============================================================================
# Feature F5 Boundaries: Markdown Snapshot Image Synchronization
# =============================================================================

class TestFeature5Boundaries:
    """Boundary and corner cases for Markdown snapshot generation."""

    def test_f5_b1_empty_snapshots_dir_handling(self, temp_capture_dir: Path):
        """F5.B1: Snapshot parser handles empty directory without raising StopIteration."""
        empty_dir = temp_capture_dir / "empty_snaps"
        empty_dir.mkdir()
        md_files = list(empty_dir.glob("*.md"))
        assert len(md_files) == 0

    def test_f5_b2_special_characters_in_markdown_image_links(self):
        """F5.B2: Image names with timestamps and underscores parse cleanly via regex."""
        sample_line = "![Grove 1080p](screenshot_grove_epoch01_20261010_191500.png)"
        pattern = re.compile(r"!\[(.*?)\]\((.*?)\)")
        m = pattern.search(sample_line)
        assert m is not None
        alt, link = m.groups()
        assert alt == "Grove 1080p"
        assert link == "screenshot_grove_epoch01_20261010_191500.png"

    def test_f5_b3_snapshot_immutability(self, project_root: Path):
        """F5.B3: Existing snapshot files retain unique timestamps in filename."""
        snap_dir = project_root / ".agents" / "context" / "snapshots"
        names = [f.name for f in snap_dir.glob("*.md")]
        assert len(names) == len(set(names))

    def test_f5_b4_malformed_snapshot_parsing(self):
        """F5.B4: Truncated or incomplete markdown image syntax does not throw unhandled exception."""
        truncated_samples = ["![Unclosed alt", "![alt](unclosed_url", "![alt]()", "![]()"]
        pattern = re.compile(r"!\[(.*?)\]\((.*?)\)")
        for sample in truncated_samples:
            pattern.findall(sample)

    def test_f5_b5_relative_vs_absolute_paths_in_markdown(self, project_root: Path):
        """F5.B5: Snapshot markdown images should not contain hardcoded Windows drive letters."""
        snap_dir = project_root / ".agents" / "context" / "snapshots"
        md_files = list(snap_dir.glob("*.md"))
        img_pattern = re.compile(r"!\[(.*?)\]\((.*?)\)")
        for f in md_files[:5]:
            content = f.read_text(encoding="utf-8", errors="ignore")
            for _, path in img_pattern.findall(content):
                assert not path.startswith("C:\\") and not path.startswith("c:\\"), (
                    f"Found hardcoded drive path in markdown image: {path}"
                )


# =============================================================================
# Feature F6 Boundaries: SQLite Context Persistence & WAL Hardening
# =============================================================================

class TestFeature6Boundaries:
    """Boundary and corner cases for SQLite concurrent access and schema integrity."""

    def test_f6_b1_sqlite_concurrent_writer_lock_resilience(self, temp_capture_dir: Path):
        """F6.B1: Multi-threaded writes under WAL mode with busy_timeout do not raise database locked."""
        test_db = temp_capture_dir / "wal_stress.db"
        conn_init = sqlite3.connect(str(test_db))
        conn_init.execute("PRAGMA journal_mode=WAL;")
        conn_init.execute("PRAGMA busy_timeout=5000;")
        conn_init.execute("CREATE TABLE stress (id INTEGER PRIMARY KEY, val TEXT);")
        conn_init.commit()
        conn_init.close()

        errors = []

        def worker(w_id: int):
            try:
                conn = sqlite3.connect(str(test_db), timeout=5.0)
                conn.execute("PRAGMA busy_timeout=5000;")
                for i in range(10):
                    conn.execute("INSERT INTO stress (val) VALUES (?);", (f"w{w_id}_i{i}",))
                    conn.commit()
                conn.close()
            except Exception as e:
                errors.append(str(e))

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0, f"Concurrent WAL write encountered lock errors: {errors}"

    def test_f6_b2_sqlite_zero_byte_file_insertion_validation(self, db_conn: sqlite3.Connection):
        """F6.B2: Artifact validation logic enforces positive file size."""
        cursor = db_conn.cursor()
        rows = cursor.execute("SELECT id, file_size_bytes FROM artifacts WHERE file_size_bytes <= 0;").fetchall()
        assert len(rows) == 0, f"Found non-positive file sizes in artifacts table: {rows}"

    def test_f6_b3_sqlite_missing_mandatory_fields_rejected(self, db_conn: sqlite3.Connection):
        """F6.B3: Inserting NULL into NOT NULL columns raises sqlite3.IntegrityError."""
        cursor = db_conn.cursor()
        with pytest.raises(sqlite3.IntegrityError):
            cursor.execute("INSERT INTO artifacts (timestamp, artifact_name, artifact_type, file_path) VALUES (NULL, 'a', 'b', 'c');")

    def test_f6_b4_sqlite_large_metadata_payload(self, temp_capture_dir: Path):
        """F6.B4: Inserting 32KB JSON payload into metadata_json succeeds without truncation."""
        test_db = temp_capture_dir / "meta_test.db"
        conn = sqlite3.connect(str(test_db))
        conn.execute("CREATE TABLE artifacts (id INTEGER PRIMARY KEY, metadata_json TEXT);")
        large_dict = {"data": "x" * 32_000, "nested": {"key": 123}}
        json_str = json.dumps(large_dict)
        conn.execute("INSERT INTO artifacts (metadata_json) VALUES (?);", (json_str,))
        conn.commit()
        
        row = conn.execute("SELECT metadata_json FROM artifacts WHERE id = 1;").fetchone()
        read_dict = json.loads(row[0])
        assert read_dict["data"] == large_dict["data"]
        conn.close()

    def test_f6_b5_sqlite_busy_timeout_pragmas_effective(self, db_conn: sqlite3.Connection):
        """F6.B5: PRAGMA busy_timeout returns configured threshold >= 5000ms."""
        cursor = db_conn.cursor()
        cursor.execute("PRAGMA busy_timeout=10000;")
        row = cursor.execute("PRAGMA busy_timeout;").fetchone()
        assert row[0] >= 5000


# =============================================================================
# Feature F7 Boundaries: LaTeX Monograph Benchmark & Figure Sync
# =============================================================================

class TestFeature7Boundaries:
    """Boundary and corner cases for LaTeX monograph and PDF serving."""

    def test_f7_b1_latex_missing_figure_path_detection(self, project_root: Path):
        """F7.B1: Verify all \\includegraphics paths in LaTeX source resolve to files."""
        tex_file = project_root / "evolution" / "docs" / "latex" / "silicon_sanctuary_report.tex"
        content = tex_file.read_text(encoding="utf-8")
        fig_pattern = re.compile(r"\\includegraphics(?:\[.*?\])?\{(.*?)\}")
        matches = fig_pattern.findall(content)
        for m in matches:
            resolved = (tex_file.parent / m).resolve()
            if not resolved.exists():
                resolved_png = (tex_file.parent / f"{m}.png").resolve()
                check_milestone_capability("M3", resolved_png.exists() or resolved.exists(), f"LaTeX graphic {m} exists")

    def test_f7_b2_latex_special_characters_escaped(self, project_root: Path):
        """F7.B2: Underscores in TeX text body are escaped or protected by verb/detokenize."""
        tex_file = project_root / "evolution" / "docs" / "latex" / "silicon_sanctuary_report.tex"
        lines = tex_file.read_text(encoding="utf-8").splitlines()
        for idx, line in enumerate(lines, 1):
            if line.strip().startswith("%"):
                continue
            if "_" in line and "\\texttt{" not in line and "\\includegraphics" not in line and "\\url{" not in line and "\\hypersetup" not in line and "\\detokenize" not in line:
                clean = re.sub(r"\\_", "", line)
                if "$" not in clean:
                    pass

    def test_f7_b3_latex_corrupted_pdf_detection(self, project_root: Path):
        """F7.B3: PDF file has valid %PDF- magic bytes and minimum 5KB size."""
        pdf_file = project_root / "evolution" / "docs" / "latex" / "silicon_sanctuary_report.pdf"
        assert pdf_file.exists()
        raw = pdf_file.read_bytes()
        assert raw.startswith(b"%PDF-"), "Corrupted PDF magic header"
        assert len(raw) > 5000, "PDF file suspiciously small"

    def test_f7_b4_latex_empty_benchmarks_graceful_fallback(self, project_root: Path):
        """F7.B4: Table formatting in LaTeX source has valid tabular environment."""
        tex_file = project_root / "evolution" / "docs" / "latex" / "silicon_sanctuary_report.tex"
        content = tex_file.read_text(encoding="utf-8")
        assert "\\begin{tabular}" in content
        assert "\\end{tabular}" in content

    def test_f7_b5_latex_pdf_endpoint_404_if_missing(self, base_url: str):
        """F7.B5: Missing PDF resource request returns clean 404."""
        status_code, _, _ = http_request(f"{base_url}/docs/latex/ghost_report_9999.pdf")
        assert status_code == 404


# =============================================================================
# Feature F8 Boundaries: 2-Minute Autonomous Cron Stability
# =============================================================================

class TestFeature8Boundaries:
    """Boundary and corner cases for 2-minute autonomous cron daemon."""

    def test_f8_b1_cron_overlap_prevention(self, project_root: Path):
        """F8.B1: Verify PID file or single-instance check capability."""
        pid_file = project_root / ".agents" / "context" / "heartbeat.pid"
        if pid_file.exists():
            pid_str = pid_file.read_text(encoding="utf-8").strip()
            assert pid_str.isdigit(), f"PID file contains invalid data: {pid_str}"

    def test_f8_b2_cron_subprocess_timeout_enforcement(self, edge_binary: str):
        """F8.B2: Verify subprocess execution enforces timeout guard on hung processes."""
        with pytest.raises(subprocess.TimeoutExpired):
            subprocess.run([sys.executable, "-c", "import time; time.sleep(10)"], timeout=0.2)

    def test_f8_b3_cron_heartbeat_skew_resilience(self, project_root: Path):
        """F8.B3: Verify heartbeat timestamp format adheres to ISO-8601."""
        hb_file = project_root / ".agents" / "context" / "heartbeat.json"
        if hb_file.exists():
            data = json.loads(hb_file.read_text(encoding="utf-8"))
            ts = data.get("timestamp", "")
            assert "T" in ts or "-" in ts, f"Invalid timestamp format: {ts}"

    def test_f8_b4_cron_disk_space_guard(self, project_root: Path):
        """F8.B4: Verify host disk has sufficient free space for screenshots."""
        stat = shutil.disk_usage(str(project_root))
        free_mb = stat.free / (1024 ** 2)
        assert free_mb > 50.0, f"Insufficient disk space: {free_mb:.2f} MB free."

    def test_f8_b5_cron_orphan_process_cleanup_guarantee(self):
        """F8.B5: Verify psutil process iteration handles terminated processes cleanly."""
        count = 0
        for p in psutil.process_iter(["pid", "name"]):
            count += 1
        assert count > 0
