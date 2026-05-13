import time

from fastapi import Request
from prometheus_client import Counter, Histogram
from starlette.middleware.base import BaseHTTPMiddleware

from app.utils.logger import error_logger, request_logger

REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status_code"],
)

REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "path"],
)


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        path = request.url.path

        request_logger.info(f"Request: {request.method} {path}")

        try:
            response = await call_next(request)
            process_time = time.time() - start_time

            REQUEST_COUNT.labels(request.method, path, str(response.status_code)).inc()
            REQUEST_LATENCY.labels(request.method, path).observe(process_time)

            request_logger.info(
                f"Response: {request.method} {path} - "
                f"Status: {response.status_code} - "
                f"Time: {process_time:.3f}s"
            )

            response.headers["X-Process-Time"] = str(process_time)
            return response
        except Exception as exc:
            process_time = time.time() - start_time
            REQUEST_COUNT.labels(request.method, path, "500").inc()
            REQUEST_LATENCY.labels(request.method, path).observe(process_time)
            error_logger.exception(f"Error processing {request.method} {path}: {exc}")
            raise
