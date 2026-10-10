# Containers & Orchestration: Multi-Stage Production Builds and K3s (2026)

> Technical reference for containerizing modern web stacks (Laravel, React/Next.js, Go) and minimal orchestration with K3s.

---

## 1. Multi-Stage Production Containerization

Multi-stage Docker builds isolate build-time SDKs and compilers from the final execution image, shrinking image footprints by up to 90% and eliminating security vulnerabilities.

### 1.1 Next.js 15/16 Production Multi-Stage Build
```dockerfile
# Stage 1: Dependency resolution
FROM node:22-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

# Stage 2: Next.js build
FROM node:22-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

# Stage 3: Minimal runner (Standalone output)
FROM node:22-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
RUN addgroup --system --gid 1001 nodejs && adduser --system --uid 1001 nextjs
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static
USER nextjs
EXPOSE 3000
CMD ["node", "server.js"]
```

### 1.2 Go Scratch / Alpine Minimal Container (Under 20 MB)
```dockerfile
FROM golang:1.23-alpine AS builder
WORKDIR /src
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-w -s" -o /bin/api ./cmd/api

FROM gcr.io/distroless/static-debian12
COPY --from=builder /bin/api /bin/api
USER 65534:65534
ENTRYPOINT ["/bin/api"]
```

---

## 2. K3s: Lightweight Kubernetes for Production VPS

K3s bundles Kubernetes into a single binary (<100 MB), replacing etcd with SQLite for single-node deployments or embedded etcd for high-availability clusters.
- Low memory footprint (~512 MB RAM consumption).
- Built-in Traefik ingress controller, Flannel CNI, and Local Storage Provider.
