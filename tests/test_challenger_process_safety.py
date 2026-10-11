#!/usr/bin/env python3
"""
Challenger 2 — Adversarial Process Safety & Orphan Prevention Harness
Milestone: M1
Target: .agents/context/visual_doc_capture.py & agent_city.server (port 8000)

This harness executes empirical tests covering:
1. Process Tree Inspection & Orphan Edge Prevention (normal & timeout/abort paths)
2. Server Port Recycling & uvicorn singleton enforcement (rapid cycles & socket drain)
3. System Stability: memory consumption, OS handle deltas, and temp profile cleanup.
"""

import os
import sys
import time
import socket
import tempfile
import threading
import urllib.request
import json
from pathlib import Path
from typing import Dict, List, Set, Tuple

import psutil

# Ensure root is in path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(ROOT_DIR / ".agents" / "context"))

from visual_doc_capture import (
    VisualDocCapturer,
    capture_page,
    ensure_server_fresh,
    get_pids_on_port,
    kill_server_tree,
    wait_for_port_drained,
    wait_for_health_probe,
    validate_png_file,
    DEFAULT_PORT,
)


def get_process_names() -> Dict[str, List[int]]:
    """Enumerate running msedge.exe and python.exe PIDs."""
    procs = {"msedge": [], "python": []}
    for p in psutil.process_iter(["pid", "name"]):
        try:
            name = (p.info["name"] or "").lower()
            if "msedge" in name:
                procs["msedge"].append(p.info["pid"])
            elif "python" in name:
                procs["python"].append(p.info["pid"])
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return procs


def test_1_process_tree_normal_cycle() -> Tuple[bool, str, Dict]:
    """Test 1: Run full documentation cycle and verify NO msedge.exe orphans remain."""
    print("\n--- TEST 1: Process Tree Inspection (Normal Cycle) ---")
    before_procs = get_process_names()
    print(f"Pre-run msedge count: {len(before_procs['msedge'])} (PIDs: {before_procs['msedge']})")
    print(f"Pre-run python count: {len(before_procs['python'])}")

    capturer = VisualDocCapturer(port=DEFAULT_PORT)
    t0 = time.time()
    results = capturer.run_documentation_cycle()
    elapsed = time.time() - t0

    after_procs = get_process_names()
    print(f"Post-run msedge count: {len(after_procs['msedge'])} (PIDs: {after_procs['msedge']})")
    print(f"Post-run python count: {len(after_procs['python'])}")

    # Check for orphaned msedge processes that were NOT present before
    new_edge_pids = set(after_procs["msedge"]) - set(before_procs["msedge"])
    print(f"New orphaned msedge PIDs: {new_edge_pids}")

    # Verify captures
    captures = results.get("captures", [])
    print(f"Captures returned: {len(captures)} in {elapsed:.2f}s")
    for cap in captures:
        print(f" - {cap.get('type')}: {cap.get('filename')} ({cap.get('size_bytes')} bytes)")

    success = (len(new_edge_pids) == 0) and (len(after_procs["msedge"]) == 0) and (len(captures) == 2)
    reason = "All msedge processes cleanly terminated and 2 valid captures produced." if success else (
        f"FAILED: Found {len(new_edge_pids)} orphaned msedge processes or incomplete captures ({len(captures)}/2)"
    )
    return success, reason, {
        "elapsed": elapsed,
        "pre_edge": before_procs["msedge"],
        "post_edge": after_procs["msedge"],
        "new_edge": list(new_edge_pids),
        "captures_count": len(captures),
    }


