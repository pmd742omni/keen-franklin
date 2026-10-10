---
name: modern-react-stack
description: "Mastery of modern React 19+, Server Components (RSC), Next.js App Router, Vite SPAs, TanStack Query v5, Zustand, Tailwind CSS v4, and shadcn/ui."
risk: none
source: workspace
date_added: "2026-10-10"
---

# Modern React Stack

> Autonomous architectural and engineering guide for building high-velocity, high-performance web systems using React 19, Server Components, Next.js, and modern state primitives.

## 🎯 Selective Reading Rule

**Read ONLY files relevant to the request!** Check the content map, find what you need.

---

## 📑 Content Map

| File | Description | When to Read |
|---|---|---|
| `references/react-19-server-components.md` | RSC streaming, Server Actions, `useActionState`, `use()` | Building Next.js / RSC server-rendered apps |
| `references/tanstack-and-zustand.md` | Server cache synchronization & lightweight global UI state | Designing client-side state layers and API queries |
| `references/tailwind-v4-and-shadcn.md` | Tailwind v4 Oxide engine, accessible Radix UI components | Implementing UI components, design tokens, styling |

---

## 🔗 Related Skills

| Need | Skill |
|---|---|
| Frontend design polish & deslop | `@[skills/baseline-ui]` |
| Design token system | `@[skills/design-system]` |
| API integration & RPC | `@[skills/api-patterns]` |
| Open source architecture | `@[skills/fullstack-open-source-architect]` |

---

## ✅ Decision Checklist

Before building React components:

- [ ] **Determined execution boundary?** (Server Component by default; add `'use client'` only when using hooks, browser APIs, or event listeners).
- [ ] **Separated Server State from Client State?**
  - Remote API data belongs in TanStack Query or Server Components.
  - Global UI state (modals, drawers) belongs in Zustand.
  - Form local transient inputs belong in standard controlled/uncontrolled state.
- [ ] **Handled loading states via `<Suspense>` boundaries?**
- [ ] **Prevented network request waterfalls?** Used `Promise.all()` for independent asynchronous calls.
- [ ] **Secured server mutations?** Validated all `FormData` inputs with Zod schemas inside Server Actions.

---

## ❌ Anti-Patterns

**DON'T:**
- Use `useEffect` for data fetching in React 19 (use Server Components, `use()`, or TanStack Query).
- Scatter `'use client'` at the root layout or top-level page components (pushes unnecessary JS bundle to client).
- Store server-fetched data in Redux or global client stores without cache invalidation mechanisms.
- Chain serial asynchronous `await` calls in Server Components when data fetching can run in parallel.

**DO:**
- Keep `'use client'` components at the leaves of the component tree.
- Use `useOptimistic` for instant user feedback on mutations.
- Leverage shadcn/ui copy-paste ownership model for full accessibility and DOM customization.
- Enforce strict TypeScript typing on all component props and Action responses.
