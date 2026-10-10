import sys
import sqlite3
import asyncio
import importlib

print("Python executable:", sys.executable)
print("Python version:", sys.version)
print("sqlite3 version:", sqlite3.sqlite_version)

packages = [
    "fastapi",
    "uvicorn",
    "starlette",
    "websockets",
    "pydantic",
    "pytest",
    "pytest_asyncio",
    "httpx",
    "sse_starlette",
    "anyio"
]

for pkg in packages:
    try:
        mod = importlib.import_module(pkg)
        ver = getattr(mod, "__version__", "available")
        print(f"  {pkg}: {ver}")
    except ImportError as e:
        print(f"  {pkg}: NOT FOUND ({e})")