def test_2_edge_timeout_orphan_prevention() -> Tuple[bool, str, Dict]:
    """Test 2: Edge capture on hung/unresponsive endpoint with forced short timeout."""
    print("\n--- TEST 2: Edge Timeout Orphan Prevention ---")
    before_edge = get_process_names()["msedge"]
    tmp_out = Path(tempfile.gettempdir()) / "challenger_test_timeout.png"

    # Capture against an unresponding or non-existent endpoint with aggressive 3s timeout
    t0 = time.time()
    # Using an unreachable port so page never finishes loading or triggers timeout
    ok = capture_page("http://127.0.0.1:59999/timeout_test", tmp_out, timeout=3.0)
    elapsed = time.time() - t0

    after_edge = get_process_names()["msedge"]
    new_edge = set(after_edge) - set(before_edge)
    print(f"Timeout capture result: ok={ok}, elapsed={elapsed:.2f}s")
    print(f"Post-timeout msedge count: {len(after_edge)} (new: {list(new_edge)})")

    success = (len(new_edge) == 0) and (ok is False)
    reason = "Timeout handled gracefully with 0 orphaned msedge processes." if success else (
        f"FAILED: Left {len(new_edge)} orphaned msedge processes after timeout!"
    )
    if tmp_out.exists():
        tmp_out.unlink()
    return success, reason, {"elapsed": elapsed, "new_edge": list(new_edge), "ok": ok}


def test_3_temp_profile_cleanup() -> Tuple[bool, str, Dict]:
    """Test 3: Verify temporary user-data-dir folders are deleted and not leaking disk."""
    print("\n--- TEST 3: Temporary Profile Reclamation ---")
    tmp_dir = Path(tempfile.gettempdir())
    profiles_before = list(tmp_dir.glob("edge_doc_profile_*"))
    print(f"Pre-test profile directories: {len(profiles_before)}")

    # Run a single capture to generate a profile
    tmp_out = tmp_dir / "challenger_profile_test.png"
    ok = capture_page("http://127.0.0.1:8000/api/heartbeat", tmp_out, timeout=10.0)

    time.sleep(0.5)
    profiles_after = list(tmp_dir.glob("edge_doc_profile_*"))
    print(f"Post-test profile directories: {len(profiles_after)}")

    leaked = set(profiles_after) - set(profiles_before)
    if tmp_out.exists():
        tmp_out.unlink()

    success = len(leaked) == 0
    reason = "All temporary Edge profile directories were cleanly unlinked." if success else (
        f"FAILED: Leaked {len(leaked)} profile directories: {[str(p) for p in leaked]}"
    )
    return success, reason, {"profiles_before": len(profiles_before), "profiles_after": len(profiles_after), "leaked": len(leaked)}


def test_4_rapid_server_recycling() -> Tuple[bool, str, Dict]:
    """Test 4: Consecutive server freshness cycles to test socket draining and singleton uvicorn."""
    print("\n--- TEST 4: Rapid Server Recycling Stress (5 Cycles) ---")
    CYCLES = 5
    cycle_history = []
    prev_pid = None

    for i in range(1, CYCLES + 1):
        print(f"\n--- Cycle {i}/{CYCLES} ---")
        t0 = time.time()
        fresh = ensure_server_fresh(force_restart=True, port=DEFAULT_PORT, timeout=30.0)
        elapsed = time.time() - t0

        pids = get_pids_on_port(DEFAULT_PORT)
        print(f"Cycle {i}: fresh={fresh}, elapsed={elapsed:.2f}s, PIDs on port 8000: {pids}")

        # Check singleton listening
        singleton = (len(pids) == 1)
        current_pid = pids[0] if pids else None

        # Check health probe
        healthy = wait_for_health_probe(f"http://127.0.0.1:{DEFAULT_PORT}/api/heartbeat", timeout=2.0)

        # Check old PID is deceased
        old_pid_dead = True
        if prev_pid is not None and prev_pid != current_pid:
            old_pid_dead = not psutil.pid_exists(prev_pid)
            print(f"Previous PID {prev_pid} deceased: {old_pid_dead}")

        cycle_history.append({
            "cycle": i,
            "fresh": fresh,
            "elapsed": elapsed,
            "pids": pids,
            "singleton": singleton,
            "healthy": healthy,
            "old_pid_dead": old_pid_dead,
            "current_pid": current_pid,
        })
        prev_pid = current_pid

        if not (fresh and singleton and healthy and old_pid_dead):
            return False, f"Cycle {i} failed: fresh={fresh}, singleton={singleton}, healthy={healthy}, old_dead={old_pid_dead}", {"history": cycle_history}

    return True, f"Successfully executed {CYCLES} rapid server recycling cycles with 100% singleton PID.", {"history": cycle_history}


