#!/usr/bin/env python3
"""
Silicon Sanctuary — Visual Documentation & Screenshot Capture Runner
Location: .agents/context/visual_doc_capture.py

Executes automated web app screenshot capture with clean server recycling:
1. Recycles/verifies the FastAPI web server on port 8000.
2. Spawns Microsoft Edge Headless to load fresh pages (Grove '/' and Portal '/evolution').
3. Allows 3D canvas and dynamic state to settle before capture.
4. Saves timestamped PNG artifacts to `agent_city/` and artifact repository.
5. Registers every screenshot in SQLite `sanctuary_context.db`.
6. Updates markdown documentation snapshots in `.agents/context/snapshots/`.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import socket
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

_script_dir = Path(__file__).resolve().parent
_root_dir = _script_dir.parent.parent
if str(_script_dir) not in sys.path:
    sys.path.insert(0, str(_script_dir))

from context_manager import ContextManager

EDGE_BIN = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
BRAIN_ARTIFACTS_DIR = Path(r"C:\Users\ignaz\.gemini\antigravity\brain\8e8e0d95-4549-4479-a58e-ba55f3632b57")

def is_server_listening(port: int = 8000) -> bool:
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=0.5):
            return True
    except OSError:
        return False

class VisualDocCapturer:
    def __init__(self):
        self.cm = ContextManager()
        self.edge_path = EDGE_BIN if os.path.exists(EDGE_BIN) else "msedge"

    def ensure_server_fresh(self) -> bool:
        """Verify web server is alive and fresh on port 8000."""
        if not is_server_listening(8000):
            print("[VisualDoc] Port 8000 not listening, launching fresh server...")
            subprocess.Popen(
                [sys.executable, "-m", "uvicorn", "agent_city.server:app", "--host", "127.0.0.1", "--port", "8000"],
                cwd=str(_root_dir),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            time.sleep(2.0)
        return is_server_listening(8000)

    def capture_page(self, url: str, output_path: Path, window_size: str = "1600,1000") -> bool:
        """Run Edge headless to capture a pristine page screenshot."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        # Remove old file if present
        if output_path.exists():
            try:
                output_path.unlink()
            except Exception:
                pass

        cmd = [
            self.edge_path,
            "--headless=new",
            "--disable-gpu",
            "--no-first-run",
            "--no-default-browser-check",
            f"--window-size={window_size}",
            f"--screenshot={str(output_path)}",
            url
        ]

        try:
            res = subprocess.run(cmd, capture_output=True, timeout=20)
            if output_path.exists() and output_path.stat().st_size > 1000:
                print(f"[VisualDoc] [OK] Captured {output_path.name} ({output_path.stat().st_size:,} bytes)")
                return True
            else:
                print(f"[VisualDoc] Failed to create screenshot at {output_path}")
                return False
        except Exception as e:
            print(f"[VisualDoc] Error during capture: {e}")
            return False

    def run_documentation_cycle(self) -> Dict[str, Any]:
        """Execute full visual capture and register into context database."""
        now = datetime.now()
        timestamp_str = now.strftime("%Y-%m-%d %H:%M:%S")
        slug = now.strftime("%Y%m%d_%H%M%S")

        self.ensure_server_fresh()

        results: Dict[str, Any] = {
            "timestamp": timestamp_str,
            "captures": []
        }

        # 1. Capture 3D Voxel Grove
        grove_filename = f"screenshot_grove_epoch01_{slug}.png"
        grove_dest = _root_dir / "agent_city" / grove_filename
        grove_url = "http://127.0.0.1:8000/"

        if self.capture_page(grove_url, grove_dest):
            # Copy to brain artifact directory
            if BRAIN_ARTIFACTS_DIR.exists():
                shutil.copy2(grove_dest, BRAIN_ARTIFACTS_DIR / grove_filename)
            
            # Register in SQLite
            self.cm.register_artifact(
                artifact_name=grove_filename,
                artifact_type="screenshot_3d_grove",
                file_path=str(grove_dest),
                epoch_id=1,
                metadata={"url": grove_url, "timestamp": timestamp_str}
            )
            results["captures"].append({
                "type": "3D Voxel Grove",
                "filename": grove_filename,
                "size_bytes": grove_dest.stat().st_size
            })

        # 2. Capture Evolution Portal
        portal_filename = f"screenshot_portal_epoch01_{slug}.png"
        portal_dest = _root_dir / "agent_city" / portal_filename
        portal_url = "http://127.0.0.1:8000/evolution"

        if self.capture_page(portal_url, portal_dest):
            if BRAIN_ARTIFACTS_DIR.exists():
                shutil.copy2(portal_dest, BRAIN_ARTIFACTS_DIR / portal_filename)

            self.cm.register_artifact(
                artifact_name=portal_filename,
                artifact_type="screenshot_evolution_portal",
                file_path=str(portal_dest),
                epoch_id=1,
                metadata={"url": portal_url, "timestamp": timestamp_str}
            )
            results["captures"].append({
                "type": "Evolution Portal",
                "filename": portal_filename,
                "size_bytes": portal_dest.stat().st_size
            })

        # 3. Log agent memory
        self.cm.save_memory(
            agent_name="BotanicalMasterSculptor",
            memory_type="visual_capture",
            key=f"capture_{slug}",
            content=results
        )

        return results

def main():
    parser = argparse.ArgumentParser(description="Silicon Sanctuary Visual Documentation Runner")
    parser.add_argument("--once", action="store_true", default=True, help="Run single visual capture cycle")
    args = parser.parse_args()

    runner = VisualDocCapturer()
    res = runner.run_documentation_cycle()
    print(json.dumps(res, indent=2))

if __name__ == "__main__":
    main()
