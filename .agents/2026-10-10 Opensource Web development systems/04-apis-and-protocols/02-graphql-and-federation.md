# Modern GraphQL & Federated Architectures (2026)

> Technical reference for GraphQL Yoga, Code-First Schema Construction with Pothos, Subgraphs, and DataLoader N+1 mitigation.

---

## 1. When to Use (and When to Avoid) GraphQL

### Ideal Scenarios
- Complex mobile and multi-client ecosystems requiring disparate data shapes in a single round-trip.
- Large enterprise organizations with dozens of microservices aggregated behind a single unified Federated Graph.

### Anti-Patterns & Pitfalls
- Simple CRUD applications (adds unnecessary schema maintenance overhead).
- High-frequency edge execution where lightweight REST/RPC headers and edge caching (`Cache-Control: max-age`) are critical.

---

## 2. Code-First GraphQL: Pothos & GraphQL Yoga

Pothos provides 100% type-safe schema construction without manual code-generation steps:

```ts
// schema/builder.ts
import SchemaBuilder from '@pothos/core';
import PrismaPlugin from '@pothos/plugin-prisma';
import type PrismaTypes from '@pothos/plugin-prisma/generated';
import { prisma } from '../db';

export const builder = new SchemaBuilder<{
  PrismaTypes: PrismaTypes;
}>({
  plugins: [PrismaPlugin],
  prisma: { client: prisma },
});

// Defining User Type
builder.prismaObject('User', {
  fields: (t) => ({
    id: t.exposeID('id'),
    email: t.exposeString('email'),
    posts: t.relation('posts', {
      args: { limit: t.arg.int({ defaultValue: 10 }) },
      query: (args) => ({ take: args.limit }),
    }),
  }),
});
```

---

## 3. Resolving the N+1 Problem: DataLoader

```ts
import DataLoader from 'dataloader';
import { db } from '../db';

// Batches 50 individual author queries into a single SQL 'WHERE id IN (...)'
export const userLoader = new DataLoader<string, User>(async (userIds) => {
  const users = await db.user.findMany({
    where: { id: { in: [...userIds] } },
  });
  const userMap = new Map(users.map((u) => [u.id, u]));
  return userIds.map((id) => userMap.get(id) || new Error(`User ${id} not found`));
});
```
