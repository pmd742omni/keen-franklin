import psutil
import subprocess
import time
import os
import shutil
import tempfile
from pathlib import Path

edge_bin = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

# Kill orphans first
for p in psutil.process_iter(['name', 'pid']):
    if p.info['name'] == 'msedge.exe':
        try: p.kill()
        except: pass

time.sleep(1)

log_file = Path(r"c:\Users\ignaz\antigravity\keen-franklin\.agents\teamwork\explorer_survey_2\edge_debug.log")
if log_file.exists():
    log_file.unlink()

temp_dir = tempfile.mkdtemp(prefix="log_edge_")

cmd = [
    edge_bin,
    f"--user-data-dir={temp_dir}",
    "--headless=new",
    "--disable-gpu",
    "--no-sandbox",
    "--enable-logging",
    f"--log-file={log_file}",
    "--v=1",
    "--dump-dom",
    "data:text/html,<h1>Hello</h1>"
]

print("Launching Edge with logging...")
t0 = time.time()
try:
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=6)
    print(f"Finished in {time.time()-t0:.2f}s, returncode={proc.returncode}")
    print("STDOUT:", proc.stdout.decode(errors='ignore')[:300])
    print("STDERR:", proc.stderr.decode(errors='ignore')[:300])
except subprocess.TimeoutExpired:
    print("TIMED OUT!")
    for p in psutil.process_iter(['name']):
        if p.info['name'] == 'msedge.exe':
            try: p.kill()
            except: pass

if log_file.exists():
    print(f"Log file size: {log_file.stat().st_size}")
    print("Log contents:\n", log_file.read_text(errors='ignore')[:1000])
else:
    print("Log file was NOT created!")

shutil.rmtree(temp_dir, ignore_errors=True)
