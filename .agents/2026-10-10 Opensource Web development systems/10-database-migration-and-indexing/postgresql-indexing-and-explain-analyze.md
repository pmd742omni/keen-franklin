# PostgreSQL Indexing Mastery & EXPLAIN (ANALYZE, BUFFERS) (2026)

> Production engineering guide for query optimization, index selection, and execution plan diagnosis.

---

## 1. Index Type Selection Matrix

| Index Type | Internal Data Structure | Best Suited For | Query Operators |
|---|---|---|---|
| **B-Tree** | Balanced Tree | Equality and range queries (Default) | `=`, `<`, `<=`, `>`, `>=`, `BETWEEN`, `IN` |
| **GIN** | Generalized Inverted Index | JSONB documents, arrays, full-text search | `@>`, `?`, `?|`, `@@` |
| **BRIN** | Block Range Index | Massive append-only time-series tables ($> 100\text{M}$ rows) | Range queries on naturally sorted columns |
| **HNSW** | Hierarchical Navigable Small World | AI vector embeddings (`pgvector`) | `<=>` (cosine), `<->` (L2 distance), `<#>` |

---

## 2. Advanced Indexing Patterns

### 2.1 Covering Indexes (`INCLUDE`)
Allows PostgreSQL to satisfy queries purely from the index pages without fetching the underlying table heap (Index-Only Scan):

```sql
-- Satisfies 'SELECT id, email, name FROM users WHERE email = ?' exclusively from index
CREATE INDEX idx_users_email_covering ON users (email) INCLUDE (name);
```

### 2.2 Partial Indexes
Reduces index footprint and maintenance overhead by indexing only a critical subset of rows:

```sql
-- Indexes only unprocessed jobs; ignores millions of finished jobs
CREATE INDEX idx_pending_jobs ON queue_jobs (priority, created_at)
WHERE status = 'pending';
```

---

## 3. Diagnosing Queries with `EXPLAIN (ANALYZE, BUFFERS)`

Always analyze query plans with buffer cache metrics enabled:

```sql
EXPLAIN (ANALYZE, BUFFERS, VERBOSE)
SELECT * FROM orders
WHERE customer_id = 'c_987' AND status = 'shipped'
ORDER BY created_at DESC
LIMIT 20;
```

### Red Flags in Query Plans:
- **`Seq Scan` on High-Cardinality Tables:** Missing index on filter columns.
- **`Buffers: shared read=...` vs `shared hit=...`:** High `shared read` indicates data is being read from physical disk rather than RAM buffer cache.
- **`Sort Method: external merge Disk`:** Work memory is too small to complete the sort in RAM; increase `work_mem` or create an index matching the `ORDER BY` clause.
