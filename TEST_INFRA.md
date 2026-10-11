# Testing Infrastructure & Methodology Specification (`TEST_INFRA.md`)

**Project**: Autonomous Multi-Agent Visual Documentation System  
**Author**: E2E Test Suite Architect (`teamwork_preview_test_writer`)  
**Scope**: Opaque-box E2E Test Suite (Tiers 1–4) & Progressive Testability Framework  
**Location**: `tests/e2e/`  

---

## 1. Executive Summary & Architecture

The Autonomous Multi-Agent Visual Documentation System operates on a 2-minute cron cadence to capture high-resolution visual progress screenshots of the running web application via Microsoft Edge headless, embeds them into interactive evolution galleries and Markdown snapshots, and maintains persistent documentation state across the 336-hour autonomous horizon.

The testing infrastructure is designed as an **opaque-box, multi-tier, requirement-driven test suite** residing in `tests/e2e/`. It evaluates the system strictly against the user requirements from `ORIGINAL_REQUEST.md` and the interface contracts defined in `PROJECT.md`, without depending on implementation internals.

### 1.1 Test Suite Directory Structure
```
tests/e2e/
├── __init__.py                  # Package marker
├── conftest.py                  # Pytest fixtures, HTTP/socket helpers, PNG header parser, DB connection
├── test_runner.py               # Master CLI test runner, tier/feature filtering, JSON reporter
├── test_tier1_features.py       # Tier 1: Feature coverage (F1–F8, 40 tests)
├── test_tier2_boundaries.py     # Tier 2: Boundary, negative & corner cases (F1–F8, 40 tests)
├── test_tier3_combinations.py   # Tier 3: Cross-feature pairwise interactions (7 workflows)
├── test_tier4_scenarios.py      # Tier 4: Real-world operational scenarios (5 workflows)
└── reports/                     # Structured JSON test execution reports
```

---

## 2. 4-Tier Test Case Design Methodology

The test suite adheres strictly to the 4-Tier Test Case Design Hierarchy:

| Tier | Category | Minimum Target | Actual Count | Scope & Purpose |
| :--- | :--- | :--- | :--- | :--- |
| **Tier 1** | **Feature Coverage** | $\ge 5$ per feature (F1–F8) | **40 tests** | Opaque-box verification of primary behavior (happy path) for all 8 system features. |
| **Tier 2** | **Boundary & Corner Cases** | $\ge 5$ per feature (F1–F8) | **40 tests** | Robustness probes: timeouts, missing files, 0-byte detection, port collisions, DB locks, traversal attacks, and corrupted payloads. |
| **Tier 3** | **Cross-Feature Combinations** | Pairwise interactions | **7 tests** | Multi-subsystem integration: restart+capture, capture+gallery, capture+db, db+markdown, markdown+gallery, db+latex, daemon+concurrency. |
| **Tier 4** | **Real-World Scenarios** | Operational workflows | **5 tests** | End-to-end 2-minute cadence simulation with live server, captures of `/` and `/evolution`, DB registration, and live traffic stress testing. |
| **Total** | | | **92 tests** | Comprehensive coverage across all architectural boundaries. |

---

## 3. Feature Coverage Matrix (Tier 1 & Tier 2)

### F1: Web Server Freshness Cycle
*Graceful restart/reload of uvicorn server on port 8000, socket draining, clean page reload.*
- **Tier 1 Tests**:
  - `test_f1_01_server_heartbeat_alive`: `GET /api/heartbeat` responds HTTP 200 with JSON status.
  - `test_f1_02_server_port_socket_responsive`: TCP socket connection handshake on port 8000 completes in $< 500$ ms.
  - `test_f1_03_server_process_pid_identification`: PID holding port 8000 identified via `psutil` as running Python/uvicorn.
  - `test_f1_04_server_freshness_lifecycle_contract`: Polling liveness before and after navigation without socket errors.
  - `test_f1_05_server_city_status_endpoint`: `GET /api/city/status` returns HTTP 200 with simulation and hardware metrics.
