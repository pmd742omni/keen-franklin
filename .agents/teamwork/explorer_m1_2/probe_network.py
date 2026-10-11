import os
import sys
import time
import subprocess
from pathlib import Path
import tempfile
import shutil

EDGE_BIN = Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")
WORK_DIR = Path(r"c:\Users\ignaz\antigravity\keen-franklin\.agents\teamwork\explorer_m1_2")
log_file = WORK_DIR / "edge_probe_run.log"
out_png = WORK_DIR / "edge_probe_run.png"

if log_file.exists():
    log_file.unlink()
if out_png.exists():
    out_png.unlink()

profile = tempfile.mkdtemp(prefix="edge_prb_")

# In Windows, Edge headless sometimes needs --no-sandbox or --proxy-server="direct://" to reach loopback 127.0.0.1
# Let's test with the required user arguments
cmd = [
    str(EDGE_BIN),
    "--headless=new",
    "--window-size=1920,1080",
    "--virtual-time-budget=3000",
    "--hide-scrollbars",
    "--no-first-run",
    "--no-default-browser-check",
    "--enable-logging",
    f"--log-file={str(log_file)}",
    f"--user-data-dir={profile}",
    f"--screenshot={str(out_png)}",
    "http://127.0.0.1:8000/evolution"
]

print("Launching Edge to capture evolution portal...")
t0 = time.time()
p = subprocess.Popen(cmd)

found = False
while time.time() - t0 < 30.0:
    if out_png.exists() and out_png.stat().st_size > 0:
        found = True
        print(f"Captured in {time.time() - t0:.2f}s! Size: {out_png.stat().st_size}")
        break
    time.sleep(0.5)

subprocess.run(["taskkill", "/F", "/T", "/PID", str(p.pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
shutil.rmtree(profile, ignore_errors=True)

print("Found PNG:", found)
if log_file.exists():
    print("Log content:")
    print(log_file.read_text(encoding="utf-8", errors="replace"))
else:
    print("No log file found.")
