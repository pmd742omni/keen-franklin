# Chi Routing, Middleware & Server Hardening in Go

> Technical reference for building robust HTTP routing hierarchies, custom middleware chains, and hardened server configurations in Go.

---

## 1. Hardened Production HTTP Server

Default `http.ListenAndServe()` instances are vulnerable to resource exhaustion. Always define strict operational timeouts:

```go
package main

import (
    "context"
    "log/slog"
    "net/http"
    "os"
    "os/signal"
    "syscall"
    "time"

    "github.com/go-chi/chi/v5"
)

func main() {
    router := chi.NewRouter()
    // Setup routes...

    server := &http.Server{
        Addr:         ":8080",
        Handler:      router,
        ReadTimeout:  5 * time.Second,   // Max time to read request headers & body
        WriteTimeout: 10 * time.Second,  // Max time to write response
        IdleTimeout:  120 * time.Second, // Keep-alive connection idle duration
    }

    go func() {
        if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
            slog.Error("server listen failure", "error", err)
            os.Exit(1)
        }
    }()

    // Graceful Shutdown
    quit := make(chan os.Signal, 1)
    signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
    <-quit

    slog.Info("shutting down server gracefully...")
    ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
    defer cancel()

    if err := server.Shutdown(ctx); err != nil {
        slog.Error("server forced to shutdown", "error", err)
    }
    slog.Info("server exited cleanly")
}
```

---

## 2. Idiomatic Middleware Construction

```go
func RequireRole(requiredRole string) func(http.Handler) http.Handler {
    return func(next http.Handler) http.Handler {
        return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
            user, ok := r.Context().Value(userContextKey).(User)
            if !ok || user.Role != requiredRole {
                http.Error(w, `{"error": "forbidden"}`, http.StatusForbidden)
                return
            }
            next.ServeHTTP(w, r)
        })
    }
}
```
