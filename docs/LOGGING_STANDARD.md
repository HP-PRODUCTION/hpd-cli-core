# HPD Logging Standard v1

This standard defines the minimum structured logging contract across HPD projects.

## Required fields

- timestamp: ISO-8601 in UTC, example `2026-05-08T12:34:56.123Z`
- level: `DEBUG|INFO|WARNING|ERROR|CRITICAL`
- logger: logger name
- message: human-readable message
- app: project or service name
- environment: runtime environment, example `development|staging|production`

## Traceability fields

- trace_id: request or operation correlation id
- run_id: cycle or batch execution id
- component: source component, example `api|worker|batch|webhook`

## Optional fields

- event: short event key, example `webhook_received`
- details: object with contextual data
- exception: formatted exception traceback when available

## Rules

1. Logs must be JSON lines for machine parsing.
2. Avoid logging secrets, tokens, passwords, and private keys.
3. Include `trace_id` in request handlers and `run_id` in workers/batches.
4. Keep messages concise and put additional data in `details`.
5. Console and file outputs must use the same JSON payload shape.

## Minimal payload example

```json
{
  "timestamp": "2026-05-08T12:34:56.123Z",
  "level": "INFO",
  "logger": "plataforma_deportiva",
  "message": "Webhook received",
  "app": "plataforma_deportiva",
  "environment": "production",
  "trace_id": "9f4a2f90d75f4f8a",
  "run_id": "",
  "component": "webhook",
  "event": "paypal_webhook_received",
  "details": {
    "order_id": "5JU...",
    "event_type": "CHECKOUT.ORDER.APPROVED"
  }
}
```
