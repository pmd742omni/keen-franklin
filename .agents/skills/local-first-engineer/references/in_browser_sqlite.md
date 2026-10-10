# In-Browser SQLite & OPFS Guide

> Architecture and operational patterns for running SQLite WebAssembly with the Origin Private File System (OPFS) in Web Workers.

---

## 1. Web Worker Architecture

Running SQLite on the main JavaScript thread blocks layout calculation and triggers frame drops. SQLite WASM must run inside a dedicated Web Worker communicating via `postMessage`.

```
[Main Thread / React UI] 
        │
   postMessage({ type: 'QUERY', sql: '...' })
        │
        ▼
[Web Worker: sqlite.worker.ts]
        │
    SQLite WASM Kernel (C compiled to WASM)
        │
        ▼
[OPFS SyncAccessHandle] ──> Fast NVMe Disk Read/Write (Zero IPC overhead)
```

---

## 2. Worker Implementation (`sqlite.worker.ts`)

```typescript
import { sqlite3Worker1Promiser } from '@sqlite.org/sqlite-wasm';

let promiser: any;

self.onmessage = async (e: MessageEvent) => {
  const { id, type, payload } = e.data;

  try {
    if (type === 'INIT') {
      promiser = await new Promise((resolve) => {
        const p = sqlite3Worker1Promiser({
          onready: () => resolve(p),
        });
      });

      await promiser('open', {
        filename: 'workspace.sqlite3',
        vfs: 'opfs',
      });

      // Crucial SQLite performance pragmas for OPFS
      await promiser('exec', {
        sql: `
          PRAGMA journal_mode = WAL;
          PRAGMA synchronous = NORMAL;
          PRAGMA cache_size = -64000; -- 64MB memory cache
          PRAGMA temp_store = MEMORY;
        `,
      });

      self.postMessage({ id, success: true });
    } else if (type === 'EXEC') {
      const response = await promiser('exec', {
        sql: payload.sql,
        bind: payload.bind,
        returnValue: 'resultRows',
      });

      self.postMessage({ id, success: true, data: response.result.resultRows });
    }
  } catch (err: any) {
    self.postMessage({ id, success: false, error: err.message });
  }
};
```

---

## 3. High-Performance Batch Mutations

```typescript
// Always wrap bulk operations in a transaction
await executeInWorker(`
  BEGIN TRANSACTION;
  INSERT INTO items (id, name, value) VALUES ('1', 'Item A', 100);
  INSERT INTO items (id, name, value) VALUES ('2', 'Item B', 200);
  COMMIT;
`);
```
