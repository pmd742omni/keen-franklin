import subprocess
import time
from pathlib import Path

edge_bin = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
out_file = Path(r"c:\Users\ignaz\antigravity\keen-franklin\debug_capture.png")
if out_file.exists():
    out_file.unlink()

args_list = ["--headless=new", "--window-size=1920,1080", f"--screenshot={out_file}", "http://127.0.0.1:8000/"]
args_str = ",".join(f"'{a}'" for a in args_list)
ps_cmd = [
    "powershell",
    "-NoProfile",
    "-Command",
    f"Start-Process '{edge_bin}' -ArgumentList {args_str} -Wait"
]

print("Launching Start-Process via python with 50s timeout...")
t0 = time.time()
res = subprocess.run(ps_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=50)
print(f"Finished in {time.time() - t0:.2f}s, RC: {res.returncode}")
print(f"Exists: {out_file.exists()}, Size: {out_file.stat().st_size if out_file.exists() else 0}")
