# Open-Source Agent Skills Ecosystem & Workspace Evolution Guide (2026)

> Technical guide to discovering, auditing, downloading, and installing open-source agent skills from GitHub repositories into workspace agents.

---

## 1. The Open Agent Skill Standard (`SKILL.md`)

Agent Skills represent a vendor-neutral, modular standard for packaging domain instructions, golden code patterns, tool definitions, and executable helper scripts:

- **Progressive Disclosure Architecture:** To avoid depleting LLM context windows, agents only load the skill's metadata (`name`, `description`) at startup. The body instructions and reference documents are dynamically paged into the context window strictly when a task matches the skill's domain.
- **Portability:** A single `SKILL.md` folder structure is compatible across Claude Code, GitHub Copilot, Gemini CLI, Cursor, and custom agentic frameworks.

### Standard Skill Directory Layout
```text
.agents/skills/<skill-name>/
├── SKILL.md             # Required: YAML frontmatter + core procedures & decision trees
├── references/          # Optional: Deep architectural guides, cheatsheets, examples
├── scripts/             # Optional: Black-box helper scripts (Python, Node, Bash)
└── templates/           # Optional: Starter boilerplates & configuration schemas
```

---

## 2. Major Open-Source GitHub Skill Repositories

| Repository | Maintainer | Key Domains | Recommended Skills |
|---|---|---|---|
| **`anthropics/skills`** | Anthropic | Testing, MCP, design, enterprise docs | `webapp-testing`, `mcp-builder`, `skill-creator` |
| **`vercel-labs/agent-skills`** | Vercel | React, Next.js, performance, UI/UX | `react-best-practices`, `composition-patterns`, `web-design-guidelines` |
| **`VoltAgent/awesome-agent-skills`** | VoltAgent / Community | 1,000+ curated developer workflows | Full-stack coding, DevOps, memory architectures |

---

## 3. Installed Skills in this Workspace

The workspace `.agents/skills/` directory is now populated with an integrated suite of custom-authored and curated open-source skills:

### Curated Open-Source Skills (from GitHub)
1. **`@[skills/webapp-testing]`** (Anthropic): End-to-end browser testing with Playwright, server lifecycle management (`scripts/with_server.py`), and DOM regression testing.
2. **`@[skills/mcp-builder]`** (Anthropic): Designing, implementing, and debugging Model Context Protocol (MCP) servers in TypeScript (MCP SDK) and Python (FastMCP).
3. **`@[skills/skill-creator]`** (Anthropic): Procedural guidelines for creating high-agency, context-efficient agent skills with progressive disclosure.
4. **`@[skills/vercel-react-best-practices]`** (Vercel): 70 rules across 8 categories for eliminating waterfalls, bundle bloat, and server-side bottlenecks in React and Next.js.
5. **`@[skills/composition-patterns]`** (Vercel): Component composition, compound components, render props, and accessible headless UI patterns.

### Custom Deep-Architected Skills (Developed in Session)
6. **`@[skills/laravel-expert]`**: Modern Laravel 11/12, Inertia.js v2, Livewire 3, Filament v3, Eloquent optimization, and FrankenPHP Octane.
7. **`@[skills/modern-react-stack]`**: React 19 RSC, Server Actions, TanStack Query v5, Zustand, Tailwind CSS v4, and shadcn/ui.
8. **`@[skills/fullstack-open-source-architect]`**: Technology selection matrices, Coolify/Kamal deployment, PostgreSQL 17 + `pgvector`, and Valkey caching.
9. **`@[skills/python-web-engineer]`**: FastAPI, Pydantic v2, Django 5+ async ORM, Django Ninja, async SQLAlchemy 2.0, and Alembic.
10. **`@[skills/go-backend-craft]`**: Go 1.23+ web services, Chi router, stdlib path routing, compile-time `sqlc`, and bounded goroutine worker pools.
11. **`@[skills/self-hosted-devops-and-coolify]`**: Coolify PaaS automation, Docker multi-stage builds, reverse proxies, and automated offsite S3 backups.

---

## 4. How to Install Additional Skills from GitHub

To pull new skills into `.agents/skills` programmatically:

```bash
# 1. Clone target skill repository into temporary directory
git clone --depth 1 https://github.com/<owner>/<repo>.git /tmp/skills-source

# 2. Copy selected skill folder into .agents/skills
cp -r /tmp/skills-source/skills/<target-skill> .agents/skills/<target-skill>

# 3. Clean up temporary source
rm -rf /tmp/skills-source
```
