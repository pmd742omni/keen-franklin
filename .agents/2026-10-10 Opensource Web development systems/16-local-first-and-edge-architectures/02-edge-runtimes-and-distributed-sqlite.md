# Open-Source Edge Runtimes & Distributed SQLite

> **2026 Production Edge Architecture:** Bringing compute and data to within 10–20ms of end users worldwide using open-source V8 isolates (`workerd`), low-overhead container runtimes, and globally replicated SQLite (`LibSQL` / `LiteFS`).

---

## 1. Architectural Landscape: Origin Servers vs. The Edge

```
Centralized Cloud Architecture:
[User in Tokyo] ─────── (220ms RTT) ───────> [AWS us-east-1 Monolith]

Modern Edge Architecture (2026):
[User in Tokyo] ── (8ms) ──> [Tokyo Edge POP: workerd Isolate]
                                  │
                                  ├─ Read: [Local LibSQL Replica] (1ms)
                                  └─ Write: Forward to [Primary PostgreSQL / LibSQL]
```

### Key Motivations:
1. **Cold Start Elimination:** Traditional container cold starts range from 800ms to 5,000ms. V8 isolate engines (`workerd`) start in **< 5ms**.
2. **Global Micro-Latency:** HTML rendering and edge redirects resolve at the closest point of presence (POP).
3. **Data Locality:** Read-heavy workloads (90%+ of queries) execute against local edge SQLite replicas without transatlantic hops.

---

## 2. Open-Source Edge Runtimes

| Runtime | Engine / Core | Key Strengths | Best Used For |
| :--- | :--- | :--- | :--- |
| **`workerd`** | C++ / V8 Isolates | The exact open-source core powering Cloudflare Workers; zero startup overhead, strict Web Standards (`fetch`, `Request`, `Response`). | Self-hosted edge proxies, micro-gateways, serverless edge workers. |
| **`Deno`** | Rust / V8 | Native TypeScript, Web Standards API, built-in KV store, sandboxed by default. | Edge APIs, SSR middleware, background scheduled workers. |
| **`Bun`** | Zig / JavaScriptCore | Extremely fast startup, integrated package manager, built-in SQLite, ultra-low memory footprint. | High-throughput edge microservices, WebSocket edge aggregators. |

---

## 3. Distributed SQLite: LibSQL & LiteFS

SQLite was traditionally confined to a single process on a single machine. In 2026, open-source distributed SQLite engines enable global replication with ACID guarantees.

### A. LibSQL (by Turso)
- **Open-source fork of SQLite** maintained under open governance.
- **Features:** Server mode (`sqld`), HTTP/WebSocket protocol, built-in vector search (`vector_top_k`), and multi-region replication.
- **Embedded Replicas:** Applications can run LibSQL embedded in-memory or on local NVMe disk while synchronizing with a remote primary instance.

#### Setting Up LibSQL Embedded Replica in Node / Bun:
```typescript
import { createClient } from '@libsql/client';

// Embedded replica: Reads are served from local file in 0.1ms;
// Writes are automatically forwarded to remote primary over TLS.
const db = createClient({
  url: 'file:/var/data/edge-replica.db',
  syncUrl: process.env.LIBSQL_PRIMARY_URL, // e.g., 'libsql://primary.internal:8080'
  authToken: process.env.LIBSQL_AUTH_TOKEN,
  syncInterval: 60, // Automatic sync every 60 seconds
});

// Explicit background synchronization
await db.sync();

// Ultra-fast local edge read
const users = await db.execute({
  sql: 'SELECT id, username, email FROM users WHERE organization_id = ? LIMIT 50;',
  args: ['org_123'],
});

console.log(`Loaded ${users.rows.length} users from edge NVMe cache.`);
```

---

### B. LiteFS (Distributed SQLite via FUSE)
- **Developed by Fly.io (Open Source):** Replicates SQLite databases across a cluster of nodes using a FUSE (Filesystem in Userspace) driver.
- **Zero Application Changes:** Applications interact with standard SQLite files (`/var/data/app.db`) through standard ORMs (Eloquent, Drizzle, SQLAlchemy).
- **Consul / Leases:** LiteFS uses Raft or Consul to elect a single primary node for writes. Read replicas stream transaction pages in near-real-time (< 10ms).

