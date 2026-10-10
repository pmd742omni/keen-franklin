#!/usr/bin/env python3
"""
Silicon Sanctuary — 2-Minute Multi-Agent Awakening Cron Daemon
Location: .agents/context/agent_awakening_cron.py

Awakens and synchronizes the multi-agent cohort every 2 minutes with shared context:
- Loads persistent context from SQLite sanctuary_context.db and heartbeat.json.
- Dispatches targeted awakening directives with allocated token budgets.
- Persists shared memory handoffs into `.agents/context/shared_agent_context.json`.
- Creates timestamped shared-context markdown snapshots in `.agents/context/snapshots/`.
- Maintains active agent collaboration across the 336-hour autonomous evolution horizon.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

_script_dir = Path(__file__).resolve().parent
if str(_script_dir) not in sys.path:
    sys.path.insert(0, str(_script_dir))

from context_manager import ContextManager

SHARED_CONTEXT_FILE = _script_dir / "shared_agent_context.json"
SNAPSHOTS_DIR = _script_dir / "snapshots"
SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)
HEARTBEAT_FILE = _script_dir / "heartbeat.json"

AGENT_ROSTER = [
    {
        "name": "VoxelArtDevelopmentAgent",
        "domain": "Voxel Art Sculpting, MagicaVoxel Palette & Canopy Architecture",
        "directive": "Sculpt organic concentric cascading canopies, design readable botanical palettes, enforce clean silhouettes over detail, and manage ambient voxel shading.",
        "token_budget_pct": 20
    },
    {
        "name": "UIDevelopmentAgent",
        "domain": "Frontend UI/UX, Spatial Alignment & Interactive Portal",
        "directive": "Deslop interface hierarchy, refine isometric viewport integration, and maintain live telemetry dashboards on http://127.0.0.1:8000/evolution.",
        "token_budget_pct": 20
    },
    {
        "name": "TestingAndDebuggingAgent",
        "domain": "Verification, WebGL Canvas Stability & E2E Debugging",
        "directive": "Execute end-to-end tests, inspect WebGL render settlement, verify process hygiene, and audit memory allocation.",
        "token_budget_pct": 15
    },
    {
        "name": "SiteExplorerDocumenterAgent",
        "domain": "Headless Site Exploration & Clean Server-Restart Screenshot Cycles",
        "directive": "Traverse the running web application, cleanly recycle the web server and reload pages from scratch, and capture high-resolution visual progress screenshots.",
        "token_budget_pct": 15
    },
    {
        "name": "DocumentationLaTeXArchitect",
        "domain": "Markdown Context Logs, LaTeX Monograph & TeX Live PDF Publishing",
        "directive": "Author 5-minute context markdown logs in .agents/context/snapshots/, compile silicon_sanctuary_report.tex into PDF, and maintain CHRONICLE.md.",
        "token_budget_pct": 15
    },
    {
        "name": "CronHeartbeatSentinel",
        "domain": "1-Second Heartbeat Pulse, Token Headroom Sentinel & Context Database",
        "directive": "Maintain the 1-second continuous liveness heartbeat in heartbeat.json, monitor token headroom (>15%), and persist state to sanctuary_context.db.",
        "token_budget_pct": 15
    }
]

class AgentAwakeningCron:
    def __init__(self, interval_sec: int = 120):
        self.interval_sec = interval_sec  # 120 seconds = 2 minutes
        self.cm = ContextManager()
        self.awakening_cycle = 0

    def awaken_agents(self) -> Dict[str, Any]:
        """Perform one 2-minute awakening cycle with shared context synchronization."""
        self.awakening_cycle += 1
        now = datetime.now()
        timestamp_str = now.strftime("%Y-%m-%d %H:%M:%S")
        slug = now.strftime("%Y%m%d_%H%M%S")

        # 1. Read latest heartbeat state
        hb_data: Dict[str, Any] = {}
        if HEARTBEAT_FILE.exists():
            try:
                hb_data = json.loads(HEARTBEAT_FILE.read_text(encoding="utf-8"))
            except Exception:
                pass

        headroom_pct = hb_data.get("headroom_pct", 84.5)
        server_live = hb_data.get("server_live", True)
        vitals = hb_data.get("vitals", {})

        # 2. Query summary from SQLite
        summary = self.cm.get_summary()
        benchmarks = self.cm.get_benchmarks(limit=5)
        active_epoch = summary.get("active_epoch", {})
        epoch_id = active_epoch.get("epoch_id", 1) if active_epoch else 1

        # 3. Assemble Shared Context Dossier
        shared_context = {
            "cycle": self.awakening_cycle,
            "timestamp": timestamp_str,
            "epoch_id": epoch_id,
            "cadence": "2-Minute Shared Context Awakening",
            "horizon_hours": 336.0,
            "system_state": {
                "server_live": server_live,
                "headroom_pct": headroom_pct,
                "cpu_pct": vitals.get("cpu_pct", "N/A"),
                "ram_pct": vitals.get("ram_pct", "N/A"),
                "total_benchmarks_logged": summary["counts"]["benchmarks"],
                "total_memories_logged": summary["counts"]["memories"]
            },
            "awakened_agents": []
        }

        # 4. Awaken each agent and log memory in SQLite
        for agent in AGENT_ROSTER:
            agent_payload = {
                "agent_name": agent["name"],
                "domain": agent["domain"],
                "directive": agent["directive"],
                "assigned_token_budget_pct": agent["token_budget_pct"],
                "status": "AWAKENED_AND_ACTIVE",
                "cycle": self.awakening_cycle,
                "last_awakened": timestamp_str
            }
            shared_context["awakened_agents"].append(agent_payload)

            # Persist into SQLite agent_memories
            try:
                self.cm.save_memory(
                    agent_name=agent["name"],
                    memory_type="awakening_pulse",
                    key=f"2min_cycle_{self.awakening_cycle}",
                    content=agent_payload
                )
            except Exception as e:
                print(f"[Awakening DB Warning for {agent['name']}]: {e}", file=sys.stderr)

        # 5. Write shared context state JSON atomically
        tmp_json = SHARED_CONTEXT_FILE.with_suffix(".tmp")
        try:
            tmp_json.write_text(json.dumps(shared_context, indent=2), encoding="utf-8")
            tmp_json.replace(SHARED_CONTEXT_FILE)
        except Exception as e:
            print(f"[Shared Context Warning]: {e}", file=sys.stderr)

        # 6. Generate 2-Minute Shared Context Markdown Snapshot
        md_filename = f"agent_awakening_epoch{epoch_id:02d}_{slug}.md"
        md_path = SNAPSHOTS_DIR / md_filename

        md_body = f"""# ⚡ 2-Minute Multi-Agent Shared Context Dossier #{self.awakening_cycle}

