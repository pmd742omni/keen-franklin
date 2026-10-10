import psutil
import subprocess
import time
import os
import shutil
import tempfile
from pathlib import Path

edge_bin = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
print("Edge binary exists:", os.path.exists(edge_bin))

# 1. Kill any existing msedge.exe processes
for p in psutil.process_iter(['name', 'pid']):
    if p.info['name'] == 'msedge.exe':
        try:
            print(f"Killing orphan msedge PID {p.info['pid']}")
            p.kill()
        except Exception as e:
            print(f"Failed to kill: {e}")

time.sleep(1)

# 2. Test running msedge with a dedicated temp directory and --headless
temp_dir = tempfile.mkdtemp(prefix="test_edge_")
out_img = Path(r"c:\Users\ignaz\antigravity\keen-franklin\.agents\teamwork\explorer_survey_2\test_captures\diag_test.png")
if out_img.exists():
    out_img.unlink()

# Command line test
cmd = [
    edge_bin,
    f"--user-data-dir={temp_dir}",
    "--headless=new",
    "--disable-gpu",
    "--no-sandbox",
    "--no-first-run",
    "--no-default-browser-check",
    f"--screenshot={out_img}",
    "about:blank"
]

print("Launching Edge with about:blank...")
t0 = time.time()
proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

try:
    stdout, stderr = proc.communicate(timeout=10)
    print(f"Exited in {time.time() - t0:.2f}s with code {proc.returncode}")
    print(f"Screenshot exists: {out_img.exists()} (size: {out_img.stat().st_size if out_img.exists() else 0})")
    print("Stderr:", stderr.decode(errors='ignore')[:300])
except subprocess.TimeoutExpired:
    print("PROCESS TIMED OUT!")
    # Terminate process tree
    parent = psutil.Process(proc.pid)
    for child in parent.children(recursive=True):
        child.kill()
    parent.kill()
finally:
    try:
        shutil.rmtree(temp_dir, ignore_errors=True)
    except Exception:
        pass
