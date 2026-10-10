# ElectricSQL & Postgres Sync Guide

> Implementing bi-directional real-time data replication between PostgreSQL 17 and client SQLite engines using ElectricSQL Shapes.

---

## 1. ElectricSQL Architecture Overview

ElectricSQL enables apps to sync slices of a central PostgreSQL database called **Shapes**:

```
[PostgreSQL 17]
       │ (Logical Replication Stream: pgoutput)
       ▼
[Electric Sync Service (Go / Elixir)]
       │ (HTTP Streaming / SSE / Shape Cache)
       ▼
[Client Web / Mobile Application]
       │
       ▼
[Local Client SQLite / PGlite / OPFS]
```

---

## 2. Server Configuration

Ensure PostgreSQL is started with logical replication enabled:
```ini
# postgresql.conf
wal_level = logical
max_replication_slots = 10
max_wal_senders = 10
```

Create an Electric publication:
```sql
CREATE PUBLICATION electric_publication FOR ALL TABLES;
```

---

## 3. Client Reactive Shape Consumption

In React or Next.js applications, use the `@electric-sql/react` hook to subscribe reactively:

```typescript
import { useShape } from '@electric-sql/react';

interface ProjectIssue {
  id: string;
  project_id: string;
  title: string;
  status: 'todo' | 'in_progress' | 'done';
}

export function ProjectIssuesList({ projectId }: { projectId: string }) {
  const { data: issues, isLoading } = useShape<ProjectIssue>({
    url: `${process.env.NEXT_PUBLIC_ELECTRIC_URL}/v1/shape`,
    params: {
      table: 'issues',
      where: `project_id = '${projectId}'`,
    },
  });

  if (isLoading) return <div>Synchronizing issues locally...</div>;

  return (
    <div className="space-y-2">
      {issues.map((issue) => (
        <div key={issue.id} className="p-3 bg-slate-800 rounded flex justify-between">
          <span>{issue.title}</span>
          <span className="text-xs uppercase px-2 py-1 bg-slate-700 rounded">{issue.status}</span>
        </div>
      ))}
    </div>
  );
}
```
