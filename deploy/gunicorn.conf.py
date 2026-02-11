"""Gunicorn configuration for production deployment."""

import multiprocessing
import os

# Bind to a Unix socket for Nginx reverse-proxy setup.
bind = os.getenv("GUNICORN_BIND", "unix:/run/marketplace/gunicorn.sock")

# Workers: (2 * CPU cores) + 1 is a common recommendation.
workers = int(os.getenv("GUNICORN_WORKERS", multiprocessing.cpu_count() * 2 + 1))

# Timeout (seconds). Increase if you have long-running requests.
timeout = int(os.getenv("GUNICORN_TIMEOUT", "30"))

# Logging
accesslog = os.getenv("GUNICORN_ACCESS_LOG", "/var/log/marketplace/gunicorn-access.log")
errorlog = os.getenv("GUNICORN_ERROR_LOG", "/var/log/marketplace/gunicorn-error.log")
loglevel = os.getenv("GUNICORN_LOG_LEVEL", "info")

# Reload workers when code changes (disable in production).
reload = os.getenv("GUNICORN_RELOAD", "false").lower() == "true"

# Security: limit request sizes.
limit_request_line = 8190
limit_request_fields = 100
limit_request_field_size = 8190

# Graceful restart timeout.
graceful_timeout = 30

# Working directory.
chdir = os.getenv("APP_DIR", "/opt/marketplace/marketplace")

# Django WSGI application.
wsgi_app = "marketplace.wsgi:application"
