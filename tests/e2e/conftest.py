"""
Pytest configuration and shared fixtures for Autonomous Multi-Agent Visual Documentation System.
Location: tests/e2e/conftest.py
"""

from __future__ import annotations

import os
import shutil
import socket
import sqlite3
import struct
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import psutil
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
BASE_URL = os.environ.get("SANCTUARY_TEST_URL", "http://127.0.0.1:8000")
STRICT_MODE = os.environ.get("STRICT_E2E", "0") in ("1", "true", "True")
EDGE_SEARCH_PATHS = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]


def is_port_open(host: str = "127.0.0.1", port: int = 8000, timeout: float = 0.5) -> bool:
    """Check if TCP port is actively accepting connections."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def ensure_server_running(host: str = "127.0.0.1", port: int = 8000) -> bool:
    """Ensure the FastAPI server is running on port 8000, launching in background if needed."""
    if is_port_open(host, port, timeout=0.2):
        return True

    flags = 0
    if sys.platform == "win32":
        DETACHED_PROCESS = 0x00000008
        CREATE_NO_WINDOW = 0x08000000
        flags = DETACHED_PROCESS | CREATE_NO_WINDOW

    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "agent_city.server:app",
        "--host",
        host,
        "--port",
        str(port),
    ]

    try:
        subprocess.Popen(
            cmd,
            cwd=str(PROJECT_ROOT),
            creationflags=flags,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            close_fds=True,
        )
        for _ in range(35):
            time.sleep(0.3)
            if is_port_open(host, port, timeout=0.2):
                return True
    except Exception:
        pass
    return is_port_open(host, port, timeout=0.5)


def get_edge_path() -> Optional[str]:
    """Find Microsoft Edge executable on disk."""
    for p in EDGE_SEARCH_PATHS:
        if os.path.exists(p):
            return p
    which_edge = shutil.which("msedge")
    if which_edge and os.path.exists(which_edge):
        return which_edge
    return None


def run_edge_capture(
    edge_bin: str,
    url: str,
    output_path: Path,
    window_size: str = "1920,1080",
    virtual_time_budget: int = 2000,
    user_data_dir: Optional[Path] = None,
    timeout: float = 35.0,
) -> bool:
    """
    Run Microsoft Edge in headless mode safely on Windows:
    - Avoids stdin/stdout pipe hangs with DEVNULL
    - Ensures isolated user-data-dir
    - Terminate child process trees on timeout
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists():
        try:
            output_path.unlink()
        except Exception:
            pass

    cleanup_temp = False
    if not user_data_dir:
        user_data_dir = Path(tempfile.mkdtemp(prefix="edge_capture_iso_"))
        cleanup_temp = True

    cmd = [
        edge_bin,
        f"--user-data-dir={str(user_data_dir)}",
        "--headless=new",
        "--no-first-run",
        "--no-default-browser-check",
        "--hide-scrollbars",
        f"--virtual-time-budget={virtual_time_budget}",
        f"--window-size={window_size}",
        f"--screenshot={str(output_path)}",
        url,
    ]

    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        proc.wait(timeout=timeout)
        success = output_path.exists() and output_path.stat().st_size > 500
        return success
    except subprocess.TimeoutExpired:
        try:
            parent = psutil.Process(proc.pid)
            for child in parent.children(recursive=True):
                child.kill()
            parent.kill()
        except Exception:
            pass
        return False
    finally:
        if cleanup_temp and user_data_dir.exists():
            try:
                shutil.rmtree(user_data_dir, ignore_errors=True)
            except Exception:
                pass


def parse_png_header(data: bytes) -> Dict[str, Any]:
    """
    Parse standard PNG signature and IHDR chunk.
    Returns dictionary with width, height, bit_depth, color_type.
    """
    PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
    if len(data) < 24:
        return {"valid": False, "error": "Data too short for PNG header"}
    if not data.startswith(PNG_SIGNATURE):
        return {"valid": False, "error": "Invalid PNG magic signature"}
    
    chunk_type = data[12:16]
    if chunk_type != b"IHDR":
        return {"valid": False, "error": f"Expected IHDR chunk, got {chunk_type!r}"}
    
    width, height, bit_depth, color_type = struct.unpack(">IIBB", data[16:26])
    return {
        "valid": True,
        "width": width,
        "height": height,
        "bit_depth": bit_depth,
        "color_type": color_type,
        "file_size": len(data),
    }


def http_request(
    url: str,
    method: str = "GET",
    data: Optional[bytes] = None,
    headers: Optional[Dict[str, str]] = None,
    timeout: float = 5.0,
) -> Tuple[int, bytes, Dict[str, str]]:
    """Execute HTTP request using standard urllib, returning (status_code, body_bytes, headers_dict)."""
    req_headers = headers or {}
    req = urllib.request.Request(url, data=data, headers=req_headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            status_code = response.status
            body = response.read()
            resp_headers = dict(response.headers)
            return status_code, body, resp_headers
    except urllib.error.HTTPError as e:
        body = e.read()
        resp_headers = dict(e.headers)
        return e.code, body, resp_headers
    except urllib.error.URLError as e:
        return 0, str(e.reason).encode("utf-8"), {}
    except Exception as e:
        return 0, str(e).encode("utf-8"), {}


def check_milestone_capability(milestone: str, condition: bool, reason: str):
    """
    Progressive testability helper:
    If condition is false:
      - in strict mode (Milestone M5): assertion fails.
      - in progressive mode: test is skipped with descriptive milestone reference.
    """
    if not condition:
        if STRICT_MODE:
            pytest.fail(f"[{milestone} Strict Failure] {reason}")
        else:
            pytest.skip(f"[{milestone} Pending] {reason}")


def pytest_sessionstart(session):
    """Auto-detect server and boot background daemon if offline."""
    ensure_server_running()


@pytest.fixture(scope="session")
def project_root() -> Path:
    return PROJECT_ROOT


@pytest.fixture(scope="session")
def base_url() -> str:
    ensure_server_running()
    return BASE_URL


@pytest.fixture(scope="session")
def edge_binary() -> str:
    edge_p = get_edge_path()
    if not edge_p:
        pytest.skip("Microsoft Edge executable not found on host system.")
    return edge_p


@pytest.fixture
def temp_capture_dir():
    temp_dir = tempfile.mkdtemp(prefix="test_e2e_capture_")
    yield Path(temp_dir)
    try:
        shutil.rmtree(temp_dir, ignore_errors=True)
    except Exception:
        pass


@pytest.fixture(scope="session")
def db_path() -> Path:
    return PROJECT_ROOT / ".agents" / "context" / "sanctuary_context.db"


@pytest.fixture
def db_conn(db_path: Path):
    if not db_path.exists():
        pytest.skip(f"Database not found at {db_path}")
    conn = sqlite3.connect(str(db_path), timeout=10.0)
    conn.row_factory = sqlite3.Row
    yield conn
    conn.close()


@pytest.fixture
def live_server_available(base_url: str) -> bool:
    return is_port_open("127.0.0.1", 8000)
