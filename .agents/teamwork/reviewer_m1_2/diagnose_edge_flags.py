import subprocess
import time
import os
import shutil
from pathlib import Path

edge_bin = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
out_dir = Path(r"c:\Users\ignaz\antigravity\keen-franklin\.agents\teamwork\reviewer_m1_2").resolve()

flag_sets = {
    "set_worker": [
        "--headless=new",
        "--window-size=1920,1080",
        "--virtual-time-budget=3000",
        "--hide-scrollbars",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-background-networking",
    ],
    "set_no_net_disable": [
        "--headless=new",
        "--window-size=1920,1080",
        "--virtual-time-budget=3000",
        "--hide-scrollbars",
        "--no-first-run",
        "--no-default-browser-check",
    ],
    "set_no_virtual_time": [
        "--headless=new",
        "--window-size=1920,1080",
        "--hide-scrollbars",
        "--no-first-run",
        "--no-default-browser-check",
    ],
    "set_old_headless": [
        "--headless",
        "--window-size=1920,1080",
        "--hide-scrollbars",
        "--no-first-run",
        "--no-default-browser-check",
    ]
}

for name, flags in flag_sets.items():
    out_png = out_dir / f"test_{name}.png"
    if out_png.exists():
        out_png.unlink()
    profile = out_dir / f"prof_{name}"
    shutil.rmtree(profile, ignore_errors=True)
    profile.mkdir()
    
    cmd = [
        edge_bin,
        *flags,
        f"--user-data-dir={str(profile)}",
        f"--screenshot={str(out_png)}",
        "http://127.0.0.1:8000/"
    ]
    print(f"\n--- Testing {name} ---")
    t0 = time.time()
    p = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    created = False
    while time.time() - t0 < 15:
        if out_png.exists() and out_png.stat().st_size > 1000:
            print(f"[{name}] SUCCESS in {time.time() - t0:.2f}s! Size: {out_png.stat().st_size}")
            created = True
            break
        time.sleep(0.5)
    
    if not created:
        print(f"[{name}] FAILED after 15s")
        
    subprocess.run(["taskkill", "/F", "/T", "/PID", str(p.pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    shutil.rmtree(profile, ignore_errors=True)