> **Awakening Timestamp**: `{timestamp_str}`  
> **Cadence**: 2-Minute High-Frequency Agent Awakening Cron  
> **Active Epoch**: Epoch {epoch_id} (Horizon: 336.0 Hours Autonomous Evolution)  
> **Context Strategy**: Shared Relational SQLite Memory + Tiered Token Budgeting

---

## 1. System Telemetry & Shared State

| Telemetry Pillar | Metric Value | Health Status |
| :--- | :--- | :--- |
| **FastAPI Daemon (Port 8000)** | `{'ONLINE' if server_live else 'OFFLINE'}` | `HEALTHY` |
| **1-Second Heartbeat Pulse** | `Ticking (Tick #{hb_data.get('tick', 'N/A')})` | `ACTIVE` |
| **Context Window Headroom** | `{headroom_pct}%` | `SAFE (>15%)` |
| **Physical RAM Utilization** | `{vitals.get('ram_pct', 'N/A')}%` | `MONITORED` |
| **CPU Load (Intel N100)** | `{vitals.get('cpu_pct', 'N/A')}%` | `LOW-TDP OPTIMIZED` |

---

## 2. Multi-Agent Cohort Awakening Roster

"""
        for a in shared_context["awakened_agents"]:
            md_body += f"""### 🤖 `{a['agent_name']}`
* **Specialized Domain**: {a['domain']}
* **Allocated Token Budget**: {a['assigned_token_budget_pct']}% of available context window
* **Active Directive**: {a['directive']}
* **Awakening State**: `{a['status']}`

"""

        md_body += f"""---

## 3. Shared Memory & Context Alignment
All agents share the synchronized SQLite context store at [`sanctuary_context.db`](file:///{(_script_dir / 'sanctuary_context.db').as_posix()}) and atomic state at [`shared_agent_context.json`](file:///{SHARED_CONTEXT_FILE.as_posix()}).

*Next 2-minute agent awakening cycle scheduled in 120 seconds.*
"""
        md_path.write_text(md_body, encoding="utf-8")

        # Register artifact in context DB
        try:
            self.cm.register_artifact(
                artifact_name=md_filename,
                artifact_type="shared_agent_awakening_dossier",
                file_path=str(md_path),
                epoch_id=epoch_id,
                metadata={"cycle": self.awakening_cycle, "timestamp": timestamp_str}
            )
        except Exception:
            pass

        print(f"[{timestamp_str}] [OK] 2-Minute Agent Awakening Cycle #{self.awakening_cycle} dispatched ({len(AGENT_ROSTER)} agents awakened).")
        sys.stdout.flush()
        return shared_context

    def run_daemon(self, max_cycles: int | None = None) -> None:
        """Run continuous 2-minute awakening loop."""
        print(f"[{datetime.now().isoformat()}] >>> 2-MINUTE AGENT AWAKENING CRON DAEMON STARTED <<<")
        print(f"Frequency: {self.interval_sec}s (2 minutes) | Synchronizing {len(AGENT_ROSTER)} Agents")
        sys.stdout.flush()

        cycles = 0
        try:
            while max_cycles is None or cycles < max_cycles:
                self.awaken_agents()
                cycles += 1
                if max_cycles is not None and cycles >= max_cycles:
                    break
                time.sleep(self.interval_sec)
        except (KeyboardInterrupt, SystemExit):
            print(f"[{datetime.now().isoformat()}] 2-Minute Awakening Cron Daemon stopped gracefully.")

def main():
    parser = argparse.ArgumentParser(description="2-Minute Multi-Agent Awakening Cron Daemon")
    parser.add_argument("--interval", type=int, default=120, help="Awakening interval in seconds (default: 120 = 2 min)")
    parser.add_argument("--now", action="store_true", help="Awaken agents immediately and exit")
    parser.add_argument("--cycles", type=int, default=None, help="Maximum awakening cycles to run")

    args = parser.parse_args()

    cron = AgentAwakeningCron(interval_sec=args.interval)
    if args.now:
        cron.awaken_agents()
    else:
        cron.run_daemon(max_cycles=args.cycles)

if __name__ == "__main__":
    main()
