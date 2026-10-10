import psutil

print("=== CHECKING PYTHON PROCESSES ===")
for p in psutil.process_iter(['pid', 'name', 'cmdline']):
    try:
        cmd = ' '.join(p.info['cmdline'] or [])
        if 'python' in p.info['name'].lower() and any(k in cmd.lower() for k in ['cron', 'server', 'heartbeat', 'uvicorn', 'agent_city']):
            print(f"PID {p.info['pid']}: {cmd}")
    except Exception as e:
        pass
