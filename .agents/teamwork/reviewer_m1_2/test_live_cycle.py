import subprocess
import time
import os
import shutil
import urllib.request
from pathlib import Path

# 1. Start server using ensure_server_fresh
import sys
sys.path.insert(0, ".agents/context")
import visual_doc_capture as vdc

print("Ensuring server is fresh...")
fresh = vdc.ensure_server_fresh(force_restart=True, timeout=35.0)
print("ensure_server_fresh:", fresh)

# Verify heartbeat
try:
    with urllib.request.urlopen("http://127.0.0.1:8000/api/heartbeat", timeout=3.0) as resp:
        print("Heartbeat status:", resp.status)
except Exception as e:
    print("Heartbeat error:", e)

# 2. Test Edge capture on root
edge_bin = vdc.find_edge_binary()
print("Edge binary:", edge_bin)
out_png = Path("test_edge_fresh_capture.png").resolve()
if out_png.exists():
    out_png.unlink()

ok = vdc.capture_page("http://127.0.0.1:8000/", out_png, timeout=45.0)
print("vdc.capture_page result:", ok)
print("File exists:", out_png.exists())
if out_png.exists():
    print("File size:", out_png.stat().st_size)
    val = vdc.validate_png_file(out_png)
    print("Validation:", val)
