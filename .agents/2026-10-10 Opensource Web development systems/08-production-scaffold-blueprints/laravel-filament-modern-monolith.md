# Production Scaffold Blueprint: Laravel 11/12 + Filament v3 + Inertia Modern Monolith

> Copy-paste ready production architecture configuration for enterprise SaaS applications.

---

## 1. `composer.json` Dependencies

```json
{
  "name": "enterprise/modern-laravel-app",
  "type": "project",
  "description": "High-performance Laravel monolith with Filament v3 and Inertia React 19.",
  "require": {
    "php": "^8.3",
    "filament/filament": "^3.2",
    "inertiajs/inertia-laravel": "^2.0",
    "laravel/framework": "^11.0",
    "laravel/octane": "^2.5",
    "laravel/sanctum": "^4.0",
    "predis/predis": "^2.2"
  },
  "require-dev": {
    "fakerphp/faker": "^1.23",
    "mockery/mockery": "^1.6",
    "pestphp/pest": "^3.0",
    "pestphp/pest-plugin-laravel": "^3.0"
  },
  "autoload": {
    "psr-4": {
      "App\\": "app/",
      "Database\\Factories\\": "database/factories/",
      "Database\\Seeders\\": "database/seeders/"
    }
  },
  "scripts": {
    "post-autoload-dump": [
      "Illuminate\\Foundation\\ComposerScripts::postAutoloadDump",
      "@php artisan package:discover --ansi"
    ]
  }
}
```

---

## 2. Core Service Provider Setup with Query Guardrails

```php
// app/Providers/AppServiceProvider.php
namespace App\Providers;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Log;
use Illuminate\Support\ServiceProvider;

class AppServiceProvider extends ServiceProvider
{
    public function register(): void
    {
        //
    }

    public function boot(): void
    {
        // Strict Eloquent modes in development/testing
        Model::preventLazyLoading(! $this->app->isProduction());
        Model::preventSilentlyDiscardingAttributes(! $this->app->isProduction());
        Model::preventAccessingMissingAttributes(! $this->app->isProduction());

        // Log slow queries (>500ms) in production
        if ($this->app->isProduction()) {
            DB::whenQueryingForLongerThan(500, function ($connection) {
                Log::warning("Database query threshold exceeded: {$connection->totalQueryDuration()}ms");
            });
        }
    }
}
```
