# Open Source Relational Databases: PostgreSQL 17, MySQL 8.4, and SQLite/LibSQL (2026)

> Deep technical specification of modern open-source relational persistence layers, vector indexing (pgvector), JSONB capabilities, and high-performance replication.

---

## 1. PostgreSQL 17: The Modern Universal Database

PostgreSQL remains the undisputed industry standard for open-source data storage due to its ACID integrity, rich extension ecosystem, and hybrid relational/document capabilities.

### 1.1 pgvector: Native AI & Semantic Vector Embeddings
With the rise of local and cloud LLMs, `pgvector` eliminates the operational overhead of running dedicated vector databases (Pinecone, Weaviate):
- **Index Types:**
  - **HNSW (Hierarchical Navigable Small World):** Provides superior query recall and ultra-fast sub-millisecond search latencies at the cost of higher build time and memory.
  - **IVFFlat:** Inverted file index with flat compression; faster build times, suitable for massive datasets with lower memory limits.

```sql
-- Enabling extension and vector column
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE document_chunks (
    id BIGSERIAL PRIMARY KEY,
    document_id UUID NOT NULL,
    content TEXT NOT NULL,
    embedding vector(1536) -- OpenAI text-embedding-3-small dimension
);

-- Building an HNSW cosine similarity index
CREATE INDEX ON document_chunks USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- Querying the top 5 most semantically similar chunks
SELECT id, content, 1 - (embedding <=> '[0.012, -0.045, ...]'::vector) AS similarity_score
FROM document_chunks
ORDER BY embedding <=> '[0.012, -0.045, ...]'::vector
LIMIT 5;
```

### 1.2 JSONB & Hybrid Document-Relational Modeling
PostgreSQL's `jsonb` type parses JSON into a decomposed binary format, allowing indexed nested queries:
- **GIN Indexing:** Creates Generalized Inverted Indexes on JSON keys and values.
- **Path Queries:** `jsonb_path_query()` enables standard JSONPath extraction.

```sql
CREATE TABLE audit_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    payload JSONB NOT NULL
);

CREATE INDEX idx_audit_payload ON audit_events USING gin (payload);

-- Query matching nested JSON criteria using containment operator (@>)
SELECT * FROM audit_events 
WHERE payload @> '{"action": "user.login", "context": {"status": "failed"}}';
```

---

## 2. SQLite & LibSQL: The Embedded and Edge Revolution

SQLite is the most widely deployed SQL database in existence. In modern web development, it has transitioned from a development toy to a primary production persistence engine:

### 2.1 Write-Ahead Logging (WAL) Mode
By default, SQLite locks the entire database file during writes. Enabling **WAL mode** allows infinite concurrent readers while a single writer operates concurrently:
```sql
PRAGMA journal_mode = WAL;
PRAGMA busy_timeout = 5000;
PRAGMA synchronous = NORMAL;
PRAGMA cache_size = -20000; -- 20MB in-memory page cache
```

### 2.2 LibSQL / Turso
An open-source fork of SQLite that adds network access (HTTP/WebSockets) and global edge replication, allowing SQLite instances to be distributed across global edge regions while keeping writes synchronized.

---

## 3. MySQL 8.4 LTS
- **InnoDB Engine Enhancements:** Optimized buffer pool flushing and improved dead lock detection.
- **Enterprise Replication:** Semi-synchronous replication, Group Replication for multi-master topologies.
- **Best Suited For:** Massive write-heavy read/write split architectures (large WordPress clusters, legacy enterprise ERPs).
