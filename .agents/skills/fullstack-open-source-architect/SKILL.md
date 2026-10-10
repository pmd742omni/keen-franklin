---
name: fullstack-open-source-architect
description: "Holistic architectural guidance for selecting, integrating, containerizing, and operating open-source web ecosystems: Laravel, React, Node, Go, PostgreSQL, Valkey, Coolify, and Kamal."
risk: none
source: workspace
date_added: "2026-10-10"
---

# Fullstack Open Source Architect

> Autonomous principal engineering guide for technology stack selection, multi-tier architectural design, self-hosted deployment, and zero-cloud-lock-in operations.

## 🎯 Selective Reading Rule

**Read ONLY files relevant to the request!** Check the content map, find what you need.

---

## 📑 Content Map

| File | Description | When to Read |
|---|---|---|
| `references/stack-selection-matrix.md` | Decision frameworks: Laravel vs React vs Go vs Django vs Rails | Choosing tech stack for a new project or migration |
| `references/self-hosted-production-guide.md` | Coolify, Kamal 2, Docker Compose, Valkey, Postgres setup | Designing deployment infrastructure & VPS operations |

---

## 🔗 Related Skills

| Need | Skill |
|---|---|
| Laravel implementation | `@[skills/laravel-expert]` |
| React implementation | `@[skills/modern-react-stack]` |
| API contracts | `@[skills/api-patterns]` |
| Database schema & indexes | `@[skills/database-design]` |
| System architecture | `@[skills/architecture]` |

---

## ✅ Architectural Evaluation Framework

When advising or architecting a web project, evaluate across 5 fundamental constraints:

1. **Team Velocity vs Concurrency Needs:**
   - Need rapid product iteration, admin dashboard, complex business logic? -> **Laravel + Inertia/Livewire** or **Django Ninja**.
   - Need 50k+ websocket connections or microsecond CPU performance? -> **Go (Chi) + PostgreSQL** or **Rust (Axum)**.
2. **Infrastructure TCO (Total Cost of Ownership):**
   - Self-hosted PaaS (Coolify on Hetzner VPS) achieves 90% cloud cost reduction compared to proprietary platforms (AWS Fargate, Vercel Enterprise).
3. **Operational Surface Area:**
   - Can the team manage separate API versions, client routers, and state stores? If not, favor unified monoliths (Inertia.js, Hotwire, or Next.js fullstack).
4. **Data Durability & Access:**
   - Always default to **PostgreSQL 17** for primary relational storage. Use `pgvector` for AI embeddings before spinning up separate vector databases.
   - Use **Valkey** for shared caching, session stores, and rate limiting.

---

## ❌ Anti-Patterns

**DON'T:**
- Prematurely decompose a startup MVP into 10 separate microservices (causes network latency, distributed transaction failures, and operational burnout).
- Introduce complex third-party SaaS tools when open-source alternatives run effortlessly on self-hosted Docker (e.g. self-hosted Supabase, Coolify, Plausible, MinIO).
- Mix multiple disparate ORMs or state managers without strict domain boundaries.
