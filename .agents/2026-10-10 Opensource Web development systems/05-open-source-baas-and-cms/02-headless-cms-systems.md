# Open Source Headless CMS: Payload 3.0, Strapi 5, and Directus (2026)

> Technical reference for modern open-source content management systems and code-first content modeling.

---

## 1. Architectural Evolution: Payload CMS 3.0

Payload 3.0 redefined the headless CMS category by embedding natively directly inside Next.js applications:
- **No Separate CMS Server:** The admin UI and CMS API run inside your Next.js `app/` directory as standard React Server Components.
- **Code-As-Configuration:** Collections and fields are declared in pure TypeScript files tracked in Git.
- **Database Engine Freedom:** Supports PostgreSQL, SQLite, and MongoDB via modular Drizzle ORM and native adapters.

```ts
// payload.config.ts
import { buildConfig } from 'payload';
import { postgresAdapter } from '@payloadcms/db-postgres';
import { lexicalEditor } from '@payloadcms/richtext-lexical';

export default buildConfig({
  admin: {
    user: 'users',
  },
  collections: [
    {
      slug: 'posts',
      fields: [
        { name: 'title', type: 'text', required: true },
        { name: 'slug', type: 'text', unique: true, index: true },
        { name: 'content', type: 'richText', editor: lexicalEditor({}) },
      ],
    },
  ],
  db: postgresAdapter({
    pool: { connectionString: process.env.DATABASE_URI },
  }),
});
```

---

## 2. Strapi 5 & Directus Comparison

- **Strapi 5:** Provides a dedicated Node.js standalone server with rich draft-and-publish workflows, internationalization, and an extensive community marketplace.
- **Directus:** Acts as an instant wrapper on top of any existing, pre-populated SQL database (PostgreSQL, MySQL, Oracle, MS SQL), generating instant REST and GraphQL APIs and a dynamic back-office interface without altering existing schemas.
