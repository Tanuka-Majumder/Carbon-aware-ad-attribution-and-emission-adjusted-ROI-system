from prometheus_client import Counter, Histogram

REQS = Counter("http_requests_total", "Total HTTP requests", ["route", "method", "status"])
LAT = Histogram("http_request_latency_seconds", "Request latency", ["route"])