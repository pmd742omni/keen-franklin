# Async SQLAlchemy 2.0 & Alembic Migration Guide

> Technical reference for SQLAlchemy 2.0 async engine, Mapped type annotations, selectinload relationship optimization, and Alembic migrations.

---

## 1. Modern SQLAlchemy 2.0 Model Definition

```python
# app/db/base.py
from datetime import datetime, timezone
from uuid import UUID, uuid4
from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass

class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    members: Mapped[list["User"]] = relationship(
        back_populates="organization",
        cascade="all, delete-orphan",
        lazy="selectin"  # Eager loads cleanly in async environments
    )

class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    org_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)

    organization: Mapped["Organization"] = relationship(back_populates="members")
```

---

## 2. Preventing Async N+1 Cascades: `selectinload`

In SQLAlchemy 2.0 async mode, accessing an un-loaded relationship raises `MissingGreenlet: greenlet_spawn has not been called`. Always specify eager loading explicitly:

```python
from sqlalchemy import select
from sqlalchemy.orm import selectinload

async def get_org_with_members(session: AsyncSession, org_id: UUID) -> Organization | None:
    stmt = (
        select(Organization)
        .where(Organization.id == org_id)
        .options(selectinload(Organization.members))
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()
```
