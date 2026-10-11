import subprocess
import tempfile
import time
from pathlib import Path
import shutil

edge_bin = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

for vt in [None, 1000, 3000]:
    temp_dir = Path(tempfile.mkdtemp(prefix="vt_test_"))
    out_file = temp_dir / f"test_vt_{vt}.png"
    prof_dir = temp_dir / "prof"
    cmd = [
        edge_bin,
        "--headless=new",
        "--window-size=1920,1080",
        "--hide-scrollbars",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-background-networking",
        f"--user-data-dir={prof_dir}",
        f"--screenshot={out_file}",
    ]
    if vt is not None:
        cmd.append(f"--virtual-time-budget={vt}")
    cmd.append("http://127.0.0.1:8000/")
    
    print(f"\n--- Testing with virtual-time-budget={vt} ---")
    t0 = time.time()
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    captured = False
    for i in range(40):
        time.sleep(1.0)
        if out_file.exists() and out_file.stat().st_size > 1000:
            captured = True
            break
        print(f"[{time.time()-t0:.1f}s] waiting...")
    
    elapsed = time.time() - t0
    size = out_file.stat().st_size if out_file.exists() else 0
    print(f"Result for vt={vt}: captured={captured}, size={size:,} bytes, elapsed={elapsed:.2f}s")
    
    try:
        proc.terminate()
        proc.kill()
    except Exception:
        pass
    subprocess.run(f"taskkill /F /T /PID {proc.pid}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    shutil.rmtree(temp_dir, ignore_errors=True)
