---
name: self-hosted-devops-and-coolify
description: "Mastery of self-hosted cloud infrastructure, Coolify PaaS automation, Docker multi-stage builds, reverse proxy management (Traefik/Caddy), PostgreSQL high availability, and VPS security hardening."
risk: none
source: workspace
date_added: "2026-10-10"
---

# Self-Hosted DevOps & Coolify

> Autonomous engineering guide for provisioning, securing, and operating production web applications and databases on self-hosted cloud VPS and bare-metal environments with zero vendor lock-in.

## 🎯 Selective Reading Rule

**Read ONLY files relevant to the request!** Check the content map, find what you need.

---

## 📑 Content Map

| File | Description | When to Read |
|---|---|---|
| `references/coolify-automation.md` | Coolify API, Nixpacks, multi-server topology, Git webhooks | Automating deployments with Coolify PaaS |
| `references/vps-hardening-and-security.md` | UFW firewall, fail2ban, SSH key rotation, non-root user setup | Hardening a fresh Debian/Ubuntu Linux VPS |
| `references/postgres-backup-and-restore.md` | Automated pg_dump, WAL-G point-in-time recovery, offsite S3 sync | Securing and testing database backup integrity |

---

## 🔗 Related Skills

| Need | Skill |
|---|---|
| Fullstack system architecture | `@[skills/fullstack-open-source-architect]` |
| Database design & indexes | `@[skills/database-design]` |
| Laptop & local dev tuning | `@[skills/laptop-optimizer]` |

---

## ✅ Decision Checklist

Before deploying self-hosted web applications:

- [ ] **Configured automated offsite database backups?** (Local backups are useless if the physical VPS drive corrupts; stream to Cloudflare R2 / AWS S3).
- [ ] **Disabled SSH password authentication and root login?** (`PasswordAuthentication no`, `PermitRootLogin no`).
- [ ] **Configured UFW firewall?** (Allow strictly ports 22, 80, 443; keep internal databases bound to private Docker networks).
- [ ] **Defined container resource constraints?** (`mem_limit`, `cpus` in Docker Compose to prevent runaway processes from freezing the host OS).
- [ ] **Set up automated Let's Encrypt TLS certificate renewal?**
