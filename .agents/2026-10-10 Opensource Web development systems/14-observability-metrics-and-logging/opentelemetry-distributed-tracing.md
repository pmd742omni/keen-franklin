# OpenTelemetry (OTel) Distributed Tracing Architecture (2026)

> Technical reference for instrumenting open-source web applications with OpenTelemetry for distributed trace propagation and span management.

---

## 1. W3C Trace Context Propagation

In modern distributed microservices and decoupled web applications, incoming HTTP requests carry W3C Trace Context headers across boundaries (`traceparent`, `tracestate`):

```text
traceparent: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01
              │  └───────────────┬────────────────┘ └───────┬──────┘ └─ flags
              version         trace-id                   parent-span-id
```

This guarantees that a user interaction in Next.js, forwarded to a Go API, and dispatched to a background Celery worker shares a single continuous trace timeline.

---

## 2. Automatic & Manual Instrumentation in Node.js / Next.js

```ts
// instrumentation.node.ts
import { NodeSDK } from '@opentelemetry/sdk-node';
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-http';
import { getNodeAutoInstrumentations } from '@opentelemetry/auto-instrumentations-node';

const sdk = new NodeSDK({
  traceExporter: new OTLPTraceExporter({
    url: process.env.OTEL_EXPORTER_OTLP_ENDPOINT || 'http://collector:4318/v1/traces',
  }),
  instrumentations: [getNodeAutoInstrumentations()],
});

sdk.start();
```

---

## 3. High-Performance Tracing in Go with Context Spans

```go
package telemetry

import (
    "context"
    "go.opentelemetry.io/otel"
    "go.opentelemetry.io/otel/attribute"
    "go.opentelemetry.io/otel/trace"
)

var tracer = otel.Tracer("order-service")

func ProcessOrderWithTrace(ctx context.Context, orderID string, amount float64) error {
    ctx, span := tracer.Start(ctx, "ProcessOrderWithTrace",
        trace.WithAttributes(
            attribute.String("order.id", orderID),
            attribute.Float64("order.amount", amount),
        ),
    )
    defer span.End()

    // Downstream calls inherit ctx and span
    return nil
}
```
