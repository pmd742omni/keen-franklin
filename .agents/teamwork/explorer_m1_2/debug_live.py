import subprocess
import tempfile
from pathlib import Path
import shutil
import time

edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
work_dir = Path(r"c:\Users\ignaz\antigravity\keen-franklin\.agents\teamwork\explorer_m1_2")
log_file = work_dir / "edge_live_debug.log"
out_png = work_dir / "edge_live_debug.png"
if log_file.exists():
    log_file.unlink()
if out_png.exists():
    out_png.unlink()

profile_dir = tempfile.mkdtemp(prefix="edge_dbg_live_")

cmd = [
    edge_path,
    "--headless=new",
    "--enable-logging",
    f"--log-file={log_file}",
    "--v=1",
    "--window-size=1920,1080",
    "--virtual-time-budget=3000",
    "--hide-scrollbars",
    "--no-first-run",
    "--no-default-browser-check",
    f"--user-data-dir={profile_dir}",
    f"--screenshot={out_png}",
    "http://127.0.0.1:8000/"
]

print("Launching Edge to capture http://127.0.0.1:8000/ with debug log...")
p = subprocess.Popen(cmd)
t0 = time.time()
while time.time() - t0 < 35:
    if out_png.exists() and out_png.stat().st_size > 0:
        print(f"PNG appeared at {time.time() - t0:.2f}s! Size: {out_png.stat().st_size}")
        break
    time.sleep(1)

try:
    subprocess.run(["taskkill", "/F", "/T", "/PID", str(p.pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
except:
    pass

print("Log exists:", log_file.exists())
if log_file.exists():
    print("Log content:")
    print(log_file.read_text(encoding="utf-8", errors="replace")[:2500])

print("PNG exists:", out_png.exists())
if out_png.exists():
    print("PNG size:", out_png.stat().st_size)

shutil.rmtree(profile_dir, ignore_errors=True)
