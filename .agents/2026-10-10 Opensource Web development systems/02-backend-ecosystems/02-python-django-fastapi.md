# Python Web Systems: FastAPI, Django 5+, and High-Concurrency Asynchronous Architectures (2026)

> Technical reference for modern Python 3.12/3.13 web frameworks: FastAPI with Pydantic v2, Django 5+ async core, Django Ninja, and SQLAlchemy 2.0.

---

## 1. FastAPI: High-Throughput Async Microservices

FastAPI remains the leading standard for Python API engineering, powered by Starlette for ASGI routing and **Pydantic v2** for validation.

### 1.1 Pydantic v2 Core (Rust Architecture)
Pydantic v2 is rewritten in Rust (`pydantic-core`), delivering a 5x to 20x performance speedup in schema validation and JSON serialization, removing Python's historical serialization bottleneck.

```python
# app/schemas/order.py
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

class OrderItemSchema(BaseModel):
    model_config = ConfigDict(strict=True)
    
    sku: str = Field(min_length=3, max_length=30)
    quantity: int = Field(gt=0, le=100)
    unit_price: float = Field(gt=0.0)

class OrderCreateSchema(BaseModel):
    customer_id: UUID
    items: list[OrderItemSchema] = Field(min_length=1)

class OrderResponseSchema(BaseModel):
    id: UUID
    customer_id: UUID
    items: list[OrderItemSchema]
    total_amount: float
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
```

### 1.2 Async Dependency Injection & SQLAlchemy 2.0 AsyncSession

```python
# app/api/endpoints/orders.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_async_db
from app.models.order import Order
from app.schemas.order import OrderCreateSchema, OrderResponseSchema

router = APIRouter(prefix="/orders", tags=["Orders"])

@router.post("/", response_model=OrderResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_order(
    payload: OrderCreateSchema,
    db: AsyncSession = Depends(get_async_db),
    # current_user: User = Depends(get_current_active_user)
):
    total = sum(item.quantity * item.unit_price for item in payload.items)
    order = Order(
        customer_id=payload.customer_id,
        items=[item.model_dump() for item in payload.items],
        total_amount=total,
    )
    db.add(order)
    await db.commit()
    await db.refresh(order)
    return order
```

---

## 2. Django 5+: Enterprise Monolith & Async Evolution

Django 5+ integrates modern Python asynchronous features while maintaining its signature "batteries-included" toolkit (ORM, built-in admin, auth, CSRF, security middleware).

### 2.1 Async ORM & Concurrency
Django provides asynchronous query iterators and persistence calls, preventing blocking of ASGI workers:

```python
# Async Django View
from django.http import JsonResponse
from .models import Article

async def latest_articles(request):
    # Non-blocking async ORM evaluation
    articles = []
    async for article in Article.objects.filter(is_published=True).order_by('-published_at')[:10]:
        articles.append({'title': article.title, 'slug': article.slug})
    return JsonResponse({'status': 'ok', 'data': articles})
```

### 2.2 Django Ninja: The Best of Django and FastAPI
**Django Ninja** allows developers to leverage Django's ORM and Admin while using FastAPI-style Pydantic schemas and auto-generated OpenAPI documentation:

```python
from ninja import NinjaAPI, Schema
from typing import List
from .models import Product

api = NinjaAPI(title="Storefront API", version="1.0.0")

class ProductOut(Schema):
    id: int
    name: str
    price: float
    inventory_count: int

@api.get("/products", response=List[ProductOut])
def list_products(request):
    return Product.objects.filter(is_active=True)
```

---

## 3. Background Task Architecture

Python web applications offload CPU-intensive operations (PDF generation, email delivery, AI inference pipelines) to dedicated worker pools:

| Task Queue | Broker | Best Suited For | Operational Complexity |
|---|---|---|---|
| **Celery** | Redis / RabbitMQ | Complex enterprise workflows, canvas chaining, retries | High (separate beat/worker processes) |
| **Dramatiq** | Redis / RabbitMQ | Modern, lightweight, thread-safe asynchronous task execution | Medium (simple configuration, low overhead) |
| **RQ (Redis Queue)** | Redis | Simple lightweight tasks, straightforward worker scripts | Low (intuitive, minimalist) |
| **FastAPI BackgroundTasks** | In-process asyncio | Simple in-memory fire-and-forget tasks (sending confirmation email) | Minimal (zero broker infrastructure) |
