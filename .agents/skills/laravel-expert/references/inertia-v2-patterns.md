# Inertia.js v2 Modern Monolith Architectural Patterns

> Technical reference for building full-stack reactive applications with Laravel backend and React 19 / Vue 3 frontend.

---

## 1. Inertia.js v2 Core Innovations

Inertia eliminates API layers (REST/GraphQL) while giving developers the full power of a client-side Single Page Application (SPA).

### Key Features of Inertia v2
1. **Deferred Props (`Inertia::defer`):** Allows heavy backend metrics or third-party API data to stream into the page asynchronously after the initial HTML/JSON render completes.
2. **Instant Prefetching:** `<Link href="/dashboard" prefetch>` preloads page props into client memory on hover or viewport intersection.
3. **Optimistic Visits:** Instantaneous UI state transitions before server response confirmation.

---

## 2. Shared Data & Authentication State

Share global application state (authenticated user, flash notifications, feature flags) via `HandleInertiaRequests` middleware:

```php
// app/Http/Middleware/HandleInertiaRequests.php
namespace App\Http\Middleware;

use Illuminate\Http\Request;
use Inertia\Middleware;

class HandleInertiaRequests extends Middleware
{
    protected $rootView = 'app';

    public function share(Request $request): array
    {
        return [
            ...parent::share($request),
            'auth' => [
                'user' => $request->user() ? [
                    'id' => $request->user()->id,
                    'name' => $request->user()->name,
                    'email' => $request->user()->email,
                    'role' => $request->user()->role,
                ] : null,
            ],
            'flash' => [
                'success' => fn () => $request->session()->get('success'),
                'error' => fn () => $request->session()->get('error'),
            ],
        ];
    }
}
```

---

## 3. Frontend Form Handling with React 19 & Inertia Form Helper

```tsx
import { useForm } from '@inertiajs/react';
import React from 'react';

export function CreateTeamForm() {
  const { data, setData, post, processing, errors, reset } = useForm({
    name: '',
    description: '',
  });

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    post('/teams', {
      onSuccess: () => reset(),
      preserveScroll: true,
    });
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="block text-sm font-medium">Team Name</label>
        <input
          type="text"
          value={data.name}
          onChange={(e) => setData('name', e.target.value)}
          className="input-field"
        />
        {errors.name && <p className="text-red-500 text-xs mt-1">{errors.name}</p>}
      </div>

      <button type="submit" disabled={processing} className="btn-primary">
        {processing ? 'Creating...' : 'Create Team'}
      </button>
    </form>
  );
}
```
