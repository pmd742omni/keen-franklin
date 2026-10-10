# OWASP Top 10 Web Defense & Hardening Guide (2026)

> Concrete defense-in-depth implementations for open-source web frameworks (Laravel, React/Next.js, Python FastAPI, Go).

---

## 1. Broken Access Control (OWASP #1)

Access control must be enforced at the data layer, not merely by hiding UI links:

- **Laravel Gates & Policies:** Always invoke `$this->authorize('update', $post)` or route middleware `can:update,post`.
- **FastAPI Dependency Injection:** Enforce ownership checks inside path dependencies:
  ```python
  async def verify_org_member(org_id: UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
      is_member = await check_membership(db, current_user.id, org_id)
      if not is_member:
          raise HTTPException(status_code=403, detail="Forbidden: User not part of organization")
      return current_user
  ```
- **PostgreSQL Row Level Security (RLS):** Push policies directly into database tables (see `05-open-source-baas-and-cms/01-supabase-and-pocketbase.md`).

---

## 2. Injection Prevention (OWASP #3)

- **SQL Injection:** Never interpolate strings into raw SQL queries. Always use parameterized queries, ORM query builders (Eloquent, Drizzle, SQLAlchemy), or compile-time generators (`sqlc`).
- **Server-Side Request Forgery (SSRF):** When fetching external user-provided URLs (webhooks, avatar imports):
  - Resolve the hostname to an IP address.
  - Reject private/loopback CIDRs (`127.0.0.0/8`, `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `169.254.0.0/16`).
  - Disable HTTP redirect following or re-verify each target IP along the redirect chain.

---

## 3. Cryptographic Failures & Secure Storage (OWASP #2)

- **Password Hashing:** Use **Argon2id** (memory-hard, resistant to GPU attacks) or **bcrypt** with work factor $\ge 12$.
- **Session Tokens:** Store authentication session tokens hashed in the database (`SHA-256`) so database dumps do not reveal active session hijacking credentials.
- **Cookies:** Enforce `HttpOnly; Secure; SameSite=Lax` (or `Strict`).

---

## 4. Modern HTTP Security Headers Baseline

```http
Content-Security-Policy: default-src 'self'; script-src 'self' 'nonce-...'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; object-src 'none'; frame-ancestors 'none';
Strict-Transport-Security: max-age=63072000; includeSubDomains; preload
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: camera=(), microphone=(), geolocation=(), browsing-topics=()
```
