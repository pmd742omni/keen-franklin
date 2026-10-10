# Laravel Octane & High-Throughput Queue Architecture (2026)

> Technical reference for persistent memory runtime management (FrankenPHP/Octane), state leakage prevention, and scalable Redis/Valkey queue workers.

---

## 1. Octane Memory Lifecycle & Leak Prevention

Under Laravel Octane with FrankenPHP, the framework boots once and keeps services in RAM across millions of HTTP requests. 

### 1.1 Preventing State Leakage Across Requests
Because the application does not reset between requests, registering stateful singletons can inadvertently leak data between different users:

```php
// ❌ Dangerous under Octane: service maintains state across separate user requests
class CartManager
{
    protected array $items = []; // Will persist to the next visitor!
}

// ✅ Safe under Octane: Resolve per request via request scope or reset listeners
```

In `config/octane.php`, register listeners to clear stale in-memory state:
```php
'listeners' => [
    OperationTerminated::class => [
        FlushTemporarySessionData::class,
    ],
    RequestReceived::class => [
        // Resetting contextual bindings
    ],
],
```

---

## 2. High-Throughput Asynchronous Queue Workers

### 2.1 Worker Daemon Configuration with Horizon
Run multi-process queue consumers with balance strategies:

```php
// config/horizon.php
'environments' => [
    'production' => [
        'supervisor-default' => [
            'connection' => 'redis',
            'queue' => ['high', 'default', 'low'],
            'balance' => 'auto',
            'autoScalingStrategy' => 'time',
            'maxProcesses' => 32,
            'minProcesses' => 4,
            'memory' => 128,
            'tries' => 3,
            'timeout' => 60,
        ],
    ],
],
```

### 2.2 Rate-Limited Job Dispatching
Protect third-party APIs (Stripe, Twilio, SendGrid) from hitting rate limit thresholds:

```php
// app/Jobs/ProcessPayment.php
namespace App\Jobs;

use Illuminate\Support\Facades\Redis;

class ProcessPayment implements ShouldQueue
{
    public function middleware(): array
    {
        return [
            // Limits execution to 10 jobs every 1 second via Redis
            new RateLimited('payments-gateway'),
        ];
    }

    public function handle(): void
    {
        // Payment execution logic...
    }
}
```
