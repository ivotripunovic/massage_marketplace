---
name: observability
description: Check or debug production errors and logs — Sentry error tracking and structured JSON logging via systemd journal. Use when checking logs, debugging a production error, or asked about Sentry or journalctl.
---

## Error Tracking — Sentry

Integrated via `sentry-sdk[django]`. Initialized in `settings.py` when `SENTRY_DSN` env var is set; no-op when blank (safe for local dev and CI).

Env vars:
- `SENTRY_DSN` — from Sentry project settings (leave blank to disable)
- `SENTRY_ENVIRONMENT` — `production` / `staging` (default: `production`)
- `SENTRY_TRACES_SAMPLE_RATE` — fraction of requests traced for performance (default: `0.1`)

## Structured Logging

`python-json-logger` formats log output as JSON in production (`DEBUG=False`) and human-readable text in development. Logs go to stdout and are collected by systemd journal.

Log levels by logger:
- `django.request` — ERROR (500s with tracebacks)
- `django.security` — WARNING (CSRF failures, suspicious requests)
- `payments`, `providers`, `users` — INFO in production, DEBUG locally

Useful `journalctl` commands:
```bash
journalctl -u your-app -f                               # stream live
journalctl -u your-app --since "1 hour ago"             # last hour
journalctl -u your-app | grep '"levelname": "ERROR"'    # errors only (JSON)
```
