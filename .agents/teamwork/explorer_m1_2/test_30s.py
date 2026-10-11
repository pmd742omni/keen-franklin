import subprocess
import tempfile
from pathlib import Path
import shutil
import time

edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
work_dir = Path(r"c:\Users\ignaz\antigravity\keen-franklin\.agents\teamwork\explorer_m1_2")
out_png = work_dir / "edge_success_test.png"
if out_png.exists():
    out_png.unlink()

profile_dir = tempfile.mkdtemp(prefix="edge_prof_")

cmd = [
    edge_path,
    "--headless=new",
    "--window-size=1920,1080",
    "--virtual-time-budget=3000",
    "--hide-scrollbars",
    "--no-first-run",
    "--no-default-browser-check",
    f"--user-data-dir={profile_dir}",
    f"--screenshot={out_png}",
    "data:text/html,<html><body style='background:#f472b6;color:#ffffff;display:flex;align-items:center;justify-content:center;height:100vh;font-family:sans-serif;'><h1>Sakura Grove Test Capture</h1></body></html>"
]

print("Launching Edge with 30s timeout...")
t0 = time.time()
p = subprocess.Popen(cmd)
try:
    p.wait(timeout=30)
    elapsed = time.time() - t0
    print(f"Edge EXITED NATURALLY in {elapsed:.2f}s with code: {p.returncode}")
except subprocess.TimeoutExpired:
    elapsed = time.time() - t0
    print(f"Timed out after {elapsed:.2f}s! Terminating...")
    p.terminate()
    try:
        p.wait(timeout=5)
    except:
        p.kill()

print("Screenshot exists:", out_png.exists())
if out_png.exists():
    print("Screenshot size:", out_png.stat().st_size, "bytes")

shutil.rmtree(profile_dir, ignore_errors=True)
