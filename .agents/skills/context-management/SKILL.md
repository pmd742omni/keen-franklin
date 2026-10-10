---
name: context-management
description: Operates and orchestrates the Silicon Sanctuary relational SQLite context management engine, memory persistence, epoch lifecycles, and high-frequency rate-limit sentinels.
risk: safe
source: silicon-sanctuary
date_added: '2026-10-10'
---

## Use this skill when

- Logging benchmarks, epoch completions, and evolution state snapshots.
- Storing and recalling multi-agent persistent memories across sessions.
- Auditing rate limits, token budgets, and liveness states using `rate_limit_sentinel.py`.
- Registering newly generated screenshots, compiled binaries, and LaTeX PDF reports.

## System Architecture

The context management subsystem lives in `.agents/context/`:
- **Database**: `sanctuary_context.db` (SQLite relational store)
- **API**: `context_manager.py` (Python ContextManager class)
- **Sentinel**: `rate_limit_sentinel.py` (Liveness & Rate-Limit monitor)
- **Documentation**: `README.md` and `SCHEMA.md`

## Standard Operational Procedures

1. **At Every Epoch Transition**:
   ```bash
   python .agents/context/context_manager.py
   ```
   Invoke `cm.record_epoch(epoch_id, title, phase, status, deliverables, summary)` to seal completed milestones and launch active epochs.

2. **At Every Optimization / Compaction**:
   Record reclaimed megabytes, process counts, and duration:
   ```python
   from context_manager import ContextManager
   cm = ContextManager()
   cm.log_benchmark("RAM Reclaimed (C-Kernel)", 3859.75, "MB", notes="Win32 psapi compaction")
   ```

3. **High-Frequency Liveness Sentinel Check**:
   ```bash
   python .agents/context/rate_limit_sentinel.py --tick
   ```
   Logs liveness heartbeats, validates server status on port 8000, and verifies token headroom.
