import subprocess
import tempfile
from pathlib import Path
import shutil
import time

edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
work_dir = Path(r"c:\Users\ignaz\antigravity\keen-franklin\.agents\teamwork\explorer_m1_2")
out_png = work_dir / "edge_poll_test.png"
if out_png.exists():
    out_png.unlink()

profile_dir = tempfile.mkdtemp(prefix="edge_poll_")

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
    "data:text/html,<html><body style='background:#10b981;color:#ffffff;'><h1>Poll Test</h1></body></html>"
]

print("Launching Edge and polling for file creation...")
t0 = time.time()
p = subprocess.Popen(cmd)

found_time = None
while time.time() - t0 < 30:
    if out_png.exists() and out_png.stat().st_size > 0:
        found_time = time.time() - t0
        print(f"SCREENSHOT CREATED at {found_time:.2f}s! Size: {out_png.stat().st_size} bytes")
        break
    time.sleep(0.5)

# Now check if Edge exits on its own after screenshot was created
if found_time:
    print(f"Waiting to see if Edge exits on its own within 5 seconds...")
    try:
        p.wait(timeout=5)
        print(f"Edge exited on its own at {time.time() - t0:.2f}s with code {p.returncode}")
    except subprocess.TimeoutExpired:
        print(f"Edge did NOT exit on its own after screenshot creation! Still alive.")
        p.terminate()
        try:
            p.wait(timeout=3)
        except:
            p.kill()

shutil.rmtree(profile_dir, ignore_errors=True)