- **Tier 2 Boundary Tests**:
  - `test_f1_b1_rapid_sequential_socket_probes`: 30 rapid sequential socket connects/disconnects without socket exhaustion.
  - `test_f1_b2_nonexistent_endpoint_404_resilience`: `GET /api/nonexistent_xyz` returns clean 404 without crashing server process.
  - `test_f1_b3_server_heartbeat_method_not_allowed`: `POST /api/heartbeat` returns 405 Method Not Allowed cleanly.
  - `test_f1_b4_malformed_raw_http_stream`: Raw malformed stream to port 8000 handled without crashing server.
  - `test_f1_b5_port_in_use_detection_logic`: Socket binding detection accurately differentiates bound vs free ports.

### F2: Edge Headless Capture Runner
*Microsoft Edge headless 1080p capture of `/` and `/evolution` with virtual-time settling delay and temp user-data-dir.*
- **Tier 1 Tests**:
  - `test_f2_01_edge_binary_presence_and_version`: Microsoft Edge binary verified on disk with valid file version.
  - `test_f2_02_edge_headless_flag_support`: Verifies `--headless=new`, `--window-size=1920,1080`, `--virtual-time-budget=3000`, `--hide-scrollbars`.
  - `test_f2_03_edge_capture_root_grove_1080p`: Headless capture of 3D Voxel Canvas (`/`) yields valid 1920x1080 PNG header ($> 20$ KB).
  - `test_f2_04_edge_capture_evolution_portal_1080p`: Headless capture of Evolution Portal (`/evolution`) yields valid 1920x1080 PNG header.
  - `test_f2_05_edge_capture_process_isolation_and_no_orphans`: Verifies isolated `--user-data-dir` and clean process exit.
- **Tier 2 Boundary Tests**:
  - `test_f2_b1_zero_byte_png_detection`: Zero-byte and corrupted PNG data rejected by header validation.
  - `test_f2_b2_capture_unreachable_port_clean_exit`: Capture of unreachable port exits cleanly without hanging host.
  - `test_f2_b3_virtual_time_budget_zero_vs_large`: Both 0ms and 1500ms virtual time budgets terminate and generate valid PNGs.
  - `test_f2_b4_custom_viewport_resolution_boundaries`: Viewports like 800x600 accurately reflect in PNG IHDR dimensions.
  - `test_f2_b5_output_directory_auto_creation`: Deeply nested non-existent output paths handled cleanly.

### F3: Static Route Mounting & 404 Fix
*Mount screenshot storage directory in FastAPI (`server.py`) so `/screenshots/*` are served with HTTP 200.*
- **Tier 1 Tests**:
  - `test_f3_01_static_css_route_served`: `GET /static/style.css` returns HTTP 200.
  - `test_f3_02_screenshots_route_mounted`: `/screenshots/` route mounted in FastAPI.
  - `test_f3_03_existing_screenshots_served`: Existing screenshot PNGs served with HTTP 200 and `image/png` media type.
  - `test_f3_04_new_screenshot_served_after_placement`: Placing fixture PNG in screenshots folder serves verbatim bytes over HTTP.
  - `test_f3_05_screenshots_traversal_prevention`: Traversal attacks (`../`) rejected (HTTP 400/403/404).
- **Tier 2 Boundary Tests**:
  - `test_f3_b1_missing_screenshot_returns_404`: Non-existent screenshot returns clean 404, not 500 error.
  - `test_f3_b2_path_traversal_dot_dot_rejected`: Path traversal attempts do not leak server source code.
  - `test_f3_b3_non_png_extension_in_screenshots_handled`: Non-image files return 404 or are rejected.
  - `test_f3_b4_empty_filename_rejected`: `/screenshots/` does not leak directory indexing.
  - `test_f3_b5_url_special_characters_escaping`: Encoded characters (`%20`, `%23`) handled safely by router.

### F4: Interactive Visual Evolution Gallery
*Dynamic gallery on `/evolution` with epoch badges, timestamps, zoom/lightbox preview modal.*
- **Tier 1 Tests**:
  - `test_f4_01_evolution_portal_serves_html`: `GET /evolution` returns HTTP 200 HTML with `#gallery` section.
  - `test_f4_02_evolution_gallery_grid_present`: DOM contains `.gallery-grid` container.
  - `test_f4_03_evolution_gallery_cards_have_badges_and_timestamps`: Gallery cards display epoch badges and metadata.
  - `test_f4_04_gallery_artifacts_api_contract`: `GET /api/context/artifacts` returns JSON array with artifact metadata.
  - `test_f4_05_gallery_zoom_preview_structure`: Page contains zoom preview / lightbox interaction markup.
