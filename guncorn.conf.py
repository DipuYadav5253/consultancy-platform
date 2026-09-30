"""Gunicorn settings. Everything can be tuned with environment variables."""

import os

bind = f"0.0.0.0:{os.environ.get('PORT', '8000')}"
worker_class = "gthread"
workers = int(os.environ.get("WEB_CONCURRENCY", "3"))
threads = int(os.environ.get("GUNICORN_THREADS", "4"))
timeout = 30
graceful_timeout = 30
keepalive = 5
max_requests = 1000  # restart workers regularly to contain memory leaks
max_requests_jitter = 100
worker_tmp_dir = "/dev/shm"  # noqa: S108  (in-memory heartbeat files; the standard Docker setting)
accesslog = "-"
errorlog = "-"
# The container must only be reachable through the load balancer (never publish its port
# to the internet), so it can trust the proxy headers.
forwarded_allow_ips = os.environ.get("FORWARDED_ALLOW_IPS", "*")