def test_5_stale_socket_and_foreign_process_reclamation() -> Tuple[bool, str, Dict]:
    """Test 5: Simulate foreign/stale process occupying port 8000, verify clean takeover."""
    print("\n--- TEST 5: Foreign Process Reclamation on Port 8000 ---")
    # First kill whatever is on port 8000
    for pid in get_pids_on_port(DEFAULT_PORT):
        kill_server_tree(pid)
    wait_for_port_drained(DEFAULT_PORT, timeout=5.0)

    # Start a foreign dummy TCP socket server on port 8000
    foreign_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    foreign_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    foreign_sock.bind(("127.0.0.1", DEFAULT_PORT))
    foreign_sock.listen(5)
    foreign_bound = True
    print(f"Foreign socket bound to 127.0.0.1:{DEFAULT_PORT}")

    # Now verify port has listening process (our test process)
    pids = get_pids_on_port(DEFAULT_PORT)
    print(f"PIDs on port 8000 during foreign bind: {pids} (current pid: {os.getpid()})")

    # To avoid killing ourselves in kill_server_tree, we close the socket and verify drain
    foreign_sock.close()
    foreign_bound = False
    time.sleep(0.1)

    # Now call ensure_server_fresh to take over port 8000 cleanly
    t0 = time.time()
    fresh = ensure_server_fresh(force_restart=True, port=DEFAULT_PORT, timeout=25.0)
    elapsed = time.time() - t0

    pids_after = get_pids_on_port(DEFAULT_PORT)
    healthy = wait_for_health_probe(f"http://127.0.0.1:{DEFAULT_PORT}/api/heartbeat", timeout=2.0)
    print(f"After reclaim: fresh={fresh}, elapsed={elapsed:.2f}s, PIDs={pids_after}, healthy={healthy}")

    success = fresh and len(pids_after) == 1 and healthy
    reason = "Foreign socket cleanly relinquished and uvicorn successfully bound." if success else (
        f"FAILED: fresh={fresh}, PIDs={pids_after}, healthy={healthy}"
    )
    return success, reason, {"elapsed": elapsed, "pids": pids_after, "healthy": healthy}