#### Sample `litefs.yml` Configuration:
```yaml
fuse:
  dir: "/litefs"

data:
  dir: "/var/lib/litefs"

exit-on-error: false

proxy:
  addr: ":8080"
  target: "localhost:3000"
  db: "production.db"
  passthrough:
    - "*.png"
    - "*.css"

lease:
  type: "consul"
  candidate: true
  promote: true
  consul:
    url: "http://consul:8500"
    key: "litefs/primary"
```

---

## 4. Multi-Region Read Replicas vs. Primary Writes

To prevent split-brain issues, the standard distributed pattern enforces **Local Reads + Forwarded Writes**:

```
[Edge Node (Frankfurt)]
       │
       ├─ READ QUERY  ────────> [Local SQLite Replica] (0.5ms)
       │
       └─ WRITE QUERY ────────> [Reverse Proxy / LiteFS Primary Forwarder]
                                      │
                                      ▼ (Cross-Region TLS)
                              [Primary Region (Virginia)]
                                      │
                                      ▼ Commit WAL
                              [Primary SQLite / Postgres]
                                      │
                                      ▼ Stream Transaction Log
                              [Replicas Worldwide]
```

### LiteFS Automatic Write Forwarding:
LiteFS includes a built-in HTTP proxy that inspects incoming HTTP requests:
1. `GET` / `HEAD` requests are served by the local replica node.
2. `POST` / `PUT` / `DELETE` / `PATCH` requests are automatically routed directly to the elected primary node using the `Fly-Replay` or internal proxy header.

---

## 5. Building an Edge Micro-Gateway with `workerd`

The open-source `workerd` runtime allows developers to execute JavaScript/TypeScript edge functions locally or self-hosted in Docker.

### Sample `config.capnp` (workerd Configuration):
```capnp
using Workerd = import "/workerd/workerd.capnp";

const config :Workerd.Config = (
  services = [
    (name = "edge-proxy", worker = .edgeWorker),
  ],
  sockets = [
    (name = "http", address = "*:8080", http = (), service = "edge-proxy"),
  ],
);

const edgeWorker :Workerd.Worker = (
  modules = [
    (name = "worker.js", esModule = embed "worker.js"),
  ],
  compatibilityDate = "2026-01-01",
);
```

### Sample `worker.js`:
```javascript
export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);

    // Geolocation and request timing header injection
    const startTime = performance.now();
    
    // Serve static asset or forward to backend
    if (url.pathname === '/healthz') {
      return new Response(JSON.stringify({ status: 'healthy', edge: 'self-hosted-workerd' }), {
        headers: { 'Content-Type': 'application/json' },
      });
    }

    const response = await fetch(request);
    const duration = (performance.now() - startTime).toFixed(2);

    const newHeaders = new Headers(response.headers);
    newHeaders.set('X-Edge-Duration', `${duration}ms`);
    newHeaders.set('Server-Timing', `edge;dur=${duration}`);

    return new Response(response.body, {
      status: response.status,
      headers: newHeaders,
    });
  },
};
```

---

## 6. Edge Decision Matrix

| Requirement | Centralized PostgreSQL (FastAPI / Laravel) | Edge SSR + LibSQL Replicas | Local-First (wa-sqlite + Yjs) |
| :--- | :--- | :--- | :--- |
| **P99 Read Latency** | 60–180ms (geographic dependent) | **8–25ms globally** | **< 1ms (on device)** |
| **Write Latency** | 20–80ms | 100–250ms (forwarded to primary) | **< 1ms (async sync)** |
| **Operational Complexity** | Low (Single DB cluster) | Moderate (Replication daemons) | Moderate-High (CRDTs, Sync engine) |
| **Offline Capability** | 0% | 0% (Edge cached reads only) | **100% full read/write** |
| **Ideal Workloads** | B2B SaaS, Admin portals, FinTech | Global E-commerce, CMS, News media | Mobile apps, Note-taking, Figma-like tools |
