# 🗄️ Sanctuary Context Database Schema
*SQLite Relational Model for Autonomous System Persistence*

Database File: `.agents/context/sanctuary_context.db`

---

## 1. Table: `epochs`
Stores chronological milestones across the 336-hour evolution roadmap.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `epoch_id` | INTEGER | PRIMARY KEY | Epoch number (0 to 27) |
| `title` | TEXT | NOT NULL | Human-readable epoch title |
| `phase` | TEXT | NOT NULL | Milestone grouping (Genesis, Refinement, Optimization, etc.) |
| `started_at` | TEXT | NOT NULL | ISO 8601 start timestamp |
| `completed_at` | TEXT | NULL | ISO 8601 completion timestamp |
| `status` | TEXT | NOT NULL | `'pending'`, `'active'`, `'completed'` |
| `deliverables_json` | TEXT | NULL | JSON array of expected and completed deliverables |
| `summary` | TEXT | NULL | Markdown summary of accomplishments |

---

## 2. Table: `benchmarks`
Empirical performance measurements logged by native layers and agents.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Unique benchmark ID |
| `timestamp` | TEXT | NOT NULL | ISO 8601 timestamp of measurement |
| `epoch_id` | INTEGER | NULL | Associated epoch ID |
| `metric_name` | TEXT | NOT NULL | Metric key (e.g. `RAM Reclaimed`, `Compaction Latency`) |
| `value_numeric` | REAL | NOT NULL | Floating-point value |
| `unit` | TEXT | NOT NULL | Unit string (`MB`, `ms`, `%`, `FPS`) |
| `notes` | TEXT | NULL | Qualitative details and hardware context |

---

## 3. Table: `rate_limits`
Liveness, token budget, and context window health records.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Unique log entry ID |
| `timestamp` | TEXT | NOT NULL | ISO 8601 timestamp |
| `tokens_used` | INTEGER | NULL | Estimated tokens consumed |
| `tokens_headroom_pct`| REAL | NULL | Estimated headroom percentage remaining |
| `step_index` | INTEGER | NULL | Trajectory step index |
| `rate_limit_state` | TEXT | NOT NULL | `'nominal'`, `'warning'`, `'throttled'` |
| `notes` | TEXT | NULL | Sentinel observation details |

---

## 4. Table: `agent_memories`
Cross-agent reflection, shared knowledge, and procedural insights.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Memory entry ID |
| `timestamp` | TEXT | NOT NULL | ISO 8601 creation timestamp |
| `agent_name` | TEXT | NOT NULL | Emitting agent (`BotanicalSculptor`, `KernelGovernor`, etc.) |
| `memory_type` | TEXT | NOT NULL | `'reflection'`, `'decision'`, `'heuristic'`, `'liveness_heartbeat'` |
| `key` | TEXT | NOT NULL | Identifier key for lookups |
| `content_json` | TEXT | NOT NULL | Serialized JSON data payload |

---

## 5. Table: `artifacts`
Persistent visual and technical artifact registry.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Artifact record ID |
| `timestamp` | TEXT | NOT NULL | Registration timestamp |
| `epoch_id` | INTEGER | NULL | Originating epoch |
| `artifact_name` | TEXT | NOT NULL | Filename (`screenshot_grove_v7.png`, `silicon_kernel.dll`) |
| `artifact_type` | TEXT | NOT NULL | `'screenshot'`, `'binary'`, `'document'`, `'latex_pdf'` |
| `file_path` | TEXT | NOT NULL | Relative workspace path |
| `file_size_bytes` | INTEGER | NULL | File size on disk |
| `metadata_json` | TEXT | NULL | JSON metadata (resolution, compiler, etc.) |
