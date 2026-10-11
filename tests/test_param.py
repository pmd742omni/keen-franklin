import subprocess
import tempfile
import time
from pathlib import Path
import shutil

edge_bin = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

for url in ["http://127.0.0.1:8000/?screenshot=1", "http://127.0.0.1:8000/"]:
    temp_dir = Path(tempfile.mkdtemp(prefix="test_param_"))
    out_file = temp_dir / "param_shot.png"
    prof_dir = temp_dir / "prof"
    cmd = [
        edge_bin,
        "--headless=new",
        "--window-size=1920,1080",
        "--hide-scrollbars",
        "--no-first-run",
        "--no-default-browser-check",
        f"--user-data-dir={prof_dir}",
        f"--screenshot={out_file}",
        url,
    ]
    print(f"\n--- Testing url: {url} ---")
    t0 = time.time()
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    captured = False
    for i in range(30):
        time.sleep(1.0)
        if out_file.exists() and out_file.stat().st_size > 1000:
            captured = True
            break
        print(f"[{time.time()-t0:.1f}s] waiting...")
    
    elapsed = time.time() - t0
    size = out_file.stat().st_size if out_file.exists() else 0
    print(f"URL: {url} -> Captured: {captured}, Size: {size:,} bytes, Elapsed: {elapsed:.2f}s")
    
    try:
        proc.terminate()
        proc.kill()
    except Exception:
        pass
    subprocess.run(f"taskkill /F /T /PID {proc.pid}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    shutil.rmtree(temp_dir, ignore_errors=True)
