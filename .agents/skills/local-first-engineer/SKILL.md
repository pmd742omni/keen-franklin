---
name: local-first-engineer
description: Mastery of 2026 local-first web engineering: in-browser SQLite (wa-sqlite + OPFS), Yjs/Automerge CRDTs, ElectricSQL Postgres sync, and offline mutation queues.
---

# Local-First Engineering Mastery

This skill equips agents and developers with deep architectural patterns, implementation invariants, and best practices for engineering **Local-First Web Applications** in 2026.

---

## 1. When to Use This Skill

Activate this skill when:
- Designing or implementing applications requiring **0ms perceived write latency** and instantaneous local UI updates.
- Implementing offline-first capabilities where the web application must remain 100% functional without internet access.
- Embedding in-browser SQLite with WebAssembly and the Origin Private File System (`OPFS`).
- Implementing multi-user collaborative editing using Conflict-Free Replicated Data Types (`Yjs`, `Automerge`).
- Synchronizing PostgreSQL 17 data with client SQLite replicas via `ElectricSQL` or `PowerSync`.
- Designing idempotent client mutation queues and monotonic conflict resolution strategies.

---

## 2. Core Architectural Pillars

### Pillar 1: In-Browser Storage with OPFS SyncAccessHandle
Never use raw IndexedDB for relational queries. Always deploy SQLite WASM (`wa-sqlite` or `@sqlite.org/sqlite-wasm`) with the Origin Private File System (`OPFS`) SyncAccessHandle pool in a dedicated Web Worker:
- **Write-Ahead Logging (WAL):** Execute `PRAGMA journal_mode = WAL;` and `PRAGMA synchronous = NORMAL;`.
- **Worker Isolation:** Run all SQL execution off the main thread to ensure 60fps / 120fps UI render loop stability.
- **Transactions:** Wrap multi-row operations inside explicit transactions to minimize filesystem sync overhead.

### Pillar 2: Conflict-Free Replicated Data Types (CRDTs)
For collaborative state (e.g. rich text, canvases, kanbans, tree hierarchies):
- Use **Yjs** or **Automerge** to represent shared data structures.
- Transmit binary delta updates over WebSockets (`y-websocket`) or WebRTC (`y-webrtc`).
- Store document history locally in IndexedDB/SQLite with `y-indexeddb` for instant offline boot.

### Pillar 3: Central Postgres Sync via ElectricSQL
Connect central PostgreSQL 17 clusters with client SQLite replicas using Postgres Logical Replication (`pgoutput`):
- Expose **Shapes** (`useShape` hook) that stream partial table queries filtered by tenant or project ID.
- Avoid full-database synchronization; sync only the working set relevant to the active user context.
- Keep business validation rules enforced at the PostgreSQL level via Row Level Security (`RLS`).

### Pillar 4: Offline Mutation Queue & Conflict Resolution
For structured business mutations outside CRDT documents:
- Write optimistically to the local SQLite tables and enqueue a mutation record in a local `outbox` table.
- When network connectivity returns, flush the outbox sequentially over HTTP/2.
- On the server, apply changes idempotently using monotonically increasing version counters (`Last-Write-Wins with version guard`).

---

## 3. Deep Technical References

For concrete code samples and deep configuration details, refer to:
- [CRDTs & Yjs Implementation Guide](references/crdts_and_yjs.md)
- [In-Browser SQLite & OPFS Guide](references/in_browser_sqlite.md)
- [ElectricSQL & Postgres Sync Guide](references/electric_sql_sync.md)
