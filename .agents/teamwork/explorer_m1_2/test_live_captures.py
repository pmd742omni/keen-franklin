import subprocess
import tempfile
import time
from pathlib import Path
import shutil
import struct

def get_png_dimensions(filepath):
    """Read width and height directly from PNG header (IHDR chunk)."""
    with open(filepath, "rb") as f:
        data = f.read(24)
        if len(data) >= 24 and data[:8] == b"\x89PNG\r\n\x1a\n":
            w, h = struct.unpack(">II", data[16:24])
            return w, h
    return None, None

edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
work_dir = Path(r"c:\Users\ignaz\antigravity\keen-franklin\.agents\teamwork\explorer_m1_2")

targets = [
    ("grove", "http://127.0.0.1:8000/"),
    ("portal", "http://127.0.0.1:8000/evolution"),
]

for label, url in targets:
    out_png = work_dir / f"test_live_{label}.png"
    if out_png.exists():
        out_png.unlink()
    profile_dir = tempfile.mkdtemp(prefix=f"edge_test_{label}_")

    cmd = [
        edge_path,
        "--headless=new",
        "--window-size=1920,1080",
        "--virtual-time-budget=3000",
        "--hide-scrollbars",
        "--no-first-run",
        "--no-default-browser-check",
        f"--user-data-dir={profile_dir}",
        f"--screenshot={out_png}",
        url
    ]

    print(f"\n==========================================")
    print(f"Capturing {label} from {url}")
    print(f"Command: {' '.join(cmd)}")
    t0 = time.time()
    p = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"Spawned PID: {p.pid}")

    max_wait = 25  # seconds
    captured = False
    while time.time() - t0 < max_wait:
        if out_png.exists() and out_png.stat().st_size > 5000:
            captured = True
            break
        time.sleep(0.5)

    duration = time.time() - t0
    print(f"File created: {captured} in {duration:.2f}s")

    # Give 0.5s for write flush
    time.sleep(0.5)

    # Process cleanup
    try:
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(p.pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        print(f"Taskkill error: {e}")

    # Verify PNG
    if out_png.exists():
        size = out_png.stat().st_size
        w, h = get_png_dimensions(out_png)
        print(f"Artifact: {out_png.name}, Size: {size} bytes, Dimensions: {w}x{h}")
    else:
        print(f"FAILED to capture {label}")

    shutil.rmtree(profile_dir, ignore_errors=True)
