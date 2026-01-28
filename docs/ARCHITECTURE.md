# Massage Marketplace - Architecture Documentation

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        Client Browser                           │
├─────────────────────────────────────────────────────────────────┤
│  HTML/CSS/JavaScript (Tailwind CSS)                             │
└────────────────────────┬────────────────────────────────────────┘
                         │
                    HTTP/HTTPS
                         │
┌────────────────────────▼────────────────────────────────────────┐
│              Django 5.0 Web Application Server                  │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Django URL Router (marketplace/urls.py)                 │  │
│  └──────────────────────────────────────────────────────────┘  │
│                         │                                       │
│  ┌──────────────────────▼──────────────────────────────────┐  │
│  │ Views Layer (Class-Based & Function-Based Views)       │  │
│  ├────────────────────────────────────────────────────────┤  │
│  │ • Authentication (users/views.py)                       │  │
│  │ • Provider Management (providers/views.py)              │  │
│  │ • Payment Management (payments/views.py)                │  │
│  │ • Admin Interfaces                                      │  │
│  └──────────────────────────────────────────────────────────┘  │
│                         │                                       │
│  ┌──────────────────────▼──────────────────────────────────┐  │
│  │ Forms & Validation (*/forms.py)                         │  │
│  │ • Signup, Login, Password Reset                         │  │
│  │ • Provider Profile, Service, Certification              │  │
│  │ • Subscription Settings                                 │  │
│  └──────────────────────────────────────────────────────────┘  │
│                         │                                       │
│  ┌──────────────────────▼──────────────────────────────────┐  │
│  │ Business Logic (Models)                                 │  │
│  ├────────────────────────────────────────────────────────┤  │
│  │ • User (Custom AbstractUser)                            │  │
│  │ • Provider                                              │  │
│  │ • Service                                               │  │
│  │ • Certification                                         │  │
│  │ • Review                                                │  │
│  │ • SubscriptionPayment                                   │  │
│  └──────────────────────────────────────────────────────────┘  │
│                         │                                       │
│  ┌──────────────────────▼──────────────────────────────────┐  │
│  │ Template Layer (HTML Rendering)                         │  │
│  ├────────────────────────────────────────────────────────┤  │
│  │ • Base template with navigation                         │  │
│  │ • Reusable includes (_messages, _form, _cards)          │  │
│  │ • App-specific templates                                │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ├──────────────────────────┐
                         │                          │
        ┌────────────────▼──────────────┐  ┌────────▼──────────────┐
        │   SQLite Database (Dev)        │  │   PostgreSQL (Prod)   │
        │   or PostgreSQL (Prod)         │  └───────────────────────┘
        │   - users_user                 │
        │   - providers_provider         │
        │   - providers_service          │
        │   - providers_certification    │
        │   - reviews_review             │
        │   - payments_payment           │
        └───────────────────────────────┘
                         │
        ┌────────────────▼──────────────┐
        │   File Storage (Media Files)   │
        ├────────────────────────────────┤
        │ • Provider photos              │
        │ • Certifications               │
        │ • Local: media/                │
        │ • Prod: Minio/S3               │
        └────────────────────────────────┘
