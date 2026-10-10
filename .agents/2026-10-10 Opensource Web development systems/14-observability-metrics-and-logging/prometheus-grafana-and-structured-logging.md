# Prometheus Metrics & Structured Logging (RED Method) (2026)

> Technical reference for application metrics collection, latency histograms, and correlation-aware structured JSON logging.

---

## 1. The RED Method for Web Services

Every production web service must track three golden signals:
- **Rate:** Number of HTTP requests per second (`http_requests_total`).
- **Errors:** Number of failed requests per second (`http_requests_errors_total` with HTTP 5xx codes).
- **Duration:** Latency distribution of requests (`http_request_duration_seconds` histogram).

### Prometheus Histogram Bucket Guidelines
```python
# Prometheus latency histogram in Python
from prometheus_client import Histogram

REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency in seconds',
    ['method', 'endpoint', 'status_code'],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0]
)
```

---

## 2. Structured JSON Logging with Trace Correlation

Plain text logs are impossible to query at scale. Modern services emit machine-readable newline-delimited JSON with automatic trace correlation:

### Go `log/slog` JSON Logger with TraceID
```go
package logging

import (
    "context"
    "log/slog"
    "os"
    "go.opentelemetry.io/otel/trace"
)

var Logger = slog.New(slog.NewJSONHandler(os.Stdout, &slog.HandlerOptions{Level: slog.LevelInfo}))

func LogWithTrace(ctx context.Context, level slog.Level, msg string, args ...any) {
    span := trace.SpanFromContext(ctx)
    if span.SpanContext().IsValid() {
        args = append(args,
            "trace_id", span.SpanContext().TraceID().String(),
            "span_id", span.SpanContext().SpanID().String(),
        )
    }
    Logger.Log(ctx, level, msg, args...)
}
```

Emitted log entry:
```json
{
  "time": "2026-10-10T15:10:00.124Z",
  "level": "INFO",
  "msg": "Order processed successfully",
  "order_id": "ord_9182",
  "amount": 49.99,
  "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
  "span_id": "00f067aa0ba902b7"
}
```
