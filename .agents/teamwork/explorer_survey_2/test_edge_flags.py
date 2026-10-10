import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

EDGE_BIN = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
OUTPUT_DIR = Path(r"c:\Users\ignaz\antigravity\keen-franklin\.agents\teamwork\explorer_survey_2\test_captures")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

test_scenarios = [
    {
        "name": "grove_basic",
        "url": "http://127.0.0.1:8000/",
        "out": OUTPUT_DIR / "test_grove_basic.png",
        "flags": [
            "--headless=new",
            "--disable-gpu",
            "--no-first-run",
            "--no-default-browser-check",
            "--window-size=1920,1080",
        ]
    },
    {
        "name": "grove_virtual_time_isolated",
        "url": "http://127.0.0.1:8000/",
        "out": OUTPUT_DIR / "test_grove_vt.png",
        "flags": [
            "--headless=new",
            "--disable-gpu",
            "--no-first-run",
            "--no-default-browser-check",
            "--no-sandbox",
            "--hide-scrollbars",
            "--virtual-time-budget=3500",
            "--window-size=1920,1080",
        ]
    },
    {
        "name": "portal_virtual_time_isolated",
        "url": "http://127.0.0.1:8000/evolution",
        "out": OUTPUT_DIR / "test_portal_vt.png",
        "flags": [
            "--headless=new",
            "--disable-gpu",
            "--no-first-run",
            "--no-default-browser-check",
            "--no-sandbox",
            "--hide-scrollbars",
            "--virtual-time-budget=3000",
            "--window-size=1920,1080",
        ]
    }
]

results = []

for sc in test_scenarios:
    temp_dir = tempfile.mkdtemp(prefix="edge_test_data_")
    t0 = time.time()
    cmd = [
        EDGE_BIN,
        f"--user-data-dir={temp_dir}",
        *sc["flags"],
        f"--screenshot={sc['out']}",
        sc["url"]
    ]
    print(f"Running scenario: {sc['name']}")
    try:
        proc = subprocess.run(cmd, capture_output=True, timeout=25)
        elapsed = time.time() - t0
        exists = sc["out"].exists()
        size = sc["out"].stat().st_size if exists else 0
        results.append({
            "scenario": sc["name"],
            "returncode": proc.returncode,
            "elapsed_sec": round(elapsed, 2),
            "output_exists": exists,
            "size_bytes": size,
            "stdout": proc.stdout.decode(errors='ignore').strip()[:200],
            "stderr": proc.stderr.decode(errors='ignore').strip()[:200],
        })
    except subprocess.TimeoutExpired:
        results.append({
            "scenario": sc["name"],
            "error": "TimeoutExpired (25s)"
        })
    finally:
        # Clean up temp user data directory
        try:
            shutil.rmtree(temp_dir, ignore_errors=True)
        except Exception:
            pass

for r in results:
    print(r)
