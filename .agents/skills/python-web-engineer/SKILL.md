---
name: python-web-engineer
description: "Mastery of modern Python 3.12/3.13 web architectures: FastAPI with Pydantic v2, Django 5+ async core, Django Ninja, async SQLAlchemy 2.0, Alembic, Celery, and Pytest."
risk: none
source: workspace
date_added: "2026-10-10"
---

# Python Web Engineer

> Autonomous engineering guide for designing, implementing, and optimizing high-throughput, async Python web applications and microservices.

## 🎯 Selective Reading Rule

**Read ONLY files relevant to the request!** Check the content map, find what you need.

---

## 📑 Content Map

| File | Description | When to Read |
|---|---|---|
| `references/fastapi-high-concurrency.md` | Lifespan managers, Pydantic v2, dependency injection, async endpoints | Building high-throughput REST APIs and microservices |
| `references/django-ninja-architecture.md` | Django 5+ async ORM + Pydantic v2 schemas, auth router | Building APIs using Django's ORM and Admin |
| `references/async-sqlalchemy-alembic.md` | SQLAlchemy 2.0 AsyncEngine, AsyncSession, relationships, Alembic | Modeling relational data and managing migrations |

---

## 🔗 Related Skills

| Need | Skill |
|---|---|
| Database modeling & indexing | `@[skills/database-design]` |
| API standards & contracts | `@[skills/api-patterns]` |
| Fullstack system architecture | `@[skills/fullstack-open-source-architect]` |

---

## ✅ Decision Checklist

Before architecting a Python web service:

- [ ] **Determined runtime concurrency model?** (Async endpoints using `async def` for I/O bound queries; standard `def` for CPU bound tasks to prevent event loop blocking).
- [ ] **Configured lifespan context manager in FastAPI?** (Replaces deprecated `@app.on_event("startup")` for connection pool initialization and cleanup).
- [ ] **Used Pydantic v2 `ConfigDict` and typed fields?** (`model_config = ConfigDict(from_attributes=True)` for ORM serialization).
- [ ] **Bounded SQLAlchemy async connection pool?** (`pool_size=20`, `max_overflow=10`, `pool_pre_ping=True`).
- [ ] **Isolated long-running CPU operations into worker queues?** (Celery, Dramatiq, or RQ with Valkey/Redis).

---

## ❌ Anti-Patterns

**DON'T:**
- Call blocking synchronous I/O operations (e.g. `requests.get()`, `time.sleep()`, synchronous DB drivers) inside `async def` endpoints (freezes the entire ASGI event loop).
- Use `def` endpoints with async database calls or vice versa without proper thread-pool offloading.
- Leave connection pools unbound in containerized environments.
- Use `select(*)` or unbounded `.all()` queries on large database tables.

**DO:**
- Use `httpx.AsyncClient` or `aiohttp` for outbound HTTP requests in async services.
- Leverage FastAPI dependency injection (`Depends()`) for authentication, database session scoping, and rate limiting.
- Write Pytest fixtures with `pytest-asyncio` for deterministic database test rollbacks.
