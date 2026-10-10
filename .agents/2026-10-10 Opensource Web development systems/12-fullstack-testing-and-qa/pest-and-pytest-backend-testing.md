# Backend Testing Mastery: Pest 3 (PHP) & Pytest (Python) (2026)

> Technical reference for unit, integration, and architecture testing patterns in modern backend engineering.

---

## 1. Pest PHP 3 Architecture & Declarative Tests

Pest simplifies PHP testing with an expressive functional syntax and automated architectural boundary enforcement.

### 1.1 Expressive Feature Test with Datasets
```php
// tests/Feature/BillingTest.php
use App\Models\User;
use App\Models\Plan;

it('calculates upgrade pricing correctly across tiers', function (string $currentTier, string $newTier, int $expectedCharge) {
    $user = User::factory()->subscribedTo($currentTier)->create();
    
    $response = $this->actingAs($user)->postJson('/api/billing/upgrade', [
        'plan' => $newTier,
    ]);

    $response->assertOk()
        ->assertJson(['charged_cents' => $expectedCharge]);
})->with([
    'basic to pro' => ['basic', 'pro', 2000],
    'basic to enterprise' => ['basic', 'enterprise', 8000],
    'pro to enterprise' => ['pro', 'enterprise', 6000],
]);
```

### 1.2 Architectural Guardrails in Pest 3
```php
// tests/ArchTest.php
arch('strict strict types everywhere')
    ->expect('App')
    ->toUseStrictTypes();

arch('controllers stay thin and do not inject database facades')
    ->expect('App\Http\Controllers')
    ->not->toUse('Illuminate\Support\Facades\DB');

arch('domain models do not call external HTTP services')
    ->expect('App\Models')
    ->not->toUse('Illuminate\Support\Facades\Http');
```

---

## 2. Pytest Async Testing Architecture (Python)

Using `pytest-asyncio` with transactional database isolation:

```python
# tests/conftest.py
import pytest
from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from app.db.base import Base

TEST_DB_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/test_db"
engine = create_async_engine(TEST_DB_URL)

@pytest.fixture(scope="session", autouse=True)
async def setup_test_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSession(engine) as session:
        # Wrap test in a savepoint transaction that rolls back after test completes
        async with session.begin():
            yield session
            await session.rollback()
```

### Async Endpoint Test with HTTPX
```python
# tests/test_orders.py
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_create_order_persists_successfully(db_session):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        payload = {
            "customer_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
            "items": [{"sku": "PROD-001", "quantity": 2, "unit_price": 29.99}]
        }
        res = await client.post("/api/v1/orders/", json=payload)
        
        assert res.status_code == 201
        data = res.json()
        assert data["total_amount"] == 59.98
        assert "id" in data
```
