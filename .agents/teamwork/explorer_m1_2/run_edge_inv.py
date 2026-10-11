import os
import sys
import time
import subprocess
from pathlib import Path
import tempfile
import shutil

EDGE_BIN = Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")
WORK_DIR = Path(r"c:\Users\ignaz\antigravity\keen-franklin\.agents\teamwork\explorer_m1_2")
log_file = WORK_DIR / "edge_investigation.log"
out_png = WORK_DIR / "edge_investigation.png"

if log_file.exists():
    log_file.unlink()
if out_png.exists():
    out_png.unlink()

profile = tempfile.mkdtemp(prefix="edge_inv_")

cmd = [
    str(EDGE_BIN),
    "--headless=new",
    "--window-size=1920,1080",
    "--virtual-time-budget=3000",
    "--hide-scrollbars",
    "--no-first-run",
    "--no-default-browser-check",
    "--enable-logging=stderr",
    f"--log-file={str(log_file)}",
    "--v=1",
    f"--user-data-dir={profile}",
    f"--screenshot={str(out_png)}",
    "http://127.0.0.1:8000/"
]

print("Launching Edge with logging...")
t0 = time.time()
p = subprocess.Popen(cmd)
while time.time() - t0 < 25.0:
    if out_png.exists() and out_png.stat().st_size > 0:
        print(f"File created at {time.time() - t0:.2f}s! Size: {out_png.stat().st_size}")
        break
    time.sleep(0.5)

subprocess.run(["taskkill", "/F", "/T", "/PID", str(p.pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
shutil.rmtree(profile, ignore_errors=True)

print("Log exists:", log_file.exists())
if log_file.exists():
    print("Log size:", log_file.stat().st_size)
    print("--- LOG CONTENT ---")
    print(log_file.read_text(encoding="utf-8", errors="replace"))
