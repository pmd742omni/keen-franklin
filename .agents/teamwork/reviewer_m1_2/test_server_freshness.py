import os
import sys
import json
import time
import urllib.request
from pathlib import Path

# Add project root to path
root_dir = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(root_dir / ".agents" / "context"))

import visual_doc_capture as vdc

def get_current_pid():
    pids = vdc.get_pids_on_port(8000)
    return pids[0] if pids else None

def test_heartbeat():
    try:
        req = urllib.request.Request("http://127.0.0.1:8000/api/heartbeat")
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            data = json.loads(resp.read().decode())
            return resp.status, data
    except Exception as e:
        return None, str(e)

def main():
    print("=== Testing Server Freshness & PID Rotation ===")
    
    # 1. Initial State
    initial_pid = get_current_pid()
    print(f"Initial server PID on port 8000: {initial_pid}")
    
    # If not running, boot it first
    if not initial_pid:
        print("Starting initial server...")
        ok = vdc.ensure_server_fresh(force_restart=True, timeout=35.0)
        assert ok, "Failed to start initial server"
        initial_pid = get_current_pid()
        print(f"Booted initial server PID: {initial_pid}")
    
    status, hb_data = test_heartbeat()
    print(f"Initial heartbeat: status={status}, data={hb_data}")
    assert status == 200, f"Expected 200, got {status}"
    
    # 2. Test ensure_server_fresh(force_restart=True)
    print("\nExecuting ensure_server_fresh(force_restart=True)...")
    t0 = time.time()
    fresh_ok = vdc.ensure_server_fresh(force_restart=True, timeout=35.0)
    elapsed = time.time() - t0
    print(f"ensure_server_fresh returned: {fresh_ok} in {elapsed:.2f}s")
    assert fresh_ok, "ensure_server_fresh returned False!"
    
    # 3. Verify PID rotation
    new_pid = get_current_pid()
    print(f"New server PID on port 8000: {new_pid}")
    assert new_pid is not None, "No server running on port 8000 after restart!"
    assert new_pid != initial_pid, f"PID did NOT change! initial={initial_pid}, new={new_pid}"
    print(f"[PASS] PID changed successfully from {initial_pid} -> {new_pid}")
    
    # 4. Verify /api/heartbeat
    status_2, hb_data_2 = test_heartbeat()
    print(f"Post-restart heartbeat: status={status_2}, data={hb_data_2}")
    assert status_2 == 200, f"Expected 200, got {status_2}"
    print("[PASS] /api/heartbeat returned HTTP 200 OK")
    
    # 5. Stress test: Back-to-back restarts to detect WinError 10048 socket collision
    print("\n=== Stress Testing Socket Drain (3 consecutive forced restarts) ===")
    curr_pid = new_pid
    for i in range(1, 4):
        print(f"\nRestart iteration #{i}...")
        t_start = time.time()
        ok_cycle = vdc.ensure_server_fresh(force_restart=True, timeout=35.0)
        t_end = time.time() - t_start
        cycle_pid = get_current_pid()
        print(f"Cycle {i}: success={ok_cycle}, time={t_end:.2f}s, old_pid={curr_pid}, new_pid={cycle_pid}")
        assert ok_cycle, f"Cycle {i} failed!"
        assert cycle_pid != curr_pid, f"Cycle {i}: PID did not change ({curr_pid} == {cycle_pid})"
        st, _ = test_heartbeat()
        assert st == 200, f"Cycle {i}: Heartbeat failed with {st}"
        curr_pid = cycle_pid
        print(f"[PASS] Cycle {i} cleanly rotated PID and passed health check without WinError 10048")

    print("\nALL SERVER FRESHNESS & SOCKET DRAIN TESTS PASSED!")

if __name__ == "__main__":
    main()
