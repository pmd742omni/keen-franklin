# Eloquent ORM Performance Tuning & Optimization Guide

> Technical reference for eliminating database bottlenecks, N+1 cascades, and excessive memory utilization in Laravel applications.

---

## 1. Preventing N+1 Query Cascades

By default, accessing relationships on an un-eager-loaded model dispatches an individual SQL query for each iteration:

```php
// ❌ Anti-pattern: 1 query for 50 users + 50 individual queries for profiles = 51 queries
$users = User::limit(50)->get();
foreach ($users as $user) {
    echo $user->profile->avatar_url;
}

// ✅ Optimized: Exactly 2 queries regardless of count
$users = User::with(['profile'])->limit(50)->get();
foreach ($users as $user) {
    echo $user->profile->avatar_url;
}
```

### Enabling Framework Guardrails in Development
```php
// app/Providers/AppServiceProvider.php
public function boot(): void
{
    Model::preventLazyLoading(! $this->app->isProduction());
    Model::preventSilentlyDiscardingAttributes(! $this->app->isProduction());
}
```

---

## 2. Advanced Subquery Selections (`addSelect`)

When displaying metrics or relational child fields in tables, avoid loading full relational model collections into memory. Push computation down into SQL subqueries:

```php
// ✅ Fetches users and calculates metrics in a single SQL query
$users = User::query()
    ->select(['users.id', 'users.name', 'users.email'])
    ->addSelect([
        'total_orders' => Order::selectRaw('count(*)')
            ->whereColumn('orders.user_id', 'users.id'),
        'last_order_date' => Order::select('created_at')
            ->whereColumn('orders.user_id', 'users.id')
            ->latest()
            ->limit(1),
    ])
    ->withCasts(['last_order_date' => 'datetime'])
    ->paginate(25);
```

---

## 3. High-Volume Processing: Lazy Collections

When processing millions of records (exports, billing cycles, sync jobs), loading all models into memory causes `OutOfMemoryException`. Use cursor pagination and lazy streams:

```php
// Stream 500,000 records using 12MB of RAM via database cursor
User::query()
    ->where('is_active', true)
    ->lazyById(chunkSize: 1000)
    ->each(function (User $user) {
        dispatch(new SyncUserToCRMJob($user->id));
    });
```
