# Django Ninja & Django 5+ Async Architecture Guide

> Technical reference for combining Django's ORM, auth, and Admin with FastAPI-style Pydantic schemas and auto-generated OpenAPI documentation.

---

## 1. Django Ninja Architecture

Django Ninja sits natively on top of Django's URL routing and ASGI/WSGI handlers:
- **No Serialization Overhead:** Uses Pydantic v2 directly for request validation and response serialization.
- **Native Django ORM Integration:** Automatically handles Django model querysets and pagination.
- **Built-in Security & Routers:** Modular `Router` objects with declarative authentication handlers (API keys, JWT, Django session auth).

```python
# api/routers/users.py
from ninja import Router, Schema
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from typing import List

User = get_user_model()
router = Router(tags=["Users"])

class UserOut(Schema):
    id: int
    username: str
    email: str
    is_active: bool

class UserCreate(Schema):
    username: str
    email: str
    password: str

@router.get("/", response=List[UserOut])
def list_users(request):
    return User.objects.filter(is_active=True)

@router.post("/", response={201: UserOut})
def create_user(request, payload: UserCreate):
    user = User.objects.create_user(
        username=payload.username,
        email=payload.email,
        password=payload.password
    )
    return 201, user
```

---

## 2. Async Views and Async ORM in Django 5+

Django 5+ supports asynchronous iteration and transactions:

```python
from ninja import Router
from asgiref.sync import sync_to_async
from .models import Invoice

router = Router()

@router.get("/invoices/summary")
async def invoice_summary(request):
    # Non-blocking async aggregation
    total_revenue = await Invoice.objects.filter(is_paid=True).aaggregate(
        total=models.Sum('amount')
    )
    return {"total_revenue": total_revenue['total'] or 0}
```
