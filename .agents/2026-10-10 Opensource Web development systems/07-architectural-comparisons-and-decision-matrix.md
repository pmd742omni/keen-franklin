# Open-Source Web Systems: Architectural Decision Matrix & Trade-Off Analysis (2026)

> Rigorous engineering comparison across developer velocity, total cost of ownership (TCO), runtime throughput, and long-term maintenance overhead.

---

## 1. Full-Stack Archetype Comparison Matrix

| Dimension | Laravel 11/12 + Inertia/Livewire | Next.js 15/16 + React 19 (Node/Bun) | Django 5+ / Ninja + React | Ruby on Rails 8 (Solid Stack) | Go 1.23+ (Chi + sqlc) + React SPA |
|---|---|---|---|---|---|
| **Core Paradigm** | Majestic Monolith / Modern Monolith | Full-Stack JS/TS (RSC + Actions) | Batteries-Included Python | Majestic Monolith (HTML-over-wire) | Decoupled Microservice + Static SPA |
| **Developer Velocity (MVP)** | ⚡⚡⚡⚡⚡ (Fastest) | ⚡⚡⚡⚡ (Very High) | ⚡⚡⚡⚡ (High) | ⚡⚡⚡⚡⚡ (Fastest) | ⚡⚡ (Moderate) |
| **Throughput (req/sec)** | High (10k+ with Octane/FrankenPHP) | Moderate-High (4k-8k Node/Bun) | Moderate (2k-5k ASGI) | Moderate (1.5k-4k Puma) | 🚀 Ultra-High (40k-80k) |
| **P99 Latency** | Low (2-10ms with Octane) | Low-Medium (10-35ms) | Medium (15-40ms) | Medium (20-50ms) | 🚀 Sub-millisecond (0.5-2ms) |
| **Memory Footprint / Instance** | ~80-150 MB (Octane worker) | ~150-350 MB | ~120-250 MB | ~150-300 MB | 🚀 15-30 MB |
| **Built-in Admin Panel** | Yes (Filament v3 - Best in class) | No (Custom shadcn/ui) | Yes (Django Admin) | Moderate (Avo / Administrate) | No (Build from scratch) |
| **Auth & Authorization** | Built-in (Sanctum/Breeze/Gates) | Manual / Auth.js / Lucia | Built-in (Django Auth/Permissions) | Built-in (Devise / Rails 8 Auth) | Manual / Custom middleware |
| **Background Processing** | Built-in (Queues, Horizon, Redis) | External (Inngest, BullMQ, Trigger) | Built-in / Celery / Dramatiq | Built-in (Solid Queue) | Native Goroutines / Asynq |
| **Infrastructure TCO** | Low ($10-$20 VPS via Coolify) | Medium ($20+ VPS / Vercel tiers) | Low-Medium ($15-$30 VPS) | Low ($10-$20 VPS via Kamal) | Ultra-Low ($5 VPS handles millions) |

---

## 2. In-Depth Scenario Analysis

### Scenario A: High-Velocity B2B SaaS / Internal Business Tools
- **Recommended Stack:** **Laravel 11 + Filament v3 + PostgreSQL**
- **Why:** B2B SaaS applications require complex permissions (RBAC), multi-tenancy, rich tabular data with sorting/filtering/export, audit logs, and administrative portals. Filament v3 generates complete, polished, accessible administrative and customer-facing interfaces in days rather than months.
- **Alternative:** **Next.js + shadcn/ui + Supabase** if the team is exclusively TypeScript-oriented.

### Scenario B: Public Marketing / Content-Rich Portal / E-Commerce
- **Recommended Stack:** **Astro 5 + React/Svelte Islands + Payload CMS 3.0**
- **Why:** Maximizes Core Web Vitals (LCP, FID, CLS) through zero-JS default rendering, while enabling interactive elements (cart, comments, search) via isolated islands.

### Scenario C: High-Throughput Real-Time API / Microservice Fleet
- **Recommended Stack:** **Go (Chi) + sqlc + PostgreSQL 17 + Valkey**
- **Why:** Single-binary deployment, instant boot times (<10ms), sub-millisecond p99 latencies, and minimal memory overhead allow dozens of Go microservices to run concurrently on minimal cloud infrastructure.
