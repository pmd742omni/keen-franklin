# Coolify Self-Hosted PaaS Automation & Architecture

> Technical reference for deploying and managing production applications, databases, and services with Coolify.

---

## 1. Coolify Architecture

Coolify operates as a centralized control plane orchestrating one or multiple destination Docker hosts over SSH:
- **Build Engine (Nixpacks & Docker):** Auto-detects runtime languages (Laravel, Node.js, Python, Go, Rust) and produces optimized container images without manual Dockerfiles.
- **Routing & SSL (Traefik Engine):** Automatically provisions Let's Encrypt certificates and manages blue/green zero-downtime rolling deploys.
- **Persistent Databases:** 1-click provisioning of PostgreSQL (with pgvector), MySQL, MariaDB, Valkey, and MongoDB with automated backup schedules.

---

## 2. Programmatic Deployments via Coolify API

Triggering builds via CI/CD pipelines (GitHub Actions, GitLab CI):

```bash
# Trigger automated deployment using Coolify Webhook Token
curl -X GET "https://coolify.myinfra.com/api/v1/deploy?uuid=app-uuid-12345" \
     -H "Authorization: Bearer ${COOLIFY_API_TOKEN}"
```

```yaml
# .github/workflows/deploy.yml
name: Trigger Self-Hosted Deploy
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Trigger Coolify Webhook
        run: |
          curl -sf -X GET "${{ secrets.COOLIFY_DEPLOY_WEBHOOK_URL }}"
```
