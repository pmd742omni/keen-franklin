# Zero-Downtime Database Migrations: The Expand & Contract Pattern (2026)

> Technical reference for performing live database schema changes without downtime or lock contention in high-traffic applications.

---

## 1. The Expand and Contract Pattern

Never rename or modify columns in a single migration while application traffic is running. Execute changes across three distinct release phases:

```mermaid
sequenceDiagram
    participant App as Web Application (Code)
    participant DB as PostgreSQL Database
    
    Note over App,DB: Phase 1: Expand (Deploy Schema)
    App->>DB: Add new column (nullable or default)
    Note over App,DB: Phase 2: Dual-Writing (Deploy App Code v2)
    App->>DB: App writes to BOTH old and new columns; reads from old
    App->>DB: Backfill historical rows in background chunks
    Note over App,DB: Phase 3: Switch Reads & Contract (Deploy App Code v3)
    App->>DB: App reads strictly from new column
    App->>DB: Drop old column in safe subsequent migration
```

---

## 2. PostgreSQL Safe vs Dangerous Migration Checklist

| Operation | Risk Level | Safe Execution Technique |
|---|---|---|
| **Add Index** | ⚠️ High (Table Lock) | `CREATE INDEX CONCURRENTLY idx_name ON table (col);` (Prevents write locks) |
| **Add Column with Default** | ✅ Safe in PG 11+ | `ALTER TABLE tbl ADD COLUMN col INT DEFAULT 0 NOT NULL;` (Metadata only update) |
| **Add Foreign Key** | ⚠️ High (Full Table Scan) | `ALTER TABLE tbl ADD CONSTRAINT fk_name FOREIGN KEY (col) REFERENCES other(id) NOT VALID;` followed by `ALTER TABLE tbl VALIDATE CONSTRAINT fk_name;` |
| **Drop Column** | ⚠️ High (Active code fails) | Remove references in application code first. Release app. Verify telemetry. Then drop column. |
| **Rename Column** | ❌ Fatal (Instant downtime) | Use Expand/Contract with generated virtual column or trigger sync. |
