# 🧠 Silicon Sanctuary Context Management Subsystem
*Persistent Multi-Agent Memory, Epoch State Engine & Rate-Limit Sentinel*

---

## 🏛️ Architecture Overview

The Context Management Subsystem provides a zero-external-dependency, relational SQLite backbone residing within `.agents/context/` to ensure continuity, state recovery, memory sharing, and token headroom tracking across the **336-Hour Autonomous Evolution Horizon**.

```
.agents/context/
├── sanctuary_context.db       # Relational SQLite context database
├── context_manager.py         # Programmatic Python API for epochs, benchmarks, memories
├── rate_limit_sentinel.py     # High-frequency liveness & rate-limit auditor
├── SCHEMA.md                  # Comprehensive relational database schema
└── README.md                  # System manual and operational procedures
```

---

## 💾 Core Components

### 1. `sanctuary_context.db`
- **`epochs`**: Tracks 28 evolution epochs spanning the 336-hour horizon.
- **`benchmarks`**: Logs empirical metrics (RAM reclaimed, latency ms, CPU load, FPS).
- **`rate_limits`**: Records token usage, context window headroom percentage, and liveness states.
- **`agent_memories`**: Stores cross-agent reflections, insights, and decision logs.
- **`artifacts`**: Indexes screenshots, PDFs, binaries (`silicon_kernel.dll`), and reports.

### 2. `context_manager.py`
Provides high-level programmatic methods:
- `record_epoch(epoch_id, title, phase, status, deliverables, summary)`
- `log_benchmark(metric_name, value, unit, epoch_id, notes)`
- `log_rate_limit(tokens_used, headroom_pct, step_index, state, notes)`
- `save_memory(agent_name, memory_type, key, content)`
- `register_artifact(artifact_name, artifact_type, file_path, epoch_id, metadata)`
- `get_summary()`

### 3. `rate_limit_sentinel.py`
- Operates on minute-based and second-based intervals (`--tick` or `--watch`).
- Evaluates daemon health on port 8000.
- Audits rate limits and awakens agent cohort with liveness heartbeats.

---

## 🔄 Integration with Evolution API
The FastAPI server (`agent_city/server.py`) queries `sanctuary_context.db` via `/api/context/summary` and `/api/context/benchmarks` to stream live context metrics directly to the web dashboard.