- **Tier 2 Boundary Tests**:
  - `test_f4_b1_empty_artifacts_list_handled`: Empty artifacts list returns clean `[]` JSON without null pointer exceptions.
  - `test_f4_b2_corrupted_metadata_json_handled`: Corrupted `metadata_json` in database row does not fail query.
  - `test_f4_b3_large_artifacts_payload_latency`: Querying 100+ artifacts finishes in $< 500$ ms.
  - `test_f4_b4_xss_sanitization_in_artifact_names`: Script injection in artifact names escaped cleanly.
  - `test_f4_b5_lightbox_missing_image_resilience`: Image 404 does not crash gallery script execution.

### F5: Markdown Snapshot Image Synchronization
*Link & embed newly captured screenshots (`![alt](path)`) into 5-minute context snapshots in `.agents/context/snapshots/`.*
- **Tier 1 Tests**:
  - `test_f5_01_snapshots_directory_populated`: `.agents/context/snapshots/` exists and contains markdown files.
  - `test_f5_02_snapshot_markdown_embed_syntax`: Snapshots contain markdown image embed syntax `![alt](path)`.
  - `test_f5_03_snapshot_referenced_images_exist`: Embedded image paths resolve to valid files on disk.
  - `test_f5_04_snapshot_cron_script_exists_and_valid`: `.agents/context/context_cron_markdown.py` is valid Python AST.
  - `test_f5_05_latest_context_snapshot_sync`: `.agents/context/latest_context_snapshot.md` is updated and populated.
- **Tier 2 Boundary Tests**:
  - `test_f5_b1_empty_snapshots_dir_handling`: Parser handles empty snapshots folder without raising StopIteration.
  - `test_f5_b2_special_characters_in_markdown_image_links`: Image links with timestamps and underscores parse cleanly.
  - `test_f5_b3_snapshot_immutability`: Snapshots retain unique timestamped filenames.
  - `test_f5_b4_malformed_snapshot_parsing`: Truncated or malformed Markdown image syntax does not cause exceptions.
  - `test_f5_b5_relative_vs_absolute_paths_in_markdown`: Markdown embeds use relative paths without hardcoded drive letters.

### F6: SQLite Context Persistence & WAL Hardening
*Register screenshots with dimensions & sizes in `artifacts` table; enforce WAL mode and remove DDL from GET path.*
- **Tier 1 Tests**:
  - `test_f6_01_sqlite_database_exists`: `sanctuary_context.db` exists with non-zero size.
  - `test_f6_02_sqlite_wal_pragmas_enforced`: `PRAGMA journal_mode` is `wal`, `busy_timeout` $\ge 5000$.
  - `test_f6_03_sqlite_artifacts_table_schema`: Table contains all mandatory contract columns.
  - `test_f6_04_sqlite_artifacts_contain_dimensions_metadata`: Screenshot rows store width=1920, height=1080.
  - `test_f6_05_sqlite_no_ddl_on_read_contract`: Read queries execute without altering `schema_version`.
- **Tier 2 Boundary Tests**:
  - `test_f6_b1_sqlite_concurrent_writer_lock_resilience`: Multi-threaded concurrent writes in WAL mode produce 0 lock errors.
  - `test_f6_b2_sqlite_zero_byte_file_insertion_validation`: Artifact validation enforces positive file size.
  - `test_f6_b3_sqlite_missing_mandatory_fields_rejected`: NULL in NOT NULL column raises `sqlite3.IntegrityError`.
  - `test_f6_b4_sqlite_large_metadata_payload`: 32KB JSON payload in `metadata_json` stores and retrieves accurately.
  - `test_f6_b5_sqlite_busy_timeout_pragmas_effective`: `PRAGMA busy_timeout` returns configured threshold.