```

## Application Structure

```
marketplace/
├── marketplace/                    # Django project configuration
│   ├── settings.py                # Project settings (DEBUG, DATABASES, APPS, etc.)
│   ├── test_settings.py           # Optimized test database settings
│   ├── urls.py                    # URL routing configuration
│   └── wsgi.py                    # WSGI application entry point
│
├── users/                          # User authentication and management
│   ├── models.py                  # Custom User model (extends AbstractUser)
│   ├── views.py                   # Auth views (Signup, Login, Password Reset)
│   ├── forms.py                   # Auth forms (SignupForm, LoginForm)
│   ├── backends.py                # Email-based authentication backend
│   ├── utils.py                   # Email verification token utilities
│   ├── admin.py                   # Django admin customization
│   └── tests.py                   # User model and auth tests
│
├── providers/                      # Provider profiles and services
│   ├── models.py                  # Provider, Service, Certification models
│   ├── views.py                   # Provider views and admin views
│   ├── forms.py                   # Provider, Service, Certification forms
│   ├── admin.py                   # Django admin with inlines
│   └── tests.py                   # Provider functionality tests
│
├── payments/                       # Payment and subscription management
│   ├── models.py                  # SubscriptionPayment model
│   ├── views.py                   # Admin payment views
│   ├── admin.py                   # Payment admin interface
│   └── tests.py                   # Payment functionality and admin tests
│
├── reviews/                        # Review and rating system
│   ├── models.py                  # Review model
│   ├── admin.py                   # Review admin
│   └── tests.py                   # Review tests
│
├── clients/                        # Client-related functionality (future)
│   ├── models.py                  # Client model (future)
│   └── views.py                   # Client views (future)
│
├── templates/                      # HTML templates
│   ├── base.html                  # Base layout with navigation
│   ├── includes/                  # Reusable template includes
│   │   ├── _messages.html         # Message display
│   │   ├── _form.html             # Generic form rendering
│   │   ├── _service_card.html     # Service card component
│   │   ├── _certification_card.html # Cert card component
│   │   └── _pagination.html       # Pagination component
│   ├── users/                     # Auth templates
│   │   ├── signup.html
│   │   ├── login.html
│   │   ├── password_reset.html
│   │   └── verify_email_error.html
│   ├── providers/                 # Provider templates
│   │   ├── dashboard.html
│   │   ├── profile_edit.html
│   │   ├── service_form.html
│   │   ├── service_list.html
│   │   ├── certification_form.html
│   │   ├── subscription.html
│   │   └── subscription_confirm.html
│   ├── admin/                     # Admin templates
│   │   ├── provider_list.html
│   │   ├── payment_list.html
│   │   └── payment_detail.html
│   └── emails/                    # Email templates
│       ├── verify_email.html
│       └── subscription_confirmation.html
│
├── static/                         # Static files (CSS, JS, images)
│   └── css/                        # Custom CSS (if needed)
│
├── media/                          # User-uploaded files
│   ├── providers/
│   │   ├── photos/
│   │   └── certifications/
│
├── docs/                           # Project documentation
│   ├── ARCHITECTURE.md
│   ├── DATABASE_SCHEMA.md
│   ├── PROVIDER_FLOWS.md
│   └── SPRINT1_SUMMARY.md
│
└── conftest.py                     # Pytest configuration and fixtures
```

## Technology Stack

### Backend
- **Framework**: Django 5.0
- **Language**: Python 3.11+
- **ORM**: Django ORM with PostgreSQL/SQLite

### Frontend
- **Template Engine**: Django Templates
- **CSS Framework**: Tailwind CSS (via CDN)
- **Form Handling**: Django Forms
- **JavaScript**: Vanilla JS for simple interactivity

### Database
- **Development**: SQLite3
- **Production**: PostgreSQL 14+
- **Migrations**: Django migrations

### Authentication
- **Method**: Email-based (custom backend)
- **Password Hashing**: Django's default (PBKDF2)
- **Session Management**: Django sessions
- **Email Verification**: Token-based (one-time use)

### File Storage
- **Development**: Local filesystem (`media/`)
- **Production**: Minio/S3-compatible object storage

### Email
- **Backend**: Console (dev), SMTP (production)
- **Templates**: HTML + plain text

### Testing
- **Framework**: Django TestCase + unittest
- **Coverage**: 90%+ on core logic
- **Command**: `python manage.py test --settings=marketplace.test_settings`

## Data Flow

### 1. Provider Signup & Activation
```
User → Signup Form → EmailBackend
  ↓
User.objects.create_user() → User Model
  ↓
generate_email_verification_token() → Token stored in User
  ↓
send_verification_email() → Email template rendered
  ↓
User clicks link → verify_email_token()
  ↓
User marked as verified → Ready to complete profile
```

### 2. Provider Profile Setup
```
Logged-in Provider → Dashboard
  ↓
Edit Profile Form → ProviderProfileUpdateView
  ↓
Form validation → Image resizing
  ↓
Provider.save() + User.save()
  ↓
Profile displayed on dashboard with stats
```

### 3. Service Management
```
Provider → Create Service Form
  ↓
ServiceForm validation → Price >= $5.00, Duration in (30,60,90)
  ↓
