---
name: go-backend-craft
description: "Mastery of Go 1.23+ web engineering: Chi and stdlib routing, sqlc compile-time SQL, bounded goroutine worker pools, pgx connection pools, and structured logging with slog."
risk: none
source: workspace
date_added: "2026-10-10"
---

# Go Backend Craft

> Autonomous engineering guide for designing, implementing, and optimizing production-grade, low-latency, high-concurrency Go web services.

## 🎯 Selective Reading Rule

**Read ONLY files relevant to the request!** Check the content map, find what you need.

---

## 📑 Content Map

| File | Description | When to Read |
|---|---|---|
| `references/chi-and-stdlib-routing.md` | Routing, middleware chains, context timeouts, request lifecycle | Scaffolding HTTP services and middleware |
| `references/sqlc-database-layer.md` | sqlc setup, queries, transactions, and pgxpool integration | Writing database queries and managing transactions |
| `references/goroutine-worker-pools.md` | Bounded worker pools, channel backpressure, graceful shutdown | Processing asynchronous background jobs |

---

## 🔗 Related Skills

| Need | Skill |
|---|---|
| Database design & indexing | `@[skills/database-design]` |
| API protocols & ConnectRPC | `@[skills/api-patterns]` |
| Fullstack system architecture | `@[skills/fullstack-open-source-architect]` |

---

## ✅ Decision Checklist

Before writing Go web services:

- [ ] **Propagated `context.Context` throughout all I/O calls?** (Database queries, outbound HTTP calls, queue dispatches).
- [ ] **Configured production HTTP server timeouts?** (`ReadTimeout`, `WriteTimeout`, `IdleTimeout` to prevent Slowloris attacks).
- [ ] **Used `sqlc` instead of dynamic ORMs for high-traffic paths?**
- [ ] **Bounded goroutine creation?** (Never spawn unthrottled `go func()` in HTTP handlers; use bounded worker channels).
- [ ] **Implemented graceful shutdown?** (Listen for `SIGTERM`/`SIGINT`, drain active connections with `server.Shutdown(ctx)`).

---

## ❌ Anti-Patterns

**DON'T:**
- Spawn unbounded goroutines per incoming HTTP request without concurrency limits (can exhaust file descriptors and memory under load spikes).
- Ignore returned errors (`_ = file.Close()`) on critical I/O operations.
- Pass `context.Background()` into handlers where `r.Context()` is available (breaks cancellation propagation when clients disconnect).
- Use global mutable variables across concurrent HTTP handlers without mutex protection.

**DO:**
- Use structured logging via the standard library `log/slog`.
- Return domain errors and handle HTTP mapping at the boundary handler layer.
- Pool database connections using `jackc/pgx/v5/pgxpool`.
