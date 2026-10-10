# High-Performance Web Servers & Proxies: FrankenPHP, Caddy, Nginx, and Traefik (2026)

> Technical reference for modern edge reverse proxies, automatic TLS, and next-generation application servers.

---

## 1. FrankenPHP: The Modern PHP Application Server

FrankenPHP embeds the PHP 8.3/8.4 runtime directly inside the Caddy web server (written in Go):
- **Worker Mode:** The application is booted once and held in memory across requests, transforming PHP execution into a persistent daemon.
- **HTTP/3 & 103 Early Hints:** Delivers assets and preloads resources while PHP workers execute database queries.
- **Automatic HTTPS:** Issues and auto-renews TLS certificates via Let's Encrypt / ZeroSSL without external certbot scripts.

```caddyfile
# Caddyfile for FrankenPHP
example.com {
    root * /app/public
    encode zstd gzip
    
    # Enable worker mode for maximum throughput
    php_server {
        worker /app/public/index.php 16
    }
}
```

---

## 2. Caddy vs Nginx in Modern Infrastructures

- **Caddy:** Default choice for modern cloud-native developers due to automatic HTTPS, native HTTP/3 support, and readable configuration files.
- **Nginx:** The enterprise battle-tested workhorse for high-concurrency static asset serving, custom Lua scripting (OpenResty), and legacy routing topologies.