### F7: LaTeX Monograph Benchmark & Figure Sync
*Add `\begin{figure}` and `\includegraphics` to `silicon_sanctuary_report.tex` and compile PDF with multi-epoch benchmarks.*
- **Tier 1 Tests**:
  - `test_f7_01_latex_report_tex_exists`: `silicon_sanctuary_report.tex` exists and is non-empty.
  - `test_f7_02_latex_includes_graphicx`: Source file includes `\usepackage{graphicx}`.
  - `test_f7_03_latex_figures_and_includegraphics`: Document embeds figures using `\includegraphics`.
  - `test_f7_04_latex_empirical_benchmarks`: Document includes empirical benchmark tables (3,859.75 MB RAM).
  - `test_f7_05_latex_pdf_endpoint_served`: `/docs/latex/silicon_sanctuary_report.pdf` serves compiled PDF (%PDF-).
- **Tier 2 Boundary Tests**:
  - `test_f7_b1_latex_missing_figure_path_detection`: Graphic inclusion paths resolve to valid files.
  - `test_f7_b2_latex_special_characters_escaped`: Underscores in text body are escaped or protected.
  - `test_f7_b3_latex_corrupted_pdf_detection`: PDF header validated for `%PDF-` signature and $> 5$ KB size.
  - `test_f7_b4_latex_empty_benchmarks_graceful_fallback`: Tabular environments structured properly.
  - `test_f7_b5_latex_pdf_endpoint_404_if_missing`: Missing PDF path returns clean HTTP 404.

### F8: 2-Minute Autonomous Cron Stability
*Continuous 2-minute documentation daemon running cleanly alongside 1-second heartbeat without port or lock contention.*
- **Tier 1 Tests**:
  - `test_f8_01_heartbeat_liveness_pulse`: `heartbeat.json` updated recently by 1-second heartbeat.
  - `test_f8_02_visual_doc_capture_script_syntax`: `visual_doc_capture.py` compiles without syntax errors.
  - `test_f8_03_cron_concurrency_no_port_contention`: Visual capture runner probes port 8000 safely.
  - `test_f8_04_cron_concurrency_no_db_locks`: DB operations succeed during active heartbeat pulse.
  - `test_f8_05_cron_runner_dry_run_or_once`: Capture script supports `--help` and `--once` execution.
- **Tier 2 Boundary Tests**:
  - `test_f8_b1_cron_overlap_prevention`: Single-instance PID lock verification.
  - `test_f8_b2_cron_subprocess_timeout_enforcement`: Timeout guards enforced on hanging child processes.
  - `test_f8_b3_cron_heartbeat_skew_resilience`: Heartbeat timestamps formatted with ISO-8601.
  - `test_f8_b4_cron_disk_space_guard`: Host disk verified for $> 1$ GB headroom.
  - `test_f8_b5_cron_orphan_process_cleanup_guarantee`: Process tree cleanup verified with psutil.

---

## 4. Cross-Feature Combinations (Tier 3)

The cross-feature combination suite validates interactions between pairs and triples of subsystems:

1. **Combo 1 (`test_tier3_combo1_restart_and_capture`)**: F1 (Server Freshness) + F2 (Edge Capture). Polling heartbeat liveness, verifying port 8000, and immediately capturing 1080p canvas snapshot.
2. **Combo 2 (`test_tier3_combo2_capture_and_gallery_mounting`)**: F2 (Edge Capture) + F3 (Route Mounting) + F4 (Gallery). Capturing a screenshot, placing it in the screenshots directory, verifying HTTP 200 via `/screenshots/{filename}`, and verifying `/evolution` renders the gallery.
3. **Combo 3 (`test_tier3_combo3_capture_and_db_registration`)**: F2 (Edge Capture) + F6 (SQLite Persistence). Capturing screenshot, parsing 1920x1080 IHDR header, registering in `artifacts` table, and querying back row.
4. **Combo 4 (`test_tier3_combo4_db_registration_and_markdown_embed`)**: F6 (SQLite Persistence) + F5 (Markdown Sync). Validating that artifacts registered in SQLite match `![alt](path)` tags in generated Markdown snapshots.
5. **Combo 5 (`test_tier3_combo5_markdown_and_gallery_sync`)**: F5 (Markdown Sync) + F4 (Gallery). Verifying consistency between latest context snapshot and web gallery assets.
6. **Combo 6 (`test_tier3_combo6_db_benchmarks_and_latex_sync`)**: F6 (SQLite Benchmarks) + F7 (LaTeX Monograph). Cross-verifying empirical compaction metrics in database against numbers cited in LaTeX report.
7. **Combo 7 (`test_tier3_combo7_2min_daemon_heartbeat_and_server_concurrency`)**: F8 (Daemon) + F1 (Server Freshness) + F6 (SQLite Concurrency). Concurrent heartbeat polling and DB reads without port collisions or database locking.

