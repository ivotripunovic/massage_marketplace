# Massage Marketplace - Database Schema

## Entity Relationship Diagram (ASCII)

```
                    ┌─────────────────┐
                    │   auth_user     │
                    ├─────────────────┤
                    │ id (PK)         │
                    │ email (UNIQUE)  │◄──────┐
                    │ password        │       │
                    │ first_name      │       │
                    │ last_name       │       │
                    │ user_type       │       │
                    │ is_active       │       │
                    │ is_staff        │       │
                    │ is_superuser    │       │
                    │ created_at      │       │
                    │ updated_at      │       │
                    └─────────────────┘       │
                                              │
                                   ONE-TO-ONE │
                                              │
                    ┌─────────────────────────┘
                    │
                    ▼
        ┌──────────────────────────┐
        │  providers_provider      │
        ├──────────────────────────┤
        │ id (PK)                  │
        │ user_id (FK, UNIQUE)     │──►user_id
        │ phone                    │
        │ bio                      │
        │ photo                    │
        │ subscription_status      │
        │ subscription_payment_method│
        │ subscription_renewal_date│
        │ crypto_address           │
        │ bank_account_encrypted   │
        │ created_at               │
        │ updated_at               │
        └──────────────────────────┘
                  │ ONE
                  │
    ┌─────────────┼──────────────────┐
    │             │                  │
  MANY          MANY                MANY
    │             │                  │
    ▼             ▼                  ▼
┌─────────────┐ ┌──────────────────┐ ┌─────────────────────────┐
│services     │ │certifications    │ │reviews                  │
├─────────────┤ ├──────────────────┤ ├─────────────────────────┤
│id (PK)      │ │id (PK)           │ │id (PK)                  │
│provider_id  │ │provider_id       │ │provider_id              │
│service_type │ │name              │ │client_name              │
│description  │ │image             │ │client_email             │
│price        │ │uploaded_at       │ │rating                   │
│duration     │ │                  │ │comment                  │
│is_active    │ │                  │ │created_at               │
│created_at   │ │                  │ │                         │
│updated_at   │ │                  │ │UNIQUE: (provider_id,    │
│             │ │                  │ │        client_email)    │
└─────────────┘ └──────────────────┘ └─────────────────────────┘

    ┌────────────────────────────────────────────┐
    │  payments_subscription_payment              │
    ├────────────────────────────────────────────┤
    │ id (PK)                                     │
    │ provider_id (FK)                            │
    │ amount (Decimal 10,2)                       │
    │ payment_method                              │
    │ status                                      │
    │ reference_id                                │
    │ created_at                                  │
    │ completed_at                                │
    │ notes                                       │
    └────────────────────────────────────────────┘
```

---

## Table Specifications

### Users (Django Built-in + Custom Fields)

