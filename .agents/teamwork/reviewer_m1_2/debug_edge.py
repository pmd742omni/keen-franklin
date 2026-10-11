import subprocess
import time
import os
import shutil
from pathlib import Path

edge_bin = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
if not os.path.exists(edge_bin):
    edge_bin = r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"
print(f"Edge bin: {edge_bin}, exists: {os.path.exists(edge_bin)}")

out_png = Path("test_probe_edge.png").resolve()
if out_png.exists():
    out_png.unlink()

temp_p = Path("test_edge_prof").resolve()
shutil.rmtree(temp_p, ignore_errors=True)
temp_p.mkdir()

cmd = [
    edge_bin,
    "--headless=new",
    "--window-size=1920,1080",
    "--virtual-time-budget=3000",
    "--hide-scrollbars",
    "--no-first-run",
    "--no-default-browser-check",
    "--disable-background-networking",
    f"--user-data-dir={str(temp_p)}",
    f"--screenshot={str(out_png)}",
    "http://127.0.0.1:8000/",
]

print("Running command:", " ".join(cmd))
t0 = time.time()
p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
try:
    stdout, stderr = p.communicate(timeout=30)
    print("Return code:", p.returncode)
    print("STDOUT:", stdout.decode(errors='ignore'))
    print("STDERR:", stderr.decode(errors='ignore'))
except subprocess.TimeoutExpired:
    print("Timed out waiting for process!")
    p.kill()

print("File exists:", out_png.exists())
if out_png.exists():
    print("File size:", out_png.stat().st_size)
