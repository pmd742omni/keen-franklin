# Local-First Web Architectures, CRDTs & Data Synchronization

> **2026 Paradigm Shift:** Local-first architecture prioritizes client-side storage as the primary source of truth, enabling instantaneous 0ms perceived latency, offline-first reliability, and background bi-directional synchronization with central PostgreSQL clusters.

---

## 1. Why Local-First Architecture?

Traditional client-server models force every interaction to make a round-trip network request (50–300ms). Under high latency or intermittent mobile connectivity, applications freeze, drop user edits, or show loading spinners.

```
Traditional Client-Server:
[UI Action] ---> (Network RTT: 120ms) ---> [API Server] ---> [PostgreSQL] ---> (Network RTT) ---> [UI Update]

Local-First:
[UI Action] ---> [Client SQLite / IndexedDB] ---> [UI Update: 0ms]
                      │
                      ▼ (Background Async Sync)
              [Sync Engine (ElectricSQL / PowerSync / WebSockets)]
                      │
                      ▼
              [Central PostgreSQL 17]
```

### Core Tenets of Local-First:
1. **Local Availability:** All user reads and writes hit local disk (OPFS - Origin Private File System or IndexedDB) instantly.
2. **Offline Resilience:** The application retains 100% functionality without network connectivity.
3. **Multi-Device Synchronization:** Changes propagate seamlessly across devices via background sync engines.
4. **Deterministic Conflict Resolution:** State is reconciled without manual user intervention using Conflict-Free Replicated Data Types (CRDTs) or Last-Write-Wins (LWW) with logical clocks (Lamport/Vector clocks).
5. **Data Ownership:** User data lives on client hardware in standard open formats (SQLite/JSON).

---

## 2. Open-Source Local-First Technology Stack (2026)

| Layer | Open-Source Technology | Role & Advantages |
| :--- | :--- | :--- |
| **In-Browser Storage** | **wa-sqlite + OPFS** | WebAssembly SQLite running in Web Workers with Origin Private File System; 10x faster than raw IndexedDB. |
| **CRDT Engines** | **Yjs** / **Automerge** | Conflict-free state reconciliation for collaborative documents, rich-text, and hierarchical JSON state. |
| **Postgres-to-Client Sync** | **ElectricSQL** | Syncs PostgreSQL subsets to client SQLite via Postgres Logical Replication (`pgoutput`). |
| **Mobile & Web Sync** | **PowerSync** | Real-time bi-directional sync engine connecting client SQLite (Flutter, React Native, Web) to Postgres/Node/Go. |
| **Reactive Client ORM** | **RxDB** / **Drizzle WASM** | Reactive query subscriptions (`useQuery`) that re-render React components automatically upon local SQLite change. |

---

## 3. In-Browser SQLite with OPFS (Origin Private File System)

The modern standard for browser-side local-first storage is SQLite compiled to WebAssembly with the `wa-sqlite` or official SQLite WASM VFS (`sqlite3.wasm` with `opfs-sahpool` - SyncAccessHandle pool).

### Client Web Worker SQLite Setup (`sqlite.worker.ts`):
```typescript
import { sqlite3Worker1Promiser } from '@sqlite.org/sqlite-wasm';

export interface DatabaseWorkerAPI {
  exec: (sql: string, params?: any[]) => Promise<any[]>;
  init: () => Promise<void>;
}

let promiser: any;

export async function initDatabase(): Promise<void> {
  promiser = await new Promise((resolve) => {
    const p = sqlite3Worker1Promiser({
      onready: () => resolve(p)
    });
  });

  // Open database backed by high-performance OPFS SyncAccessHandle
  await promiser('open', {
    filename: 'app_data.sqlite3',
    vfs: 'opfs'
  });

  // Initialize schema with WAL mode
  await promiser('exec', {
    sql: `
      PRAGMA journal_mode = WAL;
      PRAGMA synchronous = NORMAL;
      CREATE TABLE IF NOT EXISTS notes (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        content TEXT,
        updated_at INTEGER NOT NULL,
        synced INTEGER DEFAULT 0
      );
      CREATE INDEX IF NOT EXISTS idx_notes_updated ON notes(updated_at DESC);
    `
  });
}

export async function queryNotes(): Promise<any[]> {
  const result = await promiser('exec', {
    sql: 'SELECT * FROM notes ORDER BY updated_at DESC;',
    returnValue: 'resultRows'
  });
  return result.result.resultRows;
}
```

---

## 4. Conflict-Free Replicated Data Types (CRDTs) with Yjs

For multi-user collaboration (e.g. documents, kanban boards, shared carts), Yjs provides state-vector delta compression and binary network encodings.

