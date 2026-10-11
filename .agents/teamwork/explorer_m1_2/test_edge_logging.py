import subprocess
import tempfile
from pathlib import Path
import shutil
import time

edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
work_dir = Path(r"c:\Users\ignaz\antigravity\keen-franklin\.agents\teamwork\explorer_m1_2")
log_file = work_dir / "edge_debug.log"
out_png = work_dir / "edge_debug.png"
if log_file.exists():
    log_file.unlink()
if out_png.exists():
    out_png.unlink()

profile_dir = tempfile.mkdtemp(prefix="edge_dbg_")

cmd = [
    edge_path,
    "--headless=new",
    "--enable-logging",
    f"--log-file={log_file}",
    "--v=1",
    "--window-size=1920,1080",
    "--hide-scrollbars",
    "--no-first-run",
    "--no-default-browser-check",
    f"--user-data-dir={profile_dir}",
    f"--screenshot={out_png}",
    "https://example.com"
]

print("Launching Edge with logging...")
p = subprocess.Popen(cmd)
try:
    p.wait(timeout=10)
    print("Process exited cleanly with code:", p.returncode)
except subprocess.TimeoutExpired:
    print("Process timed out after 10s. Checking log and terminating...")
    p.terminate()
    try:
        p.wait(timeout=3)
    except:
        p.kill()

print("Log exists:", log_file.exists())
if log_file.exists():
    print("Log size:", log_file.stat().st_size)
    print("Log preview:")
    print(log_file.read_text(encoding="utf-8", errors="replace")[:1000])

print("PNG exists:", out_png.exists())
shutil.rmtree(profile_dir, ignore_errors=True)
