import subprocess
import time
import os
from pathlib import Path

edge_bin = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
out_img = Path(r"c:\Users\ignaz\antigravity\keen-franklin\.agents\teamwork\explorer_survey_2\test_captures\test_grove_direct.png")
out_img.parent.mkdir(parents=True, exist_ok=True)
if out_img.exists():
    out_img.unlink()

# Let's test Edge flags:
# Notice: we redirect stdout and stderr to DEVNULL to avoid pipe hang on Windows!
cmd = [
    edge_bin,
    "--headless=new",
    "--disable-gpu",
    "--no-sandbox",
    "--hide-scrollbars",
    "--no-first-run",
    "--no-default-browser-check",
    "--window-size=1920,1080",
    f"--screenshot={out_img}",
    "http://127.0.0.1:8000/"
]

print("Launching:", " ".join(cmd))
t0 = time.time()
try:
    proc = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=20)
    elapsed = time.time() - t0
    print(f"Subprocess finished with returncode {proc.returncode} in {elapsed:.2f} seconds")
    if out_img.exists():
        print(f"SUCCESS: Screenshot created! Size = {out_img.stat().st_size} bytes")
    else:
        print("FAIL: Screenshot file was not created!")
except subprocess.TimeoutExpired:
    print("TIMED OUT after 20 seconds!")
