import http.server
import os
import shutil
import socketserver
import subprocess
import tempfile
import threading
import time
from pathlib import Path

# Start a simple stdlib HTTP server on port 8888
class SimpleHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(b"<html><body style='background:lime;'><h1>SIMPLE TEST</h1></body></html>")
    def log_message(self, format, *args):
        pass

PORT = 8888
httpd = socketserver.TCPServer(("127.0.0.1", PORT), SimpleHandler)
t = threading.Thread(target=httpd.serve_forever, daemon=True)
t.start()
print("Simple HTTP server running on 127.0.0.1:8888")

edge_bin = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
temp_dir = Path(tempfile.mkdtemp(prefix="test_simple_http_"))
out_file = temp_dir / "simple.png"
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
    f"http://127.0.0.1:{PORT}/",
]

t0 = time.time()
proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
captured = False
for i in range(25):
    time.sleep(1.0)
    if out_file.exists() and out_file.stat().st_size > 1000:
        captured = True
        break
    print(f"[{time.time()-t0:.1f}s] waiting for simple http...")

elapsed = time.time() - t0
size = out_file.stat().st_size if out_file.exists() else 0
print(f"Simple HTTP Server Result: captured={captured}, size={size:,} bytes, elapsed={elapsed:.2f}s")

try:
    proc.terminate()
    proc.kill()
except Exception:
    pass
subprocess.run(f"taskkill /F /T /PID {proc.pid}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
httpd.shutdown()
shutil.rmtree(temp_dir, ignore_errors=True)