Service.objects.create()
  ↓
Service appears in provider's service list
  ↓
Displayed on provider dashboard and detail page
```

### 4. Subscription Payment
```
Provider → Activate Subscription
  ↓
ProviderSubscriptionView → Select payment method
  ↓
Provider.activate_subscription() → Set status='active', renewal_date
  ↓
SubscriptionPayment.objects.create() → status='pending'
  ↓
send_subscription_confirmation_email() → Template rendered
  ↓
Email sent to provider with payment instructions
  ↓
Admin → Monitor payment in AdminPaymentListView
  ↓
Once payment received → Mark as completed
```

### 5. Admin Payment Verification
```
AdminPaymentListView → Display all pending payments
  ↓
Filter by status/method/email
  ↓
Click on payment → AdminPaymentDetailView
  ↓
Verify transaction details
  ↓
Mark as completed/failed
  ↓
Update SubscriptionPayment record
  ↓
Send confirmation email to provider
```

## Key Design Patterns

### 1. Model-View-Template (MVT)
- **Models**: Define data structure and business logic
- **Views**: Handle requests and return responses
- **Templates**: Render HTML for responses

### 2. Class-Based Views
- Inherit from Django generic views (ListView, DetailView, FormView)
- Implement mixins for access control (LoginRequiredMixin, AdminRequiredMixin)
- Override methods for customization

### 3. Mixins for Access Control
```python
class ProviderRequiredMixin(LoginRequiredMixin):
    """Only providers can access"""
    
class AdminRequiredMixin(LoginRequiredMixin):
    """Only admins can access"""
```

### 4. Forms for Validation
- Django ModelForms for CRUD operations
- Custom validation in `clean_*` methods
- Image validation and processing

### 5. Reusable Template Components
- `_messages.html` - Unified alert display
- `_form.html` - Generic form rendering
- `_service_card.html`, `_certification_card.html` - Components

## Security Considerations

### Authentication
- ✓ Email-based login (no username)
- ✓ Secure password hashing (PBKDF2)
- ✓ Email verification tokens (one-time use)
- ✓ Session-based authentication

### Authorization
- ✓ User type checks (provider, client, admin)
- ✓ Ownership verification (can only edit own resources)
- ✓ Admin-only views with decorators

### Data Protection
- ✓ CSRF tokens on all POST forms
- ✓ SQL injection prevented (Django ORM)
- ✓ XSS prevention (Django template auto-escaping)
- ✓ Encrypted bank details (TextField, encryption in future)

### File Upload Security
- ✓ File type validation (JPEG, PNG, GIF only)
- ✓ File size limits (5MB max)
- ✓ Image format verification with PIL
- ✓ Unique filename generation

## Performance Optimizations

### Database
- `select_related()` for FK relationships
- `prefetch_related()` for reverse relationships
- Pagination (50 items per page)
- Indexes on frequently filtered fields

### Caching (Future)
- Session-based caching
- Template fragment caching
- Database query caching

### Frontend
- Tailwind CSS via CDN (no build step needed)
- Minimal JavaScript
- Fast page loads

## Deployment Architecture

### Development
```
SQLite → Django Dev Server → http://localhost:8000
```

### Production
```
PostgreSQL ← Django App (Gunicorn)
Minio S3 ← File uploads
Nginx ← Reverse proxy
Let's Encrypt ← SSL/TLS
```

### Scaling (Future)
- Load balancer (nginx/HAProxy)
- Multiple app servers
- Database replication
- CDN for static files
- Message queue (Celery) for async tasks

## Testing Strategy

### Unit Tests
- Model tests (creation, validation, methods)
- Form tests (validation, cleaning)

### Integration Tests
- View tests (access control, functionality)
- End-to-end user flows

### Coverage Goals
- Models: 100%
- Forms: 100%
- Views: 95%+
- Overall: 90%+

## Future Enhancements

### Phase 2
- Client marketplace with search/filter
- Booking system
- Real-time notifications
- Payment processing integration

### Phase 3
- Mobile app (React Native)
- Advanced analytics
- Ratings and reviews
- Messaging system

### Phase 4
- Multi-language support
- Marketing automation
- Affiliate program
- Analytics dashboard
