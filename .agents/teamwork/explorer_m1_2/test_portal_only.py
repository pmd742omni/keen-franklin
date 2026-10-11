import subprocess
import tempfile
from pathlib import Path
import shutil
import time

edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
work_dir = Path(r"c:\Users\ignaz\antigravity\keen-franklin\.agents\teamwork\explorer_m1_2")
out_png = work_dir / "edge_portal_test.png"
log_file = work_dir / "edge_portal.log"
if out_png.exists():
    out_png.unlink()
if log_file.exists():
    log_file.unlink()

profile_dir = tempfile.mkdtemp(prefix="edge_pt_")

cmd = [
    edge_path,
    "--headless=new",
    "--window-size=1920,1080",
    "--virtual-time-budget=3000",
    "--hide-scrollbars",
    "--no-first-run",
    "--no-default-browser-check",
    "--enable-logging",
    f"--log-file={log_file}",
    f"--user-data-dir={profile_dir}",
    f"--screenshot={out_png}",
    "http://127.0.0.1:8000/evolution"
]

print("Launching Edge to capture evolution portal...")
t0 = time.time()
p = subprocess.Popen(cmd)

found = False
while time.time() - t0 < 35:
    if out_png.exists() and out_png.stat().st_size > 0:
        found = True
        print(f"SUCCESS! Portal screenshot created at {time.time() - t0:.2f}s! Size: {out_png.stat().st_size} bytes")
        break
    time.sleep(0.5)

try:
    subprocess.run(["taskkill", "/F", "/T", "/PID", str(p.pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
except:
    pass

print("Screenshot exists:", out_png.exists())
if out_png.exists():
    print("Screenshot size:", out_png.stat().st_size)

if log_file.exists():
    text = log_file.read_text(encoding="utf-8", errors="replace")
    print("Log lines:", len(text.splitlines()))
    print("PageDiscarding in log?", "Discarding" in text)
    print("Last 1000 chars of log:")
    print(text[-1000:])

shutil.rmtree(profile_dir, ignore_errors=True)
