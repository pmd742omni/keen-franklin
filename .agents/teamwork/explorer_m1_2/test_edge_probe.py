import subprocess
import tempfile
from pathlib import Path
import shutil

work_dir = Path(r"c:\Users\ignaz\antigravity\keen-franklin\.agents\teamwork\explorer_m1_2")
out_png = work_dir / "test_capture.png"
if out_png.exists():
    out_png.unlink()

tmpdir = tempfile.mkdtemp(prefix="edge_profile_")

cmd = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "--headless=new",
    "--window-size=1920,1080",
    "--virtual-time-budget=3000",
    "--hide-scrollbars",
    "--no-first-run",
    "--no-default-browser-check",
    f"--user-data-dir={tmpdir}",
    f"--screenshot={out_png}",
    "data:text/html,<html><body style='background:green;color:white;'><h1>Edge Capture Success</h1></body></html>",
]

print("Launching:", cmd)
proc = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
print("Return code:", proc.returncode)
print("Stdout:", proc.stdout)
print("Stderr:", proc.stderr)
print("Exists:", out_png.exists())
if out_png.exists():
    print("Size bytes:", out_png.stat().st_size)

# Cleanup profile
shutil.rmtree(tmpdir, ignore_errors=True)
