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

out_img = Path(r"c:\Users\ignaz\antigravity\keen-franklin\.agents\teamwork\explorer_survey_2\test_captures\test_timing.png")
if out_img.exists():
    out_img.unlink()

# Let's test Edge on http://127.0.0.1:8000/
# Notice: we test with --virtual-time-budget=3000 to allow 3D canvas and dynamic state to settle!
# And window-size=1920,1080 as requested in R1!
temp_dir = tempfile.mkdtemp(prefix="edge_timing_")

cmd = [
    edge_bin,
    f"--user-data-dir={temp_dir}",
    "--headless=new",
    "--no-first-run",
    "--no-default-browser-check",
    "--hide-scrollbars",
    "--virtual-time-budget=3000",
    "--window-size=1920,1080",
    f"--screenshot={out_img}",
    "http://127.0.0.1:8000/"
]

print("Launching Edge capture of Grove with virtual-time-budget=3000 (timeout=45s)...")
t0 = time.time()
try:
    proc = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=45)
    elapsed = time.time() - t0
    print(f"Edge exited with returncode {proc.returncode} in {elapsed:.2f} seconds")
    if out_img.exists():
        size = out_img.stat().st_size
        print(f"SUCCESS! Screenshot created: {out_img} (Size: {size:,} bytes)")
    else:
        print("FAIL: Screenshot file not created!")
except subprocess.TimeoutExpired:
    print(f"TIMEOUT EXPIRED after {time.time() - t0:.2f} seconds!")
    for p in psutil.process_iter(['name']):
        if p.info['name'] == 'msedge.exe':
            try: p.kill()
            except: pass
finally:
    shutil.rmtree(temp_dir, ignore_errors=True)