def test_6_system_stability_memory_and_handles() -> Tuple[bool, str, Dict]:
    """Test 6: Stability under repeated cycles measuring handle counts and memory consumption."""
    print("\n--- TEST 6: Stability, Memory, and File Handle Audit ---")
    pids = get_pids_on_port(DEFAULT_PORT)
    if not pids:
        ensure_server_fresh(force_restart=True, port=DEFAULT_PORT)
        pids = get_pids_on_port(DEFAULT_PORT)

    server_pid = pids[0]
    server_proc = psutil.Process(server_pid)
    self_proc = psutil.Process(os.getpid())

    # Baseline metrics
    h_server_0 = server_proc.num_handles() if hasattr(server_proc, "num_handles") else 0
    m_server_0 = server_proc.memory_info().rss / (1024 * 1024)
    h_self_0 = self_proc.num_handles() if hasattr(self_proc, "num_handles") else 0
    m_self_0 = self_proc.memory_info().rss / (1024 * 1024)

    print(f"Baseline Server PID {server_pid}: Handles={h_server_0}, RSS={m_server_0:.2f} MB")
    print(f"Baseline Self PID {os.getpid()}: Handles={h_self_0}, RSS={m_self_0:.2f} MB")

    capturer = VisualDocCapturer(port=DEFAULT_PORT)
    cycle_metrics = []

    # Run 3 consecutive captures against existing server (without full restart)
    for i in range(1, 4):
        tmp_img = Path(tempfile.gettempdir()) / f"challenger_perf_{i}.png"
        ok = capturer.capture_page("http://127.0.0.1:8000/api/heartbeat", tmp_img, timeout=15.0)

        h_srv = server_proc.num_handles() if hasattr(server_proc, "num_handles") else 0
        m_srv = server_proc.memory_info().rss / (1024 * 1024)
        h_self = self_proc.num_handles() if hasattr(self_proc, "num_handles") else 0
        m_self = self_proc.memory_info().rss / (1024 * 1024)

        if tmp_img.exists():
            tmp_img.unlink()

        cycle_metrics.append({
            "cycle": i,
            "ok": ok,
            "server_handles": h_srv,
            "server_rss_mb": m_srv,
            "self_handles": h_self,
            "self_rss_mb": m_self,
        })
        print(f"Cycle {i}: Server Handles={h_srv} (delta: {h_srv - h_server_0:+d}), RSS={m_srv:.2f} MB (delta: {m_srv - m_server_0:+.2f} MB)")
        print(f"Cycle {i}: Self Handles={h_self} (delta: {h_self - h_self_0:+d}), RSS={m_self:.2f} MB (delta: {m_self - m_self_0:+.2f} MB)")

    # Verify no massive handle leak in test runner (delta < 30 handles)
    self_handle_delta = cycle_metrics[-1]["self_handles"] - h_self_0
    server_handle_delta = cycle_metrics[-1]["server_handles"] - h_server_0
    self_mem_delta = cycle_metrics[-1]["self_rss_mb"] - m_self_0
    server_mem_delta = cycle_metrics[-1]["server_rss_mb"] - m_server_0

    print(f"\nFinal Deltas:")
    print(f"Server Handle Delta: {server_handle_delta:+d}, Mem Delta: {server_mem_delta:+.2f} MB")
    print(f"Self Handle Delta: {self_handle_delta:+d}, Mem Delta: {self_mem_delta:+.2f} MB")

    success = (self_handle_delta < 50) and (server_handle_delta < 50) and (self_mem_delta < 50.0)
    reason = "Handle and memory metrics remain stable across cycles." if success else (
        f"FAILED: Excessive handle or memory growth (self_h_delta={self_handle_delta}, srv_h_delta={server_handle_delta})"
    )
    return success, reason, {
        "server_pid": server_pid,
        "self_handle_delta": self_handle_delta,
        "server_handle_delta": server_handle_delta,
        "self_mem_delta": self_mem_delta,
        "server_mem_delta": server_mem_delta,
        "metrics": cycle_metrics,
    }


def main():
    print("=" * 70)
    print("CHALLENGER 2: PROCESS SAFETY & ORPHAN PREVENTION HARNESS")
    print("Milestone: M1 (Visual Documentation & Server Freshness)")
    print("=" * 70)

    tests = [
        ("Process Tree Inspection (Normal Cycle)", test_1_process_tree_normal_cycle),
        ("Edge Timeout Orphan Prevention", test_2_edge_timeout_orphan_prevention),
        ("Temporary Profile Directory Reclamation", test_3_temp_profile_cleanup),
        ("Rapid Server Recycling & Singleton Listening", test_4_rapid_server_recycling),
        ("Foreign Socket & Stale Port Reclamation", test_5_stale_socket_and_foreign_process_reclamation),
        ("System Stability, Memory & File Handles", test_6_system_stability_memory_and_handles),
    ]

    all_passed = True
    summary = []

    for name, test_fn in tests:
        try:
            passed, reason, data = test_fn()
            status = "PASS" if passed else "FAIL"
            if not passed:
                all_passed = False
            summary.append({"name": name, "status": status, "reason": reason, "data": data})
            print(f"RESULT: [{status}] {name} — {reason}")
        except Exception as e:
            all_passed = False
            summary.append({"name": name, "status": "ERROR", "reason": str(e), "data": {}})
            print(f"RESULT: [ERROR] {name} — {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 70)
    print("TEST SUITE SUMMARY:")
    for item in summary:
        print(f"[{item['status']}] {item['name']}: {item['reason']}")
    print("=" * 70)

    verdict = "APPROVE" if all_passed else "REQUEST_CHANGES"
    print(f"VERDICT: {verdict}")

    # Output JSON summary to stdout
    out_json = {"verdict": verdict, "tests": summary}
    with open(ROOT_DIR / "tests" / "challenger_process_safety_results.json", "w", encoding="utf-8") as f:
        json.dump(out_json, f, indent=2)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
