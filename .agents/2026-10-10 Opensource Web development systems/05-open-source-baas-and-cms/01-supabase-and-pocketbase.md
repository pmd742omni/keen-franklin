# Open Source BaaS: Supabase Self-Hosted, PocketBase, and Appwrite (2026)

> Technical reference for open-source Backend-as-a-Service infrastructure, Row Level Security (RLS) architecture, and single-binary embedded engines.

---

## 1. Architectural Comparison

| Dimension | Supabase (Self-Hosted) | PocketBase | Appwrite |
|---|---|---|---|
| **Core Persistence** | PostgreSQL 16/17 | Embedded SQLite (WAL) | MariaDB / PostgreSQL / Redis |
| **Deployment Footprint** | Multi-container Docker Compose (~10 containers) | Single static compiled Go binary (~35 MB) | Multi-container Docker Compose |
| **Auth & Security** | PostgreSQL Row Level Security (RLS) + JWT | Go handler rules + SQLite filters | Server-side API key & session permissions |
| **Realtime Engine** | Realtime (Elixir) via Postgres WAL logical replication | Go WebSockets / SSE | WebSockets (C++ / Node.js) |
| **Ideal Use Case** | Production web applications, enterprise scaling | Solo founders, embedded appliances, rapid MVPs | Multi-platform mobile and web applications |

---

## 2. Supabase: PostgreSQL Row Level Security (RLS) Mastery

In Supabase architectures, authorization logic does not live in procedural application controllers—it is enforced directly inside the PostgreSQL kernel:

```sql
-- Enabling RLS on sensitive table
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only read documents belonging to their organization
CREATE POLICY "org_members_read_documents"
ON documents
FOR SELECT
TO authenticated
USING (
    organization_id IN (
        SELECT organization_id FROM organization_memberships
        WHERE user_id = auth.uid()
    )
);

-- Policy: Only workspace administrators can delete documents
CREATE POLICY "org_admins_delete_documents"
ON documents
FOR DELETE
TO authenticated
USING (
    EXISTS (
        SELECT 1 FROM organization_memberships
        WHERE user_id = auth.uid()
          AND organization_id = documents.organization_id
          AND role = 'admin'
    )
);
```

---

## 3. PocketBase: The Single-Binary Powerhouse

PocketBase compiles into a single executable that includes an embedded SQLite database, real-time subscriptions, file storage, authentication (OAuth2, email/password), and an administrative control panel:

```bash
# Running PocketBase locally or on a $4/month VPS
./pocketbase serve --http="0.0.0.0:8090"
```

Frontend JavaScript/TypeScript SDK:
```ts
import PocketBase from 'pocketbase';

const pb = new PocketBase('https://api.myproject.com');

// Subscribe to real-time changes on records
pb.collection('messages').subscribe('*', function (e) {
  console.log(`Action: ${e.action}, Record:`, e.record);
});
```
