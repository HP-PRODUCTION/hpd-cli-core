"""Prometheus metrics for HPD Control Plane API."""
import time
from prometheus_client import Counter, Histogram, Gauge, generate_latest, REGISTRY
from starlette.requests import Request
from starlette.responses import Response

# --- Métricas ---

HTTP_REQUESTS_TOTAL = Counter(
    "hpd_http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)

HTTP_REQUEST_DURATION = Histogram(
    "hpd_http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0),
)

HEALTH_CHECKS_TOTAL = Counter(
    "hpd_health_checks_total",
    "Total health check requests",
)

ACTIVE_REQUESTS = Gauge(
    "hpd_active_requests",
    "Currently active requests",
)


async def prometheus_metrics(request: Request, call_next):
    """ASGI middleware that collects Prometheus metrics for each request."""
    method = request.method
    path = request.url.path

    ACTIVE_REQUESTS.inc()
    start = time.time()
    status = 500

    try:
        response = await call_next(request)
        status = response.status_code
        return response
    finally:
        duration = time.time() - start
        HTTP_REQUESTS_TOTAL.labels(method=method, endpoint=path, status=status).inc()
        HTTP_REQUEST_DURATION.labels(method=method, endpoint=path).observe(duration)
        if path == "/api/system/health":
            HEALTH_CHECKS_TOTAL.inc()
        ACTIVE_REQUESTS.dec()


async def metrics_endpoint(request: Request):
    """Expose Prometheus metrics at /metrics."""
    return Response(
        content=generate_latest(REGISTRY),
        media_type="text/plain; charset=utf-8",
        headers={"Cache-Control": "no-cache"},
    )
