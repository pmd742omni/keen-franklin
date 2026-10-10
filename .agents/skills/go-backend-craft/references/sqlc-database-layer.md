# Compile-Time SQL in Go with sqlc and pgxpool

> Technical reference for high-throughput, type-safe database programming with sqlc and JackC's pgx/v5 driver.

---

## 1. sqlc Configuration & Query Architecture

```yaml
# sqlc.yaml
version: "2"
sql:
  - schema: "db/migrations"
    queries: "db/queries"
    gen:
      go:
        package: "db"
        out: "internal/db"
        sql_package: "pgx/v5"
        emit_json_tags: true
        emit_pointers_for_null_types: true
```

### Writing Queries
```sql
-- db/queries/accounts.sql
-- name: GetAccountForUpdate :one
SELECT id, balance, currency, updated_at
FROM accounts
WHERE id = $1
FOR UPDATE;

-- name: UpdateBalance :exec
UPDATE accounts
SET balance = balance + $2, updated_at = NOW()
WHERE id = $1;
```

---

## 2. Executing Atomic Transactions with pgxpool

```go
package service

import (
    "context"
    "fmt"
    "github.com/jackc/pgx/v5/pgxpool"
    "myproject/internal/db"
)

type AccountService struct {
    pool    *pgxpool.Pool
    queries *db.Queries
}

func (s *AccountService) TransferFunds(ctx context.Context, fromID, toID int64, amount int64) error {
    tx, err := s.pool.Begin(ctx)
    if err != nil {
        return fmt.Errorf("failed to begin tx: %w", err)
    }
    defer tx.Rollback(ctx)

    qtx := s.queries.WithTx(tx)

    // Check sender balance with lock
    fromAcc, err := qtx.GetAccountForUpdate(ctx, fromID)
    if err != nil {
        return fmt.Errorf("sender account not found: %w", err)
    }
    if fromAcc.Balance < amount {
        return fmt.Errorf("insufficient funds")
    }

    // Debit sender
    if err := qtx.UpdateBalance(ctx, db.UpdateBalanceParams{ID: fromID, Balance: -amount}); err != nil {
        return err
    }

    // Credit recipient
    if err := qtx.UpdateBalance(ctx, db.UpdateBalanceParams{ID: toID, Balance: amount}); err != nil {
        return err
    }

    return tx.Commit(ctx)
}
```
