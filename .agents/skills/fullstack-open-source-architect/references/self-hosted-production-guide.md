# Self-Hosted Open-Source Production Infrastructure Guide

> Production operational guide for running resilient, zero-lock-in web systems using Coolify, Kamal 2, Docker, PostgreSQL 17, and Valkey on bare-metal or cloud VPS.

---

## 1. High-Availability Single-Server VPS Architecture (Under $20/Month)

A modern Hetzner Cloud (CX32: 4 vCPU, 8 GB RAM, NVMe) or DigitalOcean droplet can comfortably serve millions of monthly visits with this topology:

```mermaid
graph TD
    Internet[Public Traffic HTTP/3] --> Traefik[Traefik / Caddy Reverse Proxy (Auto SSL)]
    Traefik --> WebApp[App Container (Laravel Octane / Next.js / Go)]
    WebApp --> Valkey[Valkey Container (Cache & Rate Limiting)]
    WebApp --> Postgres[PostgreSQL 17 Container]
    Postgres --> VectorExtension[pgvector AI Index]
    Postgres -.->|Nightly Encrypted Backup| OffsiteS3[(MinIO / Cloudflare R2 / S3)]
```

---

## 2. Docker Compose Production Template

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  web:
    image: ghcr.io/myorg/myapp:latest
    restart: unless-stopped
    environment:
      - DATABASE_URL=postgres://appuser:${DB_PASSWORD}@postgres:5432/appdb
      - REDIS_URL=redis://valkey:6379
      - NODE_ENV=production
    depends_on:
      postgres:
        condition: service_healthy
      valkey:
        condition: service_started
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.app.rule=Host(`app.example.com`)"
      - "traefik.http.routers.app.entrypoints=websecure"
      - "traefik.http.routers.app.tls.certresolver=letsencrypt"

  postgres:
    image: pgvector/pgvector:pg17
    restart: unless-stopped
    environment:
      POSTGRES_DB: appdb
      POSTGRES_USER: appuser
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U appuser -d appdb"]
      interval: 5s
      timeout: 5s
      retries: 5

  valkey:
    image: valkey/valkey:8-alpine
    restart: unless-stopped
    command: valkey-server --maxmemory 512mb --maxmemory-policy allkeys-lru
    volumes:
      - valkeydata:/data

volumes:
  pgdata:
  valkeydata:
```

---

## 3. Automated Automated Database Offsite Backup
Use a lightweight cron container executing `pg_dump` piped through gzip directly to Cloudflare R2 / AWS S3:

```bash
# Automated backup command
pg_dump -h postgres -U appuser appdb | gzip | aws s3 cp - s3://backups-bucket/db-$(date +%Y%m%d%H%M%S).sql.gz --endpoint-url https://<account_id>.r2.cloudflarestorage.com
```
