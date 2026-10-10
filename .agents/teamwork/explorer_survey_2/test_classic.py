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
        try:
            p.kill()
        except:
            pass

time.sleep(1)

out_img = Path(r"c:\Users\ignaz\antigravity\keen-franklin\.agents\teamwork\explorer_survey_2\test_captures\classic_test.png")
if out_img.exists():
    out_img.unlink()

temp_dir = tempfile.mkdtemp(prefix="classic_edge_")

# Test 1: Classic --headless (not --headless=new)
cmd = [
    edge_bin,
    f"--user-data-dir={temp_dir}",
    "--headless",
    "--disable-gpu",
    "--no-sandbox",
    f"--screenshot={out_img}",
    "about:blank"
]

print("Launching Classic --headless...")
t0 = time.time()
try:
    proc = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10)
    print(f"Classic --headless finished in {time.time()-t0:.2f}s, returncode={proc.returncode}")
    print(f"Created: {out_img.exists()}, size: {out_img.stat().st_size if out_img.exists() else 0}")
except subprocess.TimeoutExpired:
    print("Classic --headless TIMED OUT!")
    for p in psutil.process_iter(['name']):
        if p.info['name'] == 'msedge.exe':
            try: p.kill()
            except: pass

shutil.rmtree(temp_dir, ignore_errors=True)
