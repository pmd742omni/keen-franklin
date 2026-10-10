import psutil
import subprocess
import time
import os
import shutil
import tempfile
from pathlib import Path

edge_bin = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

# Kill orphans first
for p in psutil.process_iter(['name', 'pid']):
    if p.info['name'] == 'msedge.exe':
        try: p.kill()
        except: pass

time.sleep(1)

out_img = Path(r"c:\Users\ignaz\antigravity\keen-franklin\.agents\teamwork\explorer_survey_2\test_captures\sandbox_test.png")
if out_img.exists():
    out_img.unlink()

temp_dir = tempfile.mkdtemp(prefix="sand_edge_")

# Test: Standard flags WITHOUT --no-sandbox and WITHOUT --disable-gpu
cmd = [
    edge_bin,
    f"--user-data-dir={temp_dir}",
    "--headless=new",
    "--no-first-run",
    "--no-default-browser-check",
    f"--screenshot={out_img}",
    "about:blank"
]

print("Launching standard headless=new without no-sandbox...")
t0 = time.time()
try:
    proc = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=12)
    print(f"Finished in {time.time()-t0:.2f}s, returncode={proc.returncode}")
    print(f"Screenshot exists: {out_img.exists()}, size: {out_img.stat().st_size if out_img.exists() else 0}")
except subprocess.TimeoutExpired:
    print("TIMED OUT!")
    for p in psutil.process_iter(['name']):
        if p.info['name'] == 'msedge.exe':
            try: p.kill()
            except: pass

shutil.rmtree(temp_dir, ignore_errors=True)
