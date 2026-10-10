# CRDTs & Yjs Implementation Guide

> Technical reference for state reconciliation, binary delta synchronization, and offline collaborative editing with Yjs.

---

## 1. Yjs Document Lifecycle

A `Y.Doc` instance maintains internal state vectors representing all applied edit operations.

```typescript
import * as Y from 'yjs';
import { WebsocketProvider } from 'y-websocket';
import { IndexeddbPersistence } from 'y-indexeddb';

// 1. Create a root document
const doc = new Y.Doc();

// 2. Offline local persistence (loads immediately from disk)
const persistence = new IndexeddbPersistence('doc-offline-cache', doc);

persistence.on('synced', () => {
  console.log('[Yjs] Local offline document state loaded.');
});

// 3. Network synchronization provider (syncs changes when online)
const wsProvider = new WebsocketProvider(
  process.env.NEXT_PUBLIC_WS_ENDPOINT || 'ws://localhost:1234',
  'room-project-alpha',
  doc
);
```

---

## 2. Shared Types

Yjs provides specialized collaborative data types:
- `Y.Array`: Ordered list of elements (ideal for tasks, cards, rows).
- `Y.Map`: Key-value map (ideal for user settings, record attributes).
- `Y.Text`: Collaborative rich-text string (integrated with ProseMirror, Quill, Monaco).

### Modifying Shared State within Transactions:
```typescript
const sharedList = doc.getArray('tasks');

// Always wrap batched mutations in doc.transact to emit a single binary delta
doc.transact(() => {
  sharedList.push([
    { id: 'task_1', title: 'Implement OPFS Worker', completed: false }
  ]);
});
```

---

## 3. Awareness Protocol (Presence & Cursors)

The awareness protocol handles ephemeral state that should not be persisted (e.g. live cursors, active users, selections):

```typescript
const awareness = wsProvider.awareness;

// Broadcast local user status
awareness.setLocalStateField('user', {
  name: 'Ignazio',
  color: '#4f46e5',
  cursor: { x: 250, y: 120 }
});

// Listen to peer updates
awareness.on('change', () => {
  const states = Array.from(awareness.getStates().values());
  console.log('Active connected peers:', states);
});
```
