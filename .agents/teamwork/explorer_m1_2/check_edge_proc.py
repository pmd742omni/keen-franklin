import subprocess
import json

cmd = ["powershell", "-NoProfile", "-Command", "Get-Process msedge -ErrorAction SilentlyContinue | Select-Object Id, ProcessName, MainWindowTitle | ConvertTo-Json"]
out = subprocess.run(cmd, capture_output=True, text=True)
print("Edge processes JSON:")
print(out.stdout)