---

## 5. Real-World Application Scenarios (Tier 4)

1. **Scenario 1 (`test_tier4_scenario1_full_autonomous_documentation_cycle`)**: Complete autonomous documentation lifecycle: probe server -> capture `/` at 1080p -> capture `/evolution` at 1080p -> validate PNG IHDR -> register in SQLite -> verify rows.
2. **Scenario 2 (`test_tier4_scenario2_multi_epoch_evolution_simulation`)**: Multi-epoch progression: verify both Epoch 0 and Epoch 1 artifacts exist, are delineated in SQLite, and render with badges on `/evolution`.
3. **Scenario 3 (`test_tier4_scenario3_continuous_cadence_simulation_no_orphans`)**: Cadence stability: executes consecutive captures separated by 1-second interval, verifies distinct timestamps, and confirms 0 orphaned `msedge.exe` processes.
4. **Scenario 4 (`test_tier4_scenario4_latex_monograph_artifact_verification`)**: Monograph synchronicity: verifies `silicon_sanctuary_report.pdf` is served via HTTP 200 with `%PDF-` header and matches live visual and benchmark artifacts.
5. **Scenario 5 (`test_tier4_scenario5_stress_concurrency_during_capture`)**: High-frequency telemetry stress: bombards `/api/heartbeat` and `/api/city/status` every 50ms while Edge captures 1080p canvas; asserts zero HTTP drops and 100% capture fidelity.

---

## 6. Progressive Testability Framework

To accommodate the project's multi-milestone evolution:
- **Milestone Detection**: Tests use `check_milestone_capability(milestone, condition, reason)` in `conftest.py`.
- **Progressive Mode (Default, `STRICT_E2E=0`)**: When a target capability belongs to a future milestone (e.g. M2 `/screenshots` mount, M3 WAL mode, M3 LaTeX figures), the test records a clean `[ SKIP ]` status with the target milestone.
- **Strict Verification Mode (`STRICT_E2E=1`)**: Triggered via `--strict` flag on `test_runner.py` for Milestone M5 final gate. All skips are converted into strict assertion failures, guaranteeing 100% test completion prior to delivery.

---

## 7. How to Run the Tests

### Using Master Test Runner (`test_runner.py`)
```bash
# Run entire test suite across all Tiers (1-4)
python tests/e2e/test_runner.py --all

# Run specific tier
python tests/e2e/test_runner.py --tier 1
python tests/e2e/test_runner.py --tier 2
python tests/e2e/test_runner.py --tier 3
python tests/e2e/test_runner.py --tier 4

# Filter by feature
python tests/e2e/test_runner.py --feature F1
python tests/e2e/test_runner.py --feature F2

# Run in strict mode (enforce 100% milestone completion)
python tests/e2e/test_runner.py --all --strict

# Export structured JSON report
python tests/e2e/test_runner.py --all --json-report tests/e2e/reports/test_results.json
```

### Using Pytest Directly
```bash
# Standard pytest invocation
pytest tests/e2e/ -v

# Filter by tier file
pytest tests/e2e/test_tier1_features.py -v
pytest tests/e2e/test_tier2_boundaries.py -v
pytest tests/e2e/test_tier3_combinations.py -v
pytest tests/e2e/test_tier4_scenarios.py -v

# Strict mode via environment variable
STRICT_E2E=1 pytest tests/e2e/ -v
```

### Exit Codes
- **`0`**: All executed tests passed (or cleanly skipped pending milestones).
- **`1`**: One or more assertions failed.
- **`2`**: Harness initialization or command syntax error.