**Table**: `auth_user` (Django's built-in with extensions)

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | INTEGER | PRIMARY KEY, AUTO_INCREMENT | |
| `email` | VARCHAR(254) | UNIQUE, NOT NULL | Used as login identifier |
| `password` | VARCHAR(128) | NOT NULL | bcrypt hashed |
| `first_name` | VARCHAR(150) | NULL | Optional |
| `last_name` | VARCHAR(150) | NULL | Optional |
| `is_active` | BOOLEAN | DEFAULT TRUE | Soft delete flag |
| `is_staff` | BOOLEAN | DEFAULT FALSE | Admin access |
| `is_superuser` | BOOLEAN | DEFAULT FALSE | Full admin access |
| `date_joined` | DATETIME | AUTO_NOW_ADD | Account creation time |
| `last_login` | DATETIME | NULL | Last login timestamp |
| `user_type` | VARCHAR(20) | CHOICES: provider, client, admin | Account type |
| `is_email_verified` | BOOLEAN | DEFAULT FALSE | Email verification status |
| `email_verification_token` | VARCHAR(255) | UNIQUE, NULL | One-time token for verification |
| `phone_number` | VARCHAR(20) | NULL | Optional phone |

**Indexes**:
- PRIMARY: `id`
- UNIQUE: `email`
- INDEX: `user_type`
- INDEX: `is_email_verified`

**Constraints**:
- `email` must be unique and not null
- `user_type` must be one of: 'provider', 'client', 'admin'
- `password` must be hashed using Django's password hasher

---

### Providers

**Table**: `providers_provider`

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | INTEGER | PRIMARY KEY, AUTO_INCREMENT | |
| `user_id` | INTEGER | FOREIGN KEY, UNIQUE | Reference to User (one-to-one) |
| `phone` | VARCHAR(20) | NOT NULL | Contact phone number |
| `bio` | TEXT | NULL | Professional biography |
| `photo` | VARCHAR(100) | NULL | ImageField path |
| `subscription_status` | VARCHAR(20) | CHOICES, DEFAULT 'inactive' | active, inactive, suspended |
| `subscription_payment_method` | VARCHAR(50) | CHOICES, NULL | crypto_bitcoin, crypto_ethereum, crypto_usdc, bank_transfer |
| `subscription_renewal_date` | DATE | NULL | Next renewal date |
| `crypto_address` | VARCHAR(200) | NULL | Bitcoin/Ethereum address |
| `bank_account_encrypted` | TEXT | NULL | Encrypted bank details |
| `created_at` | DATETIME | AUTO_NOW_ADD | Creation timestamp |
| `updated_at` | DATETIME | AUTO_NOW | Last update timestamp |

**Indexes**:
- PRIMARY: `id`
- FOREIGN KEY: `user_id`
- INDEX: `subscription_status`
- INDEX: `created_at`

**Constraints**:
- `user_id` must reference valid User record
- `user_id` is unique (one provider per user)
- `phone` is required and not null
- `subscription_status` must be one of allowed choices

**Methods**:
- `activate_subscription(payment_method)` - Set active with 30-day renewal
- `deactivate_subscription()` - Set to inactive
- `is_subscription_active()` - Boolean check

---

### Services

**Table**: `providers_service`

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | INTEGER | PRIMARY KEY, AUTO_INCREMENT | |
| `provider_id` | INTEGER | FOREIGN KEY, NOT NULL | Reference to Provider |
| `service_type` | VARCHAR(50) | CHOICES, NOT NULL | swedish, deep_tissue, thai, reflexology, hot_stone, aromatherapy |
| `description` | TEXT | NULL | Service description |
| `price` | DECIMAL(10,2) | NOT NULL, >= 5.00 | Service price in USD |
| `duration_minutes` | INTEGER | CHOICES, NOT NULL | 30, 60, or 90 |
| `is_active` | BOOLEAN | DEFAULT TRUE | Active/inactive flag |
| `created_at` | DATETIME | AUTO_NOW_ADD | Creation timestamp |
| `updated_at` | DATETIME | AUTO_NOW | Last update timestamp |

**Indexes**:
- PRIMARY: `id`
- FOREIGN KEY: `provider_id`
- UNIQUE: `(provider_id, service_type)` - one service type per provider
- INDEX: `is_active`
- INDEX: `created_at`

**Constraints**:
- `provider_id` must reference valid Provider record
- `service_type` must be from allowed choices
- `price` must be >= 5.00
- `duration_minutes` must be 30, 60, or 90
- Unique constraint on (provider_id, service_type)

**Display Method**:
- `get_service_type_display()` - Returns human-readable service name

---

### Certifications

**Table**: `providers_certification`

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | INTEGER | PRIMARY KEY, AUTO_INCREMENT | |
| `provider_id` | INTEGER | FOREIGN KEY, NOT NULL | Reference to Provider |
| `name` | VARCHAR(200) | NOT NULL | Certification name |
| `image` | VARCHAR(100) | NOT NULL | ImageField path |
| `uploaded_at` | DATETIME | AUTO_NOW_ADD | Upload timestamp |

**Indexes**:
- PRIMARY: `id`
- FOREIGN KEY: `provider_id`
- INDEX: `uploaded_at`

**Constraints**:
- `provider_id` must reference valid Provider record
- `name` is required
- `image` file must be valid and < 5MB

**File Storage**:
- Path: `media/providers/certifications/`
- Formats: JPEG, PNG, GIF

---

### Reviews

**Table**: `reviews_review`

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | INTEGER | PRIMARY KEY, AUTO_INCREMENT | |
| `provider_id` | INTEGER | FOREIGN KEY, NOT NULL | Reference to Provider |
| `client_name` | VARCHAR(200) | NULL | Anonymous reviews allowed |
| `client_email` | VARCHAR(254) | NOT NULL | Client email identifier |
| `rating` | INTEGER | CHOICES 1-5, NOT NULL | Star rating |
| `comment` | TEXT | NOT NULL, MAX 250 chars | Review text |
| `created_at` | DATETIME | AUTO_NOW_ADD | Creation timestamp |

**Indexes**:
- PRIMARY: `id`
- FOREIGN KEY: `provider_id`
- UNIQUE: `(provider_id, client_email)` - one review per client
- INDEX: `created_at`

**Constraints**:
- `provider_id` must reference valid Provider record
- `rating` must be 1, 2, 3, 4, or 5
- `comment` must be <= 250 characters
- Unique constraint on (provider_id, client_email)

**Validation**:
- Rating range: 1-5 (enforced)
- Comment length: max 250 chars (enforced)

---

### Subscription Payments

**Table**: `payments_subscription_payment`

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | INTEGER | PRIMARY KEY, AUTO_INCREMENT | |
| `provider_id` | INTEGER | FOREIGN KEY, NOT NULL | Reference to Provider |
| `amount` | DECIMAL(10,2) | NOT NULL | Payment amount (usually 29.99) |
| `payment_method` | VARCHAR(50) | CHOICES, NOT NULL | Crypto or bank method |
| `status` | VARCHAR(20) | CHOICES, DEFAULT 'pending' | pending, completed, failed |
| `reference_id` | VARCHAR(255) | NULL | Transaction hash or ID |
| `created_at` | DATETIME | AUTO_NOW_ADD | Payment creation time |
| `completed_at` | DATETIME | NULL | Payment completion time |
| `notes` | TEXT | NULL | Admin notes |

**Indexes**:
- PRIMARY: `id`
- FOREIGN KEY: `provider_id`
- INDEX: `status`
- INDEX: `created_at`
- INDEX: `payment_method`

**Constraints**:
- `provider_id` must reference valid Provider record
- `payment_method` must be: crypto_bitcoin, crypto_ethereum, crypto_usdc, bank_transfer
- `status` must be: pending, completed, failed
- `amount` must be decimal (10 digits, 2 decimal places)

**Payment Methods**:
- `crypto_bitcoin` - Bitcoin address payment
- `crypto_ethereum` - Ethereum address payment
- `crypto_usdc` - USDC stablecoin payment
- `bank_transfer` - Bank account transfer

---

## Data Integrity Constraints

### Referential Integrity
- All foreign keys enforce referential integrity
- Deleting a User cascades to Provider
- Deleting a Provider cascades to Services, Certifications, Reviews, Payments

### Unique Constraints
- User email is unique (case-insensitive)
- One provider per user
- One service type per provider
- One review per (provider, client_email)

### Check Constraints
- Service price >= 5.00
- Service duration in (30, 60, 90)
- Review rating in (1, 2, 3, 4, 5)
- Review comment <= 250 characters
- User type in (provider, client, admin)
- Subscription status in (active, inactive, suspended)

---

## Migration History

### Week 1: Initial Models
- Created User model (custom AbstractUser)
- Created Provider model
- Created Service model
- Created Certification model
- Created Review model
- Created SubscriptionPayment model

### Migrations Applied
```
marketplace/
├── users/migrations/
│   ├── 0001_initial.py
│   └── (auto-generated by Django)
├── providers/migrations/
│   ├── 0001_initial.py
│   └── (auto-generated by Django)
├── reviews/migrations/
│   ├── 0001_initial.py
│   └── (auto-generated by Django)
└── payments/migrations/
    ├── 0001_initial.py
    └── (auto-generated by Django)
```

### Status
✓ All migrations created and applied
✓ Database schema matches models
✓ No pending migrations

---

## Query Optimization

### Common Queries

**Get provider with all related data**:
```python
Provider.objects.select_related('user').prefetch_related(
    'services',
    'certifications',
    'review_set'
).get(user_id=user_id)
```

**Calculate provider stats**:
```python
from django.db.models import Count, Avg

provider = Provider.objects.annotate(
    service_count=Count('services', distinct=True),
    review_count=Count('review', distinct=True),
    avg_rating=Avg('review__rating')
).get(id=provider_id)
```

**List all active providers**:
```python
Provider.objects.filter(
    subscription_status='active'
).select_related('user').prefetch_related('services')
```

### Indexes
Created indexes on:
- `user.email` (UNIQUE)
- `provider.user_id` (UNIQUE FK)
- `service.provider_id` (FK)
- `service.is_active` (filter)
- `review.provider_id` (FK)
- `review.created_at` (sort)
- All `created_at` fields (sort/filter)

---

## Database Setup

### Development (SQLite)
```bash
python manage.py migrate
python manage.py createsuperuser
```

### Creating Test Data
```python
from tests.helpers import create_test_provider, create_test_service

provider = create_test_provider()
service = create_test_service(provider)
```

---

## Backup & Recovery

### Backup Database
```bash
python manage.py dumpdata > backup.json
```

### Restore Database
```bash
python manage.py loaddata backup.json
```

### Reset Database (Development Only)
```bash
rm db.sqlite3
python manage.py migrate
python manage.py createsuperuser
```
