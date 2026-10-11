import subprocess
import tempfile
from pathlib import Path
import shutil
import time

edge_binary = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
temp_capture_dir = Path(r"c:\Users\ignaz\antigravity\keen-franklin\.agents\teamwork\explorer_m1_2")
out_file = temp_capture_dir / "probe_flag_test.png"
if out_file.exists():
    out_file.unlink()
user_data = temp_capture_dir / "edge_user_data_test_f2"

cmd = [
    edge_binary,
    f"--user-data-dir={str(user_data)}",
    "--headless=new",
    "--no-first-run",
    "--no-default-browser-check",
    "--hide-scrollbars",
    "--virtual-time-budget=1000",
    "--window-size=1920,1080",
    f"--screenshot={str(out_file)}",
    "data:text/html,<html><body style='background:teal;'><h1>Ready</h1></body></html>",
]

print("Running test_f2_02 cmd with 45s timeout...")
t0 = time.time()
try:
    res = subprocess.run(cmd, capture_output=True, timeout=45)
    print(f"res.returncode: {res.returncode} in {time.time() - t0:.2f}s")
    print(f"out_file exists: {out_file.exists()}")
    if out_file.exists():
        print(f"out_file size: {out_file.stat().st_size}")
except subprocess.TimeoutExpired:
    print(f"TIMED OUT after {time.time() - t0:.2f}s")
finally:
    shutil.rmtree(user_data, ignore_errors=True)
