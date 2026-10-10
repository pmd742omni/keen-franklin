# Bounded Goroutine Worker Pools & Channel Backpressure in Go

> Technical reference for managing background tasks, preventing memory leaks, and applying backpressure in high-concurrency Go systems.

---

## 1. The Danger of Unbounded Goroutines

```go
// ❌ Dangerous: Under an HTTP DDoS or traffic spike, 100,000 goroutines spawn simultaneously,
// each attempting network/disk access, exhausting OS file descriptors and killing the process.
func handleWebhook(w http.ResponseWriter, r *http.Request) {
    go processWebhookAsync(r.Body) 
}
```

---

## 2. Bounded Worker Pool with Buffered Channels

```go
package worker

import (
    "context"
    "errors"
    "sync"
)

var ErrQueueFull = errors.New("worker queue is at full capacity")

type Dispatcher struct {
    jobQueue chan func(ctx context.Context)
    wg       sync.WaitGroup
}

func NewDispatcher(workerCount int, queueCapacity int) *Dispatcher {
    d := &Dispatcher{
        jobQueue: make(chan func(ctx context.Context), queueCapacity),
    }

    for i := 0; i < workerCount; i++ {
        d.wg.Add(1)
        go d.worker()
    }

    return d
}

func (d *Dispatcher) worker() {
    defer d.wg.Done()
    for task := range d.jobQueue {
        ctx := context.Background()
        task(ctx)
    }
}

// TrySubmit submits a task or returns an immediate error if queue capacity is exceeded
func (d *Dispatcher) TrySubmit(task func(ctx context.Context)) error {
    select {
    case d.jobQueue <- task:
        return nil
    default:
        return ErrQueueFull // Protects memory and allows caller to return HTTP 429
    }
}

func (d *Dispatcher) Shutdown() {
    close(d.jobQueue)
    d.wg.Wait()
}
```
