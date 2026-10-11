import subprocess
import tempfile
from pathlib import Path
import shutil
import time

edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
work_dir = Path(r"c:\Users\ignaz\antigravity\keen-franklin\.agents\teamwork\explorer_m1_2")
out_png = work_dir / "edge_taskkill_test.png"
if out_png.exists():
    out_png.unlink()

profile_dir = tempfile.mkdtemp(prefix="edge_tk_")

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
    "data:text/html,<html><body style='background:#10b981;color:#ffffff;'><h1>Taskkill Test</h1></body></html>"
]

print("Spawning Edge with Popen...")
t0 = time.time()
p = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print(f"Spawned root PID: {p.pid}")

# Wait for screenshot to appear and be non-empty
screenshot_ready = False
max_wait = 25  # seconds
while time.time() - t0 < max_wait:
    if out_png.exists() and out_png.stat().st_size > 0:
        screenshot_ready = True
        print(f"Screenshot detected after {time.time() - t0:.2f}s! Size: {out_png.stat().st_size}")
        break
    time.sleep(0.5)

# Grace period of 1 second for I/O flush
time.sleep(1.0)

# Terminate process tree via taskkill /F /T /PID
print("Killing process tree via taskkill...")
kill_res = subprocess.run(
    ["taskkill", "/F", "/T", "/PID", str(p.pid)],
    capture_output=True,
    text=True
)
print("Taskkill output:", kill_res.stdout.strip())

# Verify no msedge processes remain
time.sleep(0.5)
verify_res = subprocess.run(
    ["powershell", "-NoProfile", "-Command", "Get-Process msedge -ErrorAction SilentlyContinue | Measure-Object | Select-Object -ExpandProperty Count"],
    capture_output=True,
    text=True
)
remaining_count = verify_res.stdout.strip()
print(f"Remaining msedge processes: {remaining_count or 0}")

shutil.rmtree(profile_dir, ignore_errors=True)
print("Temporary user-data-dir cleaned up successfully.")
