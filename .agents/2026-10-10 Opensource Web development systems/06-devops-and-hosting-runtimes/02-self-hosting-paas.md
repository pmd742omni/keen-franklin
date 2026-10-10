# Self-Hosted PaaS: Coolify, Dokku, and Kamal 2 (2026)

> Technical reference for self-hosted Platform-as-a-Service alternatives to Vercel, Netlify, and Heroku.

---

## 1. Coolify: The Open Source Vercel/Heroku Alternative

**Coolify** has emerged as the premier open-source self-hosted PaaS:
- **Server Agnostic:** Runs on any Ubuntu/Debian VPS (Hetzner €4/month instances to bare-metal clusters).
- **Automated Git Deployments:** Push-to-deploy triggers via GitHub/GitLab webhooks with PR preview environments.
- **Integrated Databases with 1-Click Provisioning:** PostgreSQL, Valkey, MySQL, MongoDB, MariaDB with automated automated offsite S3 backups.
- **Reverse Proxy & Let's Encrypt:** Automated SSL certificate generation and renewal via Traefik.

---

## 2. Dokku & Kamal 2

- **Dokku:** Uses Docker and Heroku-compatible buildpacks for small single-node VPS environments.
- **Kamal 2:** Manages multi-server Docker deployments over SSH with zero downtime, automated health-checks, and minimal server footprint.