### React Integration with Yjs and WebSockets:
```tsx
import React, { useEffect, useState } from 'react';
import * as Y from 'yjs';
import { WebsocketProvider } from 'y-websocket';

// Shared document instance
const doc = new Y.Doc();
const provider = new WebsocketProvider(
  process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:1234',
  'room-workspace-1',
  doc
);

// Shared Y.Array of items
const yItems = doc.getArray<string>('todo-items');

export function CollaborativeList() {
  const [items, setItems] = useState<string[]>([]);
  const [inputVal, setInputVal] = useState('');

  useEffect(() => {
    const observer = () => {
      setItems(yItems.toArray());
    };

    yItems.observe(observer);
    setItems(yItems.toArray());

    return () => {
      yItems.unobserve(observer);
    };
  }, []);

  const addItem = () => {
    if (!inputVal.trim()) return;
    // Mutating the Yjs structure instantly updates local state
    // and broadcasts a binary delta to all connected peers
    doc.transact(() => {
      yItems.push([inputVal]);
    });
    setInputVal('');
  };

  return (
    <div className="p-4 bg-slate-900 text-white rounded-lg">
      <h3 className="text-lg font-bold mb-3">Live Collaborative List (Yjs CRDT)</h3>
      <div className="flex gap-2 mb-4">
        <input
          type="text"
          value={inputVal}
          onChange={(e) => setInputVal(e.target.value)}
          className="px-3 py-2 bg-slate-800 rounded border border-slate-700 flex-1"
          placeholder="New collaborative task..."
        />
        <button
          onClick={addItem}
          className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 rounded font-semibold"
        >
          Add
        </button>
      </div>

      <ul className="space-y-1">
        {items.map((item, idx) => (
          <li key={idx} className="p-2 bg-slate-800/60 rounded border border-slate-800">
            {item}
          </li>
        ))}
      </ul>
    </div>
  );
}
```

---

## 5. PostgreSQL-to-Client Sync via ElectricSQL

ElectricSQL bridges central PostgreSQL 17 databases with local SQLite databases in the browser, Electron, or mobile apps using Postgres Logical Replication (`WAL`).

### Architecture Flow:
1. **Central Database:** PostgreSQL 17 with `wal_level = logical`.
2. **Electric Sync Service:** Go-based daemon subscribing to Postgres logical replication stream (`pgoutput`).
3. **Client:** Web app using `@electric-sql/pglite` or client SQLite.

### Defining Sync Rules in PostgreSQL:
```sql
-- Enable replication for target tables
ALTER TABLE projects REPLICA IDENTITY FULL;
ALTER TABLE tasks REPLICA IDENTITY FULL;

-- Electric publication
CREATE PUBLICATION electric_publication FOR TABLE projects, tasks;
```

### Client React Component Syncing Shapes:
```typescript
import { useShape } from '@electric-sql/react';

interface Task {
  id: string;
  project_id: string;
  title: string;
  completed: boolean;
}

export function ProjectTasksView({ projectId }: { projectId: string }) {
  // useShape streams only the user's active project slice from Postgres
  const { data: tasks, isLoading } = useShape<Task>({
    url: `${process.env.NEXT_PUBLIC_ELECTRIC_URL}/v1/shape`,
    params: {
      table: 'tasks',
      where: `project_id = '${projectId}'`,
    },
  });

  if (isLoading) return <div>Syncing local replica...</div>;

  return (
    <div className="space-y-2">
      {tasks.map((task) => (
        <div key={task.id} className="flex items-center gap-2">
          <input type="checkbox" checked={task.completed} readOnly />
          <span className={task.completed ? 'line-through text-slate-500' : ''}>
            {task.title}
          </span>
        </div>
      ))}
    </div>
  );
}
```

---

## 6. Offline Mutation Queue & Conflict Resolution

When writing while offline without a formal CRDT data structure, use an **Idempotent Mutation Queue** backed by client SQLite:

```
[User Action] ---> [Local SQLite: Apply Optimistically]
               ---> [Local Outbox Table: Enqueue Mutation (UUID, Timestamp, Action, Payload)]
               
[Network Online Event Triggered]
               ---> [Drain Outbox in Sequential Order]
               ---> [POST /api/v1/sync/mutations (HTTP/2 Batch)]
               ---> [Server: Execute within Postgres Transaction]
               ---> [Server Returns Ack or Conflict Resolution Payload]
               ---> [Client Outbox: Purge Acknowledged Entries]
```

### Server-Side Last-Write-Wins (LWW) with Version Columns:
```sql
-- Idempotent Upsert in PostgreSQL with Vector Clock / Monotonic Version
CREATE OR REPLACE FUNCTION apply_client_mutation(
  p_id UUID,
  p_title TEXT,
  p_client_version INT,
  p_client_updated_at TIMESTAMPTZ
) RETURNS VOID AS $$
BEGIN
  INSERT INTO documents (id, title, version, updated_at)
  VALUES (p_id, p_title, p_client_version, p_client_updated_at)
  ON CONFLICT (id) DO UPDATE
  SET 
    title = EXCLUDED.title,
    version = EXCLUDED.version,
    updated_at = EXCLUDED.updated_at
  WHERE EXCLUDED.version > documents.version; -- Reject stale out-of-order writes
END;
$$ LANGUAGE plpgsql;
```

---

## 7. Performance & Latency Matrix

| Metric | Server-Rendered / REST | React SPA + TanStack Query | Local-First (wa-sqlite / Yjs) |
| :--- | :--- | :--- | :--- |
| **First Interaction Latency** | 100–350ms (RTT dependent) | 80–200ms (Optimistic UI fallback) | **< 1ms (Instant disk write)** |
| **Offline Behavior** | Complete Failure | Read-only cache / stale | **Full Read & Write Capability** |
| **Network Bandwidth** | Full HTML or Large JSON payloads | JSON payload per request | **Compact binary delta sync** |
| **Server Load** | Proportional to user actions | Proportional to queries | **Offloaded to client compute** |
| **Failure Mode** | 500 / 504 Gateway Timeout | Stale Error Toast | **Transparent background retry** |
