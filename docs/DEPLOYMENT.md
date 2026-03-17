# Production Deployment Guide

Target environment: **1GB RAM VPS** running multiple applications (Debian/Ubuntu).

---

## Prerequisites

- Python 3.11+
- PostgreSQL 14+
- Redis 6+
- Nginx
- Certbot (Let's Encrypt)

```bash
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3-pip \
    postgresql redis-server nginx certbot python3-certbot-nginx
```

---

## 1. Application Setup

```bash
git clone <repository-url> /srv/massage_marketplace
cd /srv/massage_marketplace

python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## 2. Environment Variables

```bash
cp .env.example .env
chmod 600 .env        # restrict read access
nano .env             # fill in all values
```

Required production values:

```dotenv
# Django
SECRET_KEY=<generate with: python -c "import secrets; print(secrets.token_urlsafe(50))">
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Database
DB_ENGINE=django.db.backends.postgresql
DB_NAME=massage_marketplace
DB_USER=massage_user
DB_PASSWORD=<strong-password>
DB_HOST=127.0.0.1
DB_PORT=5432

# Redis
REDIS_URL=redis://127.0.0.1:6379/1

# Email (SMTP)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.yourprovider.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=noreply@yourdomain.com
EMAIL_HOST_PASSWORD=<smtp-password>
DEFAULT_FROM_EMAIL=noreply@yourdomain.com

# Admin notifications
ADMIN_EMAILS=admin@yourdomain.com

# NOWPayments
NOW_PAYMENTS_API_KEY=<your-api-key>
NOW_PAYMENTS_IPN=<your-ipn-secret>
NOWPAYMENTS_SANDBOX=false

# Sentry (leave blank to disable)
SENTRY_DSN=https://...@sentry.io/...
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.1
```

---

## 3. Database Setup

```bash
sudo -u postgres psql <<'SQL'
CREATE USER massage_user WITH PASSWORD '<strong-password>';
CREATE DATABASE massage_marketplace OWNER massage_user;
SQL

source venv/bin/activate
python marketplace/manage.py migrate
python marketplace/manage.py createsuperuser
python marketplace/manage.py collectstatic --no-input
```

---

## 4. Redis

```bash
sudo systemctl enable --now redis-server
redis-cli ping   # → PONG
```

Redis is used for:
- Django cache (NOWPayments currency list, homepage data)
- Session storage (optional, falls back to DB)

---

## 5. Gunicorn (systemd service)

Create `/etc/systemd/system/massage_marketplace.service`:

```ini
[Unit]
Description=Massage Marketplace
After=network.target postgresql.service redis-server.service

[Service]
User=www-data
Group=www-data
WorkingDirectory=/srv/massage_marketplace/marketplace
Environment="PATH=/srv/massage_marketplace/venv/bin"
EnvironmentFile=/srv/massage_marketplace/.env
ExecStart=/srv/massage_marketplace/venv/bin/gunicorn \
    marketplace.wsgi \
    --workers 2 \
    --worker-class sync \
    --bind 127.0.0.1:8001 \
    --timeout 60 \
    --max-requests 1000 \
    --max-requests-jitter 50 \
    --log-level info
StandardOutput=journal
StandardError=journal
SyslogIdentifier=massage_marketplace
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

> **Worker count:** 2 workers on a 1GB VPS with multiple apps. Each gunicorn worker uses ~80-120MB.
> `--max-requests 1000` recycles workers to prevent memory leaks.

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now massage_marketplace
sudo systemctl status massage_marketplace
```

---

## 6. Nginx

Create `/etc/nginx/sites-available/massage_marketplace`:

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name yourdomain.com www.yourdomain.com;

    ssl_certificate     /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    ssl_protocols       TLSv1.2 TLSv1.3;
    ssl_ciphers         HIGH:!aNULL:!MD5;

    client_max_body_size 60M;

    # Static files — served directly by Nginx, never hits Django
    location /static/ {
        alias /srv/massage_marketplace/marketplace/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Media files — provider photos, gallery images
    location /media/ {
        alias /srv/massage_marketplace/marketplace/media/;
        expires 7d;
        add_header Cache-Control "public";
    }

    # Django application
    location / {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 60s;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/massage_marketplace /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## 7. SSL (Let's Encrypt)

```bash
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
# Certbot auto-renews via a systemd timer — verify with:
sudo systemctl status certbot.timer
```

---

## 8. File Permissions

```bash
# App files readable by www-data
sudo chown -R www-data:www-data /srv/massage_marketplace/marketplace/media
sudo chown -R www-data:www-data /srv/massage_marketplace/marketplace/staticfiles

# .env must not be world-readable
sudo chown root:www-data /srv/massage_marketplace/.env
sudo chmod 640 /srv/massage_marketplace/.env
```

---

## 9. Backups

### Database (daily, keep 7 days)

Create `/etc/cron.d/massage_marketplace_backup`:

```cron
0 3 * * * www-data pg_dump massage_marketplace | gzip > /srv/backups/db_$(date +\%Y\%m\%d).sql.gz && find /srv/backups -name "db_*.sql.gz" -mtime +7 -delete
```

```bash
sudo mkdir -p /srv/backups
sudo chown www-data: /srv/backups
```

### Media files

Media files (provider photos, gallery images) should be backed up off-server. Options:
- `rsync` to a second VPS or object storage (Hetzner Storage Box, Backblaze B2)
- Daily cron: `rsync -az /srv/massage_marketplace/marketplace/media/ user@backup-host:/backups/media/`

### Restore from backup

```bash
gunzip -c /srv/backups/db_20260317.sql.gz | sudo -u postgres psql massage_marketplace
```

---

## 10. Monitoring

### Uptime — UptimeRobot (free, cloud)

Add a monitor for `https://yourdomain.com` — alerts via email/Slack when site goes down.

### Errors — Sentry (free tier, cloud)

Set `SENTRY_DSN` in `.env`. Captures all unhandled exceptions with full stack traces and request context. No server resources used.

### Logs — systemd journal

All application output goes to the journal (configured via `StandardOutput=journal` in the service file).

```bash
# Stream live logs
journalctl -u massage_marketplace -f

# Last 100 lines
journalctl -u massage_marketplace -n 100

# Errors only
journalctl -u massage_marketplace -p err

# Filter by time
journalctl -u massage_marketplace --since "2026-03-17 00:00:00"

# Parse JSON errors (production format)
journalctl -u massage_marketplace | grep '"levelname": "ERROR"'
```

### Resource usage

```bash
# Memory breakdown
free -h
ps aux --sort=-%mem | head -10

# Disk
df -h /srv

# Nginx access logs
tail -f /var/log/nginx/access.log
```

---

## 11. Deploying Updates

```bash
cd /srv/massage_marketplace
source venv/bin/activate

git pull
pip install -r requirements.txt          # install new deps if any
python marketplace/manage.py migrate     # apply DB migrations
python marketplace/manage.py collectstatic --no-input

sudo systemctl restart massage_marketplace
sudo systemctl status massage_marketplace  # verify it came back up
```

> **Zero-downtime:** Nginx continues serving requests while gunicorn restarts (takes ~2s). For longer maintenance, return a 503 from Nginx by temporarily enabling a maintenance page.

---

## 12. Pre-launch Checklist

- [ ] `DEBUG=False` in `.env`
- [ ] `SECRET_KEY` is unique and not the default
- [ ] `ALLOWED_HOSTS` set to production domain(s)
- [ ] PostgreSQL running and migrated
- [ ] Redis running (`redis-cli ping`)
- [ ] `collectstatic` has been run
- [ ] Nginx config tested (`nginx -t`)
- [ ] SSL certificate active and auto-renewing
- [ ] `.env` permissions restricted (`chmod 640`)
- [ ] `SENTRY_DSN` set and a test error verified in Sentry dashboard
- [ ] `NOW_PAYMENTS_API_KEY` and `NOW_PAYMENTS_IPN` set
- [ ] `NOWPAYMENTS_SANDBOX=false` (not in sandbox mode)
- [ ] Admin superuser created
- [ ] `ADMIN_EMAILS` set for payment/subscription notifications
- [ ] Backup cron job created and tested
- [ ] UptimeRobot monitor created
- [ ] Media directory writable by `www-data`

---

## Troubleshooting

| Symptom | Check |
|---------|-------|
| 502 Bad Gateway | `systemctl status massage_marketplace` — gunicorn may have crashed |
| Static files 404 | `collectstatic` not run, or Nginx alias path wrong |
| 500 errors | Sentry dashboard or `journalctl -u massage_marketplace -p err` |
| DB connection error | PostgreSQL running? `DB_HOST`, `DB_USER`, `DB_PASSWORD` correct? |
| Redis connection error | `systemctl status redis-server`; check `REDIS_URL` in `.env` |
| Emails not sending | Check `EMAIL_*` vars; test with `python manage.py sendtestemail admin@yourdomain.com` |
| Payments not confirming | Check NOWPayments IPN secret matches `NOW_PAYMENTS_IPN`; verify webhook URL is reachable |
| High memory | `ps aux --sort=-%mem | head -10`; consider reducing gunicorn `--workers` to 1 |
