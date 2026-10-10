# Open-Source In-Memory & Key-Value Stores: Valkey, Redis OSS, and Dragonfly (2026)

> Technical analysis of high-throughput caching layers, the Linux Foundation Valkey initiative, and distributed memory architectures.

---

## 1. The Open-Source In-Memory Landscape (Post-2024 Licensing Transition)

Following Redis Ltd.'s shift away from open-source BSD licensing to dual RSALv2/SSPL licenses, the global technology consortium organized under the **Linux Foundation** to establish **Valkey** as the official, truly open-source successor.

| Engine | License | Concurrency Architecture | Memory Efficiency | Protocol Compatibility |
|---|---|---|---|---|
| **Valkey 8+** | BSD-3-Clause | Single-threaded event loop with I/O threads | High (jemalloc integration) | 100% Redis RESP2/RESP3 compatible |
| **Dragonfly** | BSL / Source-Available | Multi-threaded shared-nothing architecture | Ultra-High (hardware thread mapping) | Drop-in Redis/Memcached client compatible |
| **Redict** | LGPL-3.0 | Conservative, rock-solid stable fork | High | 100% Redis 7.2 API compatible |

---

## 2. Core Architectural Patterns

### 2.1 Cache-Aside Pattern with Stampede Protection
Preventing cache stampedes (where thousands of concurrent requests hit the primary database when a cache key expires) using distributed locks or probabilistic early expiration:

```ts
// TypeScript cache-aside with early expiration
async function getWithXFetch<T>(
  key: string,
  ttlSeconds: number,
  fetchFn: () => Promise<T>,
  beta: number = 1.0 // Probabilistic factor
): Promise<T> {
  const cached = await valkey.get(key);
  if (cached) {
    const { value, delta, expiry } = JSON.parse(cached);
    const timeRemaining = expiry - Date.now();
    
    // Probabilistic early recomputation (Optimal Probabilistic Cache algorithm)
    if (-delta * beta * Math.log(Math.random()) < timeRemaining) {
      return value;
    }
  }

  // Cache miss or early refresh triggered
  const start = Date.now();
  const freshData = await fetchFn();
  const delta = Date.now() - start;
  
  await valkey.set(
    key,
    JSON.stringify({ value: freshData, delta, expiry: Date.now() + ttlSeconds * 1000 }),
    'EX',
    ttlSeconds
  );
  
  return freshData;
}
```

### 2.2 Distributed Rate Limiting via Sliding Window (Lua Scripting)
Executing rate limits atomically directly inside the Valkey engine via Lua:

```lua
-- sliding_window_rate_limiter.lua
-- KEYS[1]: User rate limit key (e.g., ratelimit:user_123)
-- ARGV[1]: Current UNIX timestamp in milliseconds
-- ARGV[2]: Window size in milliseconds (e.g., 60000 for 1 min)
-- ARGV[3]: Maximum permitted requests

local key = KEYS[1]
local now = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local limit = tonumber(ARGV[3])
local clearBefore = now - window

-- Remove requests older than the sliding window
redis.call('ZREMRANGEBYSCORE', key, 0, clearBefore)

-- Count remaining requests in the active window
local currentRequests = redis.call('ZCARD', key)

if currentRequests < limit then
    -- Record this request
    redis.call('ZADD', key, now, now)
    redis.call('PEXPIRE', key, window)
    return 1 -- Allowed
else
    return 0 -- Rejected (Rate limit exceeded)
end
```
