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

See [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) for the full production deployment guide including Nginx config, systemd services, SSL, backups, and monitoring.

**Deploy update (bare repo + post-receive hook):**
```bash
# From your local machine — hook handles everything on the server
git push production main
```

See [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) for initial server setup.

---

## Testing

```bash
# Fast — 372 tests in ~6s (in-memory SQLite, dummy cache, no Redis required)
./test.sh

# Specific app
./test.sh users
./test.sh providers

# Specific test class
python marketplace/manage.py test users.tests.CustomUserModelTests --settings=marketplace.test_settings
```

Tests use optimized settings: MD5 hashing, in-memory SQLite, `DummyCache`, no NOWPayments API calls.

---

## Project structure

```
marketplace/
├── marketplace/        # Project settings, URLs, middleware
├── users/              # Custom user model, email auth
├── providers/          # Provider profiles, pricing, preferences
├── clients/            # Client views, provider directory
├── reviews/            # Review and rating system
├── payments/           # Subscription payment processing (NOWPayments)
├── templates/          # Server-side rendered HTML
└── static/             # JS, CSS assets
```

## Key features

- Email-based authentication (no usernames)
- Provider profiles with pricing grid, gallery, preferences
- Subscription payments via cryptocurrency (NOWPayments — dynamic coin list)
- Automatic payment confirmation via IPN webhook
- Client reviews with per-category ratings and provider replies
- Location-based provider search (country/city, non-US)
- Redis caching for high-traffic endpoints (production only)
- Sentry error tracking + structured JSON logging to systemd journal
