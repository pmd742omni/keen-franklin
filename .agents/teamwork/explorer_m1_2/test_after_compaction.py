import os
import sys
import time
import subprocess
from pathlib import Path
import tempfile
import shutil

EDGE_BIN = Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")
WORK_DIR = Path(r"c:\Users\ignaz\antigravity\keen-franklin\.agents\teamwork\explorer_m1_2")
out_png = WORK_DIR / "post_compaction_portal.png"

if out_png.exists():
    out_png.unlink()

profile = tempfile.mkdtemp(prefix="edge_post_comp_")

cmd = [
    str(EDGE_BIN),
    "--headless=new",
    "--window-size=1920,1080",
    "--virtual-time-budget=3000",
    "--hide-scrollbars",
    "--no-first-run",
    "--no-default-browser-check",
    f"--user-data-dir={profile}",
    f"--screenshot={str(out_png)}",
    "http://127.0.0.1:8000/evolution"
]

print("Launching Edge to capture evolution portal after 3.6GB memory compaction...")
t0 = time.time()
p = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

found = False
while time.time() - t0 < 30.0:
    if out_png.exists() and out_png.stat().st_size > 10000:
        found = True
        print(f"CAPTURED! File size: {out_png.stat().st_size} bytes in {time.time() - t0:.2f}s")
        break
    time.sleep(0.5)

subprocess.run(["taskkill", "/F", "/T", "/PID", str(p.pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
shutil.rmtree(profile, ignore_errors=True)

print("Found PNG:", found)
if out_png.exists():
    import struct
    with open(out_png, "rb") as f:
        data = f.read(24)
        w, h = struct.unpack(">II", data[16:24])
    print(f"Dimensions: {w}x{h}, Size: {out_png.stat().st_size} bytes")
