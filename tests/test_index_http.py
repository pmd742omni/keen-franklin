import http.server
import shutil
import socketserver
import subprocess
import tempfile
import threading
import time
from pathlib import Path

index_html_path = Path("agent_city/static/index.html").resolve()
html_content = index_html_path.read_bytes()

class FileHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(html_content)))
        self.end_headers()
        self.wfile.write(html_content)
    def log_message(self, format, *args):
        pass

PORT = 8889
httpd = socketserver.TCPServer(("127.0.0.1", PORT), FileHandler)
t = threading.Thread(target=httpd.serve_forever, daemon=True)
t.start()
print("Serving index.html on 127.0.0.1:8889")

edge_bin = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
temp_dir = Path(tempfile.mkdtemp(prefix="test_index_http_"))
out_file = temp_dir / "index_shot.png"
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
    print(f"[{time.time()-t0:.1f}s] waiting for index.html on 8889...")

elapsed = time.time() - t0
size = out_file.stat().st_size if out_file.exists() else 0
print(f"index.html on 8889 Result: captured={captured}, size={size:,} bytes, elapsed={elapsed:.2f}s")

try:
    proc.terminate()
    proc.kill()
except Exception:
    pass
subprocess.run(f"taskkill /F /T /PID {proc.pid}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
httpd.shutdown()
shutil.rmtree(temp_dir, ignore_errors=True)
