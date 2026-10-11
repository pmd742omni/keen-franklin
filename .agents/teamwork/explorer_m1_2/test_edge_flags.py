import subprocess
import tempfile
from pathlib import Path
import shutil
import time

edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
work_dir = Path(r"c:\Users\ignaz\antigravity\keen-franklin\.agents\teamwork\explorer_m1_2")

test_cases = [
    # Test 1: Minimal headless screenshot
    {
        "name": "minimal_headless",
        "flags": ["--headless=new", "--no-first-run", "--no-default-browser-check"]
    },
    # Test 2: Standard headless with window-size
    {
        "name": "window_size",
        "flags": ["--headless=new", "--window-size=1920,1080", "--hide-scrollbars", "--no-first-run", "--no-default-browser-check"]
    },
    # Test 3: With virtual-time-budget
    {
        "name": "virtual_time",
        "flags": ["--headless=new", "--window-size=1920,1080", "--virtual-time-budget=3000", "--hide-scrollbars", "--no-first-run", "--no-default-browser-check"]
    },
    # Test 4: With disable-gpu
    {
        "name": "disable_gpu",
        "flags": ["--headless=new", "--window-size=1920,1080", "--disable-gpu", "--hide-scrollbars", "--no-first-run", "--no-default-browser-check"]
    },
]

url = "https://example.com"

for tc in test_cases:
    out_file = work_dir / f"test_{tc['name']}.png"
    if out_file.exists():
        out_file.unlink()
    profile_dir = tempfile.mkdtemp(prefix=f"edge_test_{tc['name']}_")
    
    cmd = [
        edge_path,
        *tc["flags"],
        f"--user-data-dir={profile_dir}",
        f"--screenshot={out_file}",
        url
    ]
    print(f"=== Running test case: {tc['name']} ===")
    t0 = time.time()
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=12)
        elapsed = time.time() - t0
        print(f"Elapsed: {elapsed:.2f}s, ReturnCode: {proc.returncode}")
        print(f"File exists: {out_file.exists()}, Size: {out_file.stat().st_size if out_file.exists() else 0}")
        if proc.stdout:
            print("Stdout:", proc.stdout.strip())
        if proc.stderr:
            print("Stderr:", proc.stderr.strip()[:300])
    except subprocess.TimeoutExpired:
        print(f"TIMED OUT after 12s!")
    finally:
        shutil.rmtree(profile_dir, ignore_errors=True)
