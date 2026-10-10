---
name: laravel-expert
description: "Mastery of modern Laravel 11/12 architecture, Inertia.js v2, Livewire 3, Filament v3, Eloquent ORM performance tuning, Octane/FrankenPHP, and Pest 3 testing."
risk: none
source: workspace
date_added: "2026-10-10"
---

# Laravel Expert

> Autonomous architectural and engineering guide for building modern, high-performance web systems with the Laravel ecosystem.
> **Learn to build resilient, maintainable Laravel monoliths and APIs.**

## 🎯 Selective Reading Rule

**Read ONLY files relevant to the request!** Check the content map, find what you need.

---

## 📑 Content Map

| File | Description | When to Read |
|---|---|---|
| `references/eloquent-optimization.md` | Preventing N+1, subqueries, strict mode, indexing | Tuning database queries, debugging slow requests |
| `references/inertia-v2-patterns.md` | Modern monolith with React 19 / Vue 3.5, deferred props | Building full-stack SPA apps without REST boilerplate |
| `references/filament-and-livewire.md` | Filament v3 admin panels, Livewire 3 real-time components | Building admin dashboards, internal tools, form wizards |
| `references/octane-and-queues.md` | FrankenPHP worker mode, Redis/Valkey queues, Horizon | High-concurrency scaling, background processing |

---

## 🔗 Related Skills

| Need | Skill |
|---|---|
| Database modeling | `@[skills/database-design]` |
| API patterns & contracts | `@[skills/api-patterns]` |
| Frontend design tokens | `@[skills/design-system]` |
| Open source architecture | `@[skills/fullstack-open-source-architect]` |

---

## ✅ Decision Checklist

Before architecting a Laravel application:

- [ ] **Decided between Inertia.js v2, Livewire 3, or Decoupled API?**
  - Inertia: for rich React 19 / Vue 3 frontend with full-stack monolith developer velocity.
  - Livewire: for rapid Blade-native reactive apps and TALL stack workflows.
  - Decoupled API (Sanctum/Passport): for external mobile apps or third-party consumers.
- [ ] **Configured Model strict mode in `AppServiceProvider`?** (`preventLazyLoading`, `preventSilentlyDiscardingAttributes`).
- [ ] **Defined Model casts via the native `casts()` method?**
- [ ] **Configured queue driver and failed job monitoring?**
- [ ] **Selected deployment engine?** (FrankenPHP/Octane for maximum throughput, standard PHP-FPM for simple shared setups).

---

## ❌ Anti-Patterns

**DON'T:**
- Run database queries inside Blade views or loops (causes N+1 query cascades).
- Put domain business logic directly inside Controllers (use Actions, Services, or Form Requests).
- Default to building separate REST APIs and SPAs for internal/business tools when Inertia.js or Livewire achieves 3x developer velocity.
- Use `env()` outside of `config/` files (configuration caching causes `env()` to return `null`).
- Leave `APP_DEBUG=true` in production environments.

**DO:**
- Use Form Requests (`php artisan make:request`) for authorization and validation.
- Leverage Eloquent subqueries (`addSelect`) instead of in-memory collections for aggregations.
- Use Pest 3 architecture tests to enforce code boundaries.
- Cache routes, config, and views in production (`php artisan optimize`).

---

## 🛠️ When to Use

Use this skill whenever:
1. Designing, scaffolding, or refactoring Laravel 11/12 applications.
2. Integrating React 19 or Vue 3.5 via Inertia.js v2.
3. Implementing administrative dashboards or customer portals with Filament v3.
4. Profiling and eliminating slow Eloquent queries and memory bottlenecks.
5. Setting up asynchronous background jobs, queues, or FrankenPHP Octane runtime.

---

## 📋 Worked Example: Inertia v2 Deferred Props Controller

```php
namespace App\Http\Controllers;

use App\Models\Organization;
use App\Models\Invoice;
use Inertia\Inertia;
use Inertia\Response;
use Illuminate\Http\Request;

class DashboardController extends Controller
{
    public function __invoke(Request $request): Response
    {
        $organization = $request->user()->currentOrganization;

        return Inertia::render('Dashboard/Index', [
            // Instant prop: sent immediately with initial page render
            'organization' => $organization->only(['id', 'name', 'slug']),
            
            // Critical metrics: loaded synchronously
            'recentInvoices' => Invoice::query()
                ->where('organization_id', $organization->id)
                ->with(['customer:id,name,email'])
                ->latest()
                ->limit(5)
                ->get(),

            // Deferred prop: does NOT block initial page load; streams in background
            'financialSummary' => Inertia::defer(function () use ($organization) {
                return Invoice::calculateYearToDateRevenue($organization->id);
            }),
        ]);
    }
}
```
