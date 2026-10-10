import subprocess
import time
from pathlib import Path

edge_bin = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
out_dir = Path(r"c:\Users\ignaz\antigravity\keen-franklin\.agents\teamwork\explorer_survey_2\test_captures")

tests = [
    {
        "name": "about_blank_headless_new",
        "url": "about:blank",
        "flags": ["--headless=new", "--disable-gpu", "--no-first-run", "--no-default-browser-check"]
    },
    {
        "name": "about_blank_headless_old",
        "url": "about:blank",
        "flags": ["--headless", "--disable-gpu", "--no-first-run", "--no-default-browser-check"]
    },
    {
        "name": "about_blank_headless_old_no_sandbox",
        "url": "about:blank",
        "flags": ["--headless", "--disable-gpu", "--no-sandbox", "--no-first-run", "--no-default-browser-check"]
    }
]

for t in tests:
    shot = out_dir / f"{t['name']}.png"
    if shot.exists():
        shot.unlink()
    cmd = [edge_bin, *t["flags"], f"--screenshot={shot}", t["url"]]
    print(f"Testing {t['name']}...")
    t0 = time.time()
    try:
        p = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10)
        elapsed = time.time() - t0
        print(f"  Result: returncode={p.returncode}, elapsed={elapsed:.2f}s, created={shot.exists()}, size={shot.stat().st_size if shot.exists() else 0}")
    except subprocess.TimeoutExpired:
        print(f"  Result: TIMEOUT after 10s!")
