# Production Scaffold Blueprint: React 19 + Next.js App Router + Drizzle ORM

> Modern full-stack TypeScript blueprint with Server Components, Actions, and edge-ready Drizzle ORM.

---

## 1. `package.json`

```json
{
  "name": "modern-react19-fullstack",
  "version": "1.0.0",
  "scripts": {
    "dev": "next dev --turbopack",
    "build": "next build",
    "start": "next start",
    "db:push": "drizzle-kit push",
    "db:studio": "drizzle-kit studio"
  },
  "dependencies": {
    "@tanstack/react-query": "^5.50.0",
    "drizzle-orm": "^0.33.0",
    "lucide-react": "^0.440.0",
    "next": "^15.0.0",
    "postgres": "^3.4.4",
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "zod": "^3.23.8",
    "zustand": "^5.0.0"
  },
  "devDependencies": {
    "@types/node": "^22.0.0",
    "@types/react": "^19.0.0",
    "@types/react-dom": "^19.0.0",
    "drizzle-kit": "^0.24.0",
    "tailwindcss": "^4.0.0",
    "typescript": "^5.5.0"
  }
}
```

---

## 2. Drizzle Database Client & Connection Pool

```ts
// src/db/index.ts
import { drizzle } from 'drizzle-orm/postgres-js';
import postgres from 'postgres';
import * as schema from './schema';

const connectionString = process.env.DATABASE_URL!;

// Cache pool across hot reloads in development
const globalForDb = globalThis as unknown as {
  conn: postgres.Sql | undefined;
};

const conn = globalForDb.conn ?? postgres(connectionString, { max: 15 });
if (process.env.NODE_ENV !== 'production') globalForDb.conn = conn;

export const db = drizzle(conn, { schema });
```

---

## 3. Server Action with Optimistic Response Protocol

```tsx
// src/app/actions/todos.ts
'use server';

import { z } from 'zod';
import { db } from '@/db';
import { todos } from '@/db/schema';
import { revalidatePath } from 'next/cache';

const CreateTodoSchema = z.object({
  title: z.string().min(2).max(100),
});

export async function createTodoAction(prevState: any, formData: FormData) {
  const result = CreateTodoSchema.safeParse({
    title: formData.get('title'),
  });

  if (!result.success) {
    return { error: result.error.flatten().fieldErrors };
  }

  await db.insert(todos).values({
    title: result.data.title,
    completed: false,
  });

  revalidatePath('/todos');
  return { success: true };
}
```
