import subprocess
import tempfile
from pathlib import Path
import shutil
import time

edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
work_dir = Path(r"c:\Users\ignaz\antigravity\keen-franklin\.agents\teamwork\explorer_m1_2")
out_file = work_dir / "test_out.png"

# Test different variations:
# 1. --headless instead of --headless=new
# 2. --no-sandbox
# 3. file URL instead of data URL
sample_html = work_dir / "sample.html"
sample_html.write_text("<!DOCTYPE html><html><body style='background:purple;color:white;'><h1>Edge Diagnostic</h1></body></html>", encoding="utf-8")

variations = [
    ("headless_old", ["--headless"]),
    ("headless_old_gpu_off", ["--headless", "--disable-gpu"]),
    ("headless_new_nosandbox", ["--headless=new", "--no-sandbox", "--disable-gpu"]),
    ("headless_old_nosandbox", ["--headless", "--no-sandbox", "--disable-gpu"]),
]

for name, flags in variations:
    profile_dir = tempfile.mkdtemp(prefix=f"edge_{name}_")
    out_file = work_dir / f"test_{name}.png"
    if out_file.exists():
        out_file.unlink()
    cmd = [
        edge_path,
        *flags,
        "--no-first-run",
        "--no-default-browser-check",
        f"--user-data-dir={profile_dir}",
        f"--screenshot={out_file}",
        sample_html.as_uri()
    ]
    print(f"Testing {name}: {' '.join(cmd)}")
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        stdout, stderr = p.communicate(timeout=8)
        print(f"[{name}] Completed! ReturnCode: {p.returncode}, File exists: {out_file.exists()}, Size: {out_file.stat().st_size if out_file.exists() else 0}")
    except subprocess.TimeoutExpired:
        print(f"[{name}] Timed out. Killing...")
        p.kill()
    finally:
        shutil.rmtree(profile_dir, ignore_errors=True)
