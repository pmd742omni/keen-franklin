import subprocess
import tempfile
from pathlib import Path
import shutil
import time

edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
work_dir = Path(r"c:\Users\ignaz\antigravity\keen-franklin\.agents\teamwork\explorer_m1_2")
out_file = work_dir / "test_pipe_test.png"
if out_file.exists():
    out_file.unlink()

profile_dir = tempfile.mkdtemp(prefix="edge_pipe_")
url = "data:text/html,<html><body style='background:blue;color:white;'><h1>DevNull Test</h1></body></html>"

cmd = [
    edge_path,
    "--headless=new",
    "--window-size=1920,1080",
    "--virtual-time-budget=3000",
    "--hide-scrollbars",
    "--no-first-run",
    "--no-default-browser-check",
    f"--user-data-dir={profile_dir}",
    f"--screenshot={out_file}",
    url
]

print("Testing with stdout=DEVNULL, stderr=DEVNULL...")
t0 = time.time()
try:
    proc = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=12)
    elapsed = time.time() - t0
    print(f"Elapsed: {elapsed:.2f}s, ReturnCode: {proc.returncode}")
    print(f"File exists: {out_file.exists()}, Size: {out_file.stat().st_size if out_file.exists() else 0}")
except subprocess.TimeoutExpired:
    print("TIMED OUT even with DEVNULL!")
finally:
    shutil.rmtree(profile_dir, ignore_errors=True)
