# Massage Marketplace

A Django-based marketplace platform for massage therapy services.

## Local Development Setup

### Prerequisites
- Python 3.11+
- pip

### Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd massage_marketplace
   ```

2. **Create and activate virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env — keep DEBUG=True for local dev
   ```

5. **Run migrations:**
   ```bash
   python marketplace/manage.py migrate
   ```

6. **Create superuser:**
   ```bash
   python marketplace/manage.py createsuperuser
   ```

7. **Run development server:**
   ```bash
   python marketplace/manage.py runserver
   ```
   Server available at `http://localhost:8000`

> **Note:** Local dev uses `DummyCache` (no-op) automatically when `DEBUG=True`. No Redis needed.

---

## Production Deployment

### Prerequisites
- Python 3.11+
- PostgreSQL 14+
- Redis 6+
- A WSGI server (gunicorn recommended)
- A reverse proxy (nginx recommended)

### 1. System dependencies

```bash
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip postgresql redis-server nginx
```

### 2. Application setup

```bash
git clone <repository-url> /srv/massage_marketplace
cd /srv/massage_marketplace

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn django-redis
```

### 3. Environment variables

Copy and fill in `.env`:

```bash
cp .env.example .env
```

Key production values to set:

```dotenv
# Django
SECRET_KEY=<long-random-string>
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Database (PostgreSQL)
DB_ENGINE=django.db.backends.postgresql
DB_NAME=massage_marketplace
DB_USER=massage_user
DB_PASSWORD=<strong-password>
DB_HOST=127.0.0.1
DB_PORT=5432

# Redis cache
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

# Crypto wallet addresses
CRYPTO_BITCOIN_ADDRESS=<your-btc-address>
CRYPTO_ETHEREUM_ADDRESS=<your-eth-address>
CRYPTO_USDC_ADDRESS=<your-usdc-address>

# Bank details
BANK_NAME=Your Bank Name
BANK_ACCOUNT_NAME=Your Company Name
BANK_ACCOUNT_NUMBER=****1234
BANK_ROUTING_NUMBER=<routing>
BANK_SWIFT_CODE=<swift>
```

### 4. Database setup

```bash
sudo -u postgres psql -c "CREATE USER massage_user WITH PASSWORD '<strong-password>';"
sudo -u postgres psql -c "CREATE DATABASE massage_marketplace OWNER massage_user;"

cd /srv/massage_marketplace
source venv/bin/activate
python marketplace/manage.py migrate
python marketplace/manage.py createsuperuser
python marketplace/manage.py collectstatic --no-input
```

### 5. Redis

```bash
sudo systemctl enable redis-server
sudo systemctl start redis-server

# Verify
redis-cli ping  # should return PONG
```

### 6. Gunicorn

Create `/etc/systemd/system/massage_marketplace.service`:

```ini
[Unit]
Description=Massage Marketplace gunicorn
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/srv/massage_marketplace/marketplace
Environment="PATH=/srv/massage_marketplace/venv/bin"
EnvironmentFile=/srv/massage_marketplace/.env
ExecStart=/srv/massage_marketplace/venv/bin/gunicorn \
    marketplace.wsgi \
    --workers 4 \
    --bind 127.0.0.1:8000 \
    --access-logfile /var/log/massage_marketplace/access.log \
    --error-logfile /var/log/massage_marketplace/error.log
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

```bash
sudo mkdir -p /var/log/massage_marketplace
sudo chown www-data: /var/log/massage_marketplace

sudo systemctl daemon-reload
sudo systemctl enable massage_marketplace
sudo systemctl start massage_marketplace
```

**Gunicorn worker count:** set `--workers` to `(2 × CPU cores) + 1`. Check with `nproc`.

### 7. Nginx

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

    client_max_body_size 60M;  # allows profile photo + video uploads

    location /static/ {
        alias /srv/massage_marketplace/marketplace/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias /srv/massage_marketplace/marketplace/media/;
        expires 7d;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/massage_marketplace /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 8. SSL (Let's Encrypt)

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

### 9. Seed data (optional)

```bash
source venv/bin/activate
python marketplace/manage.py seed_beta_data
```

---

## Updating the application

```bash
cd /srv/massage_marketplace
source venv/bin/activate

git pull
pip install -r requirements.txt
python marketplace/manage.py migrate
python marketplace/manage.py collectstatic --no-input

sudo systemctl restart massage_marketplace
```

---

## Testing

```bash
# Fast — 374 tests in ~6s (uses in-memory SQLite, dummy cache, no Redis)
./test.sh

# Specific app
./test.sh users
./test.sh providers

# Specific test class
python marketplace/manage.py test users.tests.CustomUserModelTests --settings=marketplace.test_settings
```

Tests use optimized settings: MD5 hashing, in-memory SQLite, `DummyCache`.

---

## Load testing

```bash
pip install locust
python -m gunicorn marketplace.wsgi -w 4 --chdir marketplace &
locust -f locustfile.py --host=http://localhost:8000
# Open http://localhost:8089
```

---

## Project structure

```
marketplace/
├── marketplace/        # Project settings, URLs, middleware
├── users/              # Custom user model, email auth
├── providers/          # Provider profiles, pricing, preferences
├── clients/            # Client views, provider directory
├── reviews/            # Review and rating system
├── payments/           # Subscription payment processing
├── templates/          # Server-side rendered HTML
└── static/             # JS, CSS assets
```

## Key features

- Email-based authentication (no usernames)
- Provider profiles with pricing, gallery, preferences, certifications
- Subscription payments via crypto (BTC/ETH/USDC) and bank transfer
- Admin payment verification workflow
- Client reviews with per-category ratings and provider replies
- Location-based provider search (country/city)
- Redis caching for high-traffic endpoints (production only)
