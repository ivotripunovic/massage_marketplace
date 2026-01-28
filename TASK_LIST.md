# Massage Marketplace - Detailed Task List for Code Implementation

**Status:** Ready for development  
**Format:** Each task is atomic and can be completed in 1-4 hours  
**Testing:** All tasks include test requirements  
**Workflow:** Complete task → mark [✓ DONE] → move to next task

---

## SPRINT 1: Foundation & Provider Portal

### WEEK 1: Project Bootstrap & Database Schema

#### TASK 1.1: Initialize Django 5.0 Project Structure
**Status:** [✓ DONE] ✓

**Objective:** Create Django project with proper structure, dependencies, and local development setup.

**Requirements:**
- Create Django 5.0 project: `django-admin startproject marketplace`
- Create Django apps: `users`, `providers`, `clients`, `reviews`, `payments`
- Create `requirements.txt` with minimal dependencies:
  ```
  Django==5.0.1
  psycopg[binary]==3.1.18
  python-dotenv==1.0.0
  Pillow==10.1.0
  web3==6.11.2
  ```
- Create `.env` template file (not committed)
- Create `.gitignore` for Django
- Create `README.md` with setup instructions

**Tests:**
- Verify `python manage.py migrate` runs without errors
- Verify `python manage.py runserver` starts on http://localhost:8000
- Verify Django admin loads at http://localhost:8000/admin

**Acceptance Criteria:**
- [ ] Project structure created with all apps
- [ ] `.env.example` file exists with placeholders
- [ ] `requirements.txt` matches versions above
- [ ] `README.md` has complete local setup instructions
- [ ] All team members can run project locally

**Mark as [✓ DONE] when:** Project runs locally and admin page loads.

---

#### TASK 1.2: Create Custom User Model (Extended AbstractUser)
**Status:** [✓ DONE] ✓

**Objective:** Implement custom Django User model with email-based authentication.

**Requirements:**
- Extend `AbstractUser` in `users/models.py`
- Fields:
  - `email` (unique, primary identifier)
  - `user_type` (choices: 'provider', 'client', 'admin')
  - `is_email_verified` (boolean, default False)
  - `email_verification_token` (CharField, nullable)
  - `phone_number` (CharField, optional)
- Make email the login username (set `USERNAME_FIELD = 'email'`)
- Remove username requirement
- Add custom manager with `create_user()` and `create_superuser()` methods

**Tests:**
```python
def test_create_user():
    user = User.objects.create_user(email='test@example.com', password='testpass123')
    assert user.email == 'test@example.com'
    assert user.check_password('testpass123')

def test_email_is_unique():
    User.objects.create_user(email='test@example.com', password='pass')
    with pytest.raises(Exception):  # IntegrityError
        User.objects.create_user(email='test@example.com', password='pass')

def test_user_type_choices():
    user = User.objects.create_user(email='test@example.com', password='pass', user_type='provider')
    assert user.user_type == 'provider'
```

**Acceptance Criteria:**
- [ ] Custom User model extends AbstractUser
- [ ] Email is unique and used for login
- [ ] `user_type` field with correct choices
- [ ] Migration created and runs
- [ ] All tests pass
- [ ] Settings.py updated with `AUTH_USER_MODEL = 'users.User'`

**Mark as [✓ DONE] when:** Custom user model migrates and tests pass.

---

#### TASK 1.3: Create Provider Model & Admin Registration
**Status:** [✓ DONE] ✓

**Objective:** Build Provider profile model with required fields and register in Django admin.

**Requirements:**
- File: `providers/models.py`
- Create `Provider` model:
  - `user` (OneToOneField to User)
  - `bio` (TextField, optional)
  - `phone` (CharField, required)
  - `photo` (ImageField, optional, stored in `media/providers/photos/`)
  - `subscription_status` (choices: 'active', 'inactive', 'suspended', default 'inactive')
  - `subscription_payment_method` (choices: 'crypto', 'bank_transfer', nullable)
  - `subscription_renewal_date` (DateField, nullable)
  - `crypto_address` (CharField, optional - stores Bitcoin/Ethereum address)
  - `bank_account_encrypted` (TextField, optional, for storing encrypted bank details)
  - `created_at` (DateTimeField, auto_now_add)
  - `updated_at` (DateTimeField, auto_now)
- Add `__str__()` method returning provider name
- Register in Django admin with search, filters, and inline editing

**Tests:**
```python
def test_provider_creation():
    user = User.objects.create_user(email='provider@test.com', password='pass', user_type='provider')
    provider = Provider.objects.create(user=user, phone='+1234567890')
    assert provider.user.email == 'provider@test.com'
    assert provider.subscription_status == 'inactive'

def test_provider_admin_registered():
    assert Provider in admin.site._registry
```

**Acceptance Criteria:**
- [ ] Provider model has all required fields
- [ ] Migrations created and applied
- [ ] Can create provider via Django admin
- [ ] Can search providers by name in admin
- [ ] Can filter by subscription_status in admin
- [ ] All tests pass

**Mark as [✓ DONE] when:** Provider model migrates, tests pass, admin interface works.

---

#### TASK 1.4: Create Service Model & Certification Model
**Status:** [✓ DONE] ✓

**Objective:** Build Service and Certification models for provider offerings.

**Requirements:**

**Service Model** (`providers/models.py`):
- `provider` (ForeignKey to Provider)
- `service_type` (choices: 'swedish', 'deep_tissue', 'thai', 'reflexology', 'hot_stone', 'aromatherapy')
- `description` (TextField, optional)
- `price` (DecimalField, max_digits=10, decimal_places=2, min 5.00)
- `duration_minutes` (IntegerField, choices: 30, 60, 90)
- `is_active` (BooleanField, default True)
- `created_at` (DateTimeField, auto_now_add)
- `updated_at` (DateTimeField, auto_now)
- `__str__()` returning "Provider - Service Type - $Price"

**Certification Model** (`providers/models.py`):
- `provider` (ForeignKey to Provider)
- `name` (CharField, e.g., "Licensed Massage Therapist")
- `image` (ImageField, stored in `media/providers/certifications/`)
- `uploaded_at` (DateTimeField, auto_now_add)
- `__str__()` returning "Provider - Certification Name"

**Validations:**
- Service price >= 5.00
- Service duration in (30, 60, 90)
- Service type from choices only

**Tests:**
```python
def test_create_service():
    provider = create_test_provider()
    service = Service.objects.create(
        provider=provider,
        service_type='swedish',
        price=75.00,
        duration_minutes=60
    )
    assert service.price == 75.00
    assert service.duration_minutes == 60

def test_service_price_validation():
    provider = create_test_provider()
    with pytest.raises(ValidationError):
        service = Service(provider=provider, price=2.00, duration_minutes=60)
        service.full_clean()

def test_certification_creation():
    provider = create_test_provider()
    cert = Certification.objects.create(provider=provider, name='LMT')
    assert cert.name == 'LMT'
```

**Acceptance Criteria:**
- [ ] Service model with all required fields
- [ ] Certification model created
- [ ] Both models have proper validation
- [ ] Both registered in Django admin
- [ ] Migrations created and applied
- [ ] All tests pass

**Mark as [✓ DONE] when:** Models migrate, validation works, admin interfaces functional.

---

#### TASK 1.5: Create Review & SubscriptionPayment Models
**Status:** [✓ DONE] ✓

**Objective:** Build models for client reviews and provider payment tracking.

**Requirements:**

**Review Model** (`reviews/models.py`):
- `provider` (ForeignKey to Provider)
- `client_name` (CharField, optional - can be anonymous)
- `rating` (IntegerField, choices: 1-5)
- `comment` (TextField, max_length=250)
- `created_at` (DateTimeField, auto_now_add)
- Constraint: Unique (provider, client_email) to prevent duplicate reviews per client
- `__str__()` returning "Provider - Rating Stars - Date"

**SubscriptionPayment Model** (`payments/models.py`):
- `provider` (ForeignKey to Provider)
- `amount` (DecimalField, default to subscription cost, e.g., 29.99)
- `payment_method` (choices: 'crypto_bitcoin', 'crypto_ethereum', 'crypto_usdc', 'bank_transfer')
- `status` (choices: 'pending', 'completed', 'failed', default 'pending')
- `reference_id` (CharField, nullable - tx hash for crypto, transaction ID for bank)
- `created_at` (DateTimeField, auto_now_add)
- `completed_at` (DateTimeField, nullable)
- `notes` (TextField, for admin notes)
- `__str__()` returning "Provider - Amount - Status - Date"

**Tests:**
```python
def test_review_creation():
    provider = create_test_provider()
    review = Review.objects.create(provider=provider, rating=5, comment="Great service!")
    assert review.rating == 5

def test_review_rating_validation():
    provider = create_test_provider()
    with pytest.raises(ValidationError):
        review = Review(provider=provider, rating=6)
        review.full_clean()

def test_payment_creation():
    provider = create_test_provider()
    payment = SubscriptionPayment.objects.create(
        provider=provider,
        amount=29.99,
        payment_method='crypto_bitcoin'
    )
    assert payment.status == 'pending'

def test_payment_methods():
    provider = create_test_provider()
    for method in ['crypto_bitcoin', 'crypto_ethereum', 'crypto_usdc', 'bank_transfer']:
        payment = SubscriptionPayment.objects.create(
            provider=provider, payment_method=method
        )
        assert payment.payment_method == method
```

**Acceptance Criteria:**
- [ ] Review model with rating validation (1-5)
- [ ] SubscriptionPayment model with status tracking
- [ ] Both models registered in admin
- [ ] Unique constraint on reviews prevents duplicates
- [ ] Migrations created and applied
- [ ] All tests pass

**Mark as [✓ DONE] when:** Models migrate, validations work, tests pass.

---

#### TASK 1.6: Create & Register All Models in Django Admin
**Status:** [✓ DONE]

**Objective:** Configure Django admin interface for all models with proper display, search, and filters.

**Requirements:**
- File: `users/admin.py`, `providers/admin.py`, `reviews/admin.py`, `payments/admin.py`

**User Admin:**
- List display: email, user_type, is_active, created_at
- Search fields: email, phone_number
- Filter by: user_type, is_active, created_at
- Readonly fields: created_at, email_verification_token

**Provider Admin:**
- List display: name, phone, subscription_status, created_at
- Search fields: user__email, phone
- Filter by: subscription_status, subscription_payment_method, created_at
- Readonly fields: created_at, updated_at
- Inline: Services, Certifications

**Service Admin:**
- List display: provider, service_type, price, duration_minutes, is_active
- Search fields: provider__user__email, service_type
- Filter by: service_type, is_active, price
- Readonly fields: created_at, updated_at

**Review Admin:**
- List display: provider, rating, created_at, client_name
- Search fields: provider__user__email, comment
- Filter by: rating, created_at
- Readonly fields: created_at

**SubscriptionPayment Admin:**
- List display: provider, amount, status, payment_method, created_at
- Search fields: provider__user__email, reference_id
- Filter by: status, payment_method, created_at
- Readonly fields: created_at, completed_at
- Actions: Mark as completed, Mark as failed

**Tests:**
```python
def test_admin_sites_registered():
    from django.contrib import admin
    assert User in admin.site._registry
    assert Provider in admin.site._registry
    assert Service in admin.site._registry
    assert Review in admin.site._registry
    assert SubscriptionPayment in admin.site._registry

def test_admin_user_can_access():
    admin_user = User.objects.create_superuser(
        email='admin@test.com', password='adminpass123'
    )
    assert admin_user.is_staff
```

**Acceptance Criteria:**
- [ ] All models registered in admin
- [ ] List displays show correct fields
- [ ] Search fields functional
- [ ] Filters work correctly
- [ ] Inline editing for Services/Certifications works
- [ ] Can navigate admin without errors
- [ ] Create/edit/delete operations work in admin

**Mark as [✓ DONE] when:** All admin interfaces functional and tested.

---

#### TASK 1.7: Create Test Fixtures & Utilities
**Status:** [✓ DONE]

**Objective:** Create reusable test helpers for all subsequent tests.

**Requirements:**
- File: `tests/conftest.py` (pytest fixtures)
- Create fixtures:
  ```python
  @pytest.fixture
  def test_user():
      return User.objects.create_user(
          email='test@example.com',
          password='testpass123'
      )
  
  @pytest.fixture
  def test_provider(test_user):
      return Provider.objects.create(
          user=test_user,
          phone='+1234567890'
      )
  
  @pytest.fixture
  def test_service(test_provider):
      return Service.objects.create(
          provider=test_provider,
          service_type='swedish',
          price=75.00,
          duration_minutes=60
      )
  
  @pytest.fixture
  def test_review(test_provider):
      return Review.objects.create(
          provider=test_provider,
          rating=5,
          comment="Great!"
      )
  
  @pytest.fixture
  def test_payment(test_provider):
      return SubscriptionPayment.objects.create(
          provider=test_provider,
          amount=29.99,
          payment_method='crypto_bitcoin'
      )
  ```
- Create helper functions in `tests/helpers.py`:
  ```python
  def create_test_user(email='test@example.com', user_type='provider'):
      return User.objects.create_user(email=email, password='pass', user_type=user_type)
  
  def create_test_provider(user=None):
      if not user:
          user = create_test_user()
      return Provider.objects.create(user=user, phone='+1234567890')
  
  def create_test_service(provider=None):
      if not provider:
          provider = create_test_provider()
      return Service.objects.create(
          provider=provider,
          service_type='swedish',
          price=75.00,
          duration_minutes=60
      )
  ```
- Create `pytest.ini` configuration
- Ensure tests can run with `pytest`

**Tests:**
```python
def test_fixtures_work(test_user, test_provider, test_service):
    assert test_user.email == 'test@example.com'
    assert test_provider.user == test_user
    assert test_service.provider == test_provider
```

**Acceptance Criteria:**
- [ ] `conftest.py` created with all fixtures
- [ ] `helpers.py` created with utility functions
- [ ] `pytest.ini` configured
- [ ] Fixtures can be imported in all test files
- [ ] All helper functions tested and working
- [ ] Tests run with `pytest` command

**Mark as [✓ DONE] when:** Fixtures work and are used in subsequent tests.

---

#### TASK 1.8: Git Setup & Initial Commit
**Status:** [✓ DONE]

**Objective:** Initialize Git repository with proper structure and documentation.

**Requirements:**
- Create `.gitignore` for Django:
  ```
  __pycache__/
  *.py[cod]
  *$py.class
  .env
  .env.local
  db.sqlite3
  /media/
  /static/
  .vscode/
  .idea/
  *.log
  venv/
  ```
- Create `CONTRIBUTING.md` with:
  - Git workflow (feature branches)
  - Code style guidelines
  - Testing requirements
  - Commit message format
- Update `README.md` with complete setup instructions:
  ```bash
  git clone <repo>
  cd marketplace
  python -m venv venv
  source venv/bin/activate  # or venv\Scripts\activate on Windows
  pip install -r requirements.txt
  python manage.py migrate
  python manage.py createsuperuser
  python manage.py runserver
  ```
- Initial commit: "Initial: Django project scaffold with models"

**Tests:**
- Verify Git tracks correct files
- Verify `.env` is not tracked
- Verify migrations are tracked
- Verify `__pycache__` is not tracked

**Acceptance Criteria:**
- [ ] `.gitignore` properly configured
- [ ] `CONTRIBUTING.md` created
- [ ] `README.md` has complete setup
- [ ] Initial commit made
- [ ] All team members can clone and run
- [ ] No large files or sensitive data in repo

**Mark as [✓ DONE] when:** Repo is clean, documented, and everyone can run it.

---

### WEEK 2: Authentication & Provider Signup Flow

#### TASK 2.1: Create Custom Authentication Backend (Email-Based Login)
**Status:** [✓ DONE] ✓

**Objective:** Implement email-based authentication instead of username.

**Requirements:**
- File: `users/backends.py`
- Create `EmailBackend` class that:
  - Authenticates using email instead of username
  - Accepts `email` and `password` parameters
  - Returns User object on success, None on failure
  - Case-insensitive email matching
- Register in `settings.py`:
  ```python
  AUTHENTICATION_BACKENDS = [
      'users.backends.EmailBackend',
  ]
  ```
- Update `User.REQUIRED_FIELDS` in custom user manager

**Tests:**
```python
def test_authenticate_with_email():
    user = User.objects.create_user(email='test@example.com', password='pass123')
    authenticated = authenticate(email='test@example.com', password='pass123')
    assert authenticated == user

def test_authenticate_wrong_password():
    User.objects.create_user(email='test@example.com', password='pass123')
    authenticated = authenticate(email='test@example.com', password='wrongpass')
    assert authenticated is None

def test_authenticate_nonexistent_user():
    authenticated = authenticate(email='nonexistent@example.com', password='pass')
    assert authenticated is None

def test_case_insensitive_email():
    User.objects.create_user(email='test@example.com', password='pass123')
    authenticated = authenticate(email='TEST@EXAMPLE.COM', password='pass123')
    assert authenticated is not None
```

**Acceptance Criteria:**
- [ ] EmailBackend authenticates with email/password
- [ ] Case-insensitive matching works
- [ ] Returns None for wrong credentials
- [ ] Registered in AUTHENTICATION_BACKENDS
- [ ] All tests pass

**Mark as [✓ DONE] when:** Authentication backend works with all test cases.

---

#### TASK 2.2: Create Email Verification Token & Utility Functions
**Status:** [✓ DONE] ✓

**Objective:** Implement email verification token generation and validation.

**Requirements:**
- File: `users/utils.py`
- Create function `generate_email_verification_token(user)`:
  - Generates URL-safe token unique to user
  - Stored in `user.email_verification_token`
  - Returns token string
  - Use Django's `django.utils.http` and `django.core.signing`
  
- Create function `verify_email_token(token)`:
  - Validates token format and expiration
  - Finds user by token
  - Returns User object or None
  - Invalidates token after use
  
- Create function `send_verification_email(user, request)`:
  - Generates token
  - Creates verification URL: `/auth/verify-email/{token}/`
  - Sends email to user (console output for development)
  - Returns True on success

**Tests:**
```python
def test_generate_verification_token():
    user = create_test_user()
    token = generate_email_verification_token(user)
    assert token is not None
    assert user.email_verification_token == token

def test_verify_email_token():
    user = create_test_user()
    token = generate_email_verification_token(user)
    verified_user = verify_email_token(token)
    assert verified_user == user
    assert user.is_email_verified == True
    assert user.email_verification_token == None

def test_verify_invalid_token():
    result = verify_email_token('invalid_token_xyz')
    assert result is None

def test_send_verification_email():
    user = create_test_user()
    result = send_verification_email(user, None)
    assert result == True
```

**Acceptance Criteria:**
- [ ] Token generation works
- [ ] Token validation works
- [ ] Tokens expire after use
- [ ] Email sending function created
- [ ] All tests pass

**Mark as [✓ DONE] when:** Token system works and emails can be sent.

---

#### TASK 2.3: Create Signup View & Form
**Status:** [✓ DONE] ✓

**Objective:** Implement provider signup view with form handling.

**Requirements:**
- File: `users/views.py`
- Create `SignupView` (Django TemplateView or FormView):
  - GET: Display signup form
  - POST: Handle form submission
  - Form fields: email, password, password_confirm, user_type
  - Validation:
    - Email must be unique
    - Password >= 8 characters
    - Passwords must match
  - On success:
    - Create User with `user_type='provider'`
    - Mark `is_email_verified=False`
    - Send verification email
    - Redirect to `/auth/check-email/` page
  - On error: Display form with errors

- File: `users/forms.py`
- Create `SignupForm` (Django Form):
  ```python
  class SignupForm(forms.Form):
      email = forms.EmailField()
      password = forms.CharField(widget=forms.PasswordInput)
      password_confirm = forms.CharField(widget=forms.PasswordInput)
      user_type = forms.ChoiceField(choices=[('provider', 'I am a provider')])
  ```

- File: `marketplace/urls.py`
- Add URL patterns:
  ```python
  path('auth/signup/', SignupView.as_view(), name='signup'),
  ```

**Tests:**
```python
def test_signup_form_valid():
    form = SignupForm(data={
        'email': 'new@example.com',
        'password': 'testpass123',
        'password_confirm': 'testpass123'
    })
    assert form.is_valid()

def test_signup_form_password_mismatch():
    form = SignupForm(data={
        'email': 'new@example.com',
        'password': 'testpass123',
        'password_confirm': 'different'
    })
    assert not form.is_valid()

def test_signup_view_creates_user():
    response = client.post('/auth/signup/', {
        'email': 'new@example.com',
        'password': 'testpass123',
        'password_confirm': 'testpass123'
    })
    assert User.objects.filter(email='new@example.com').exists()
    assert response.status_code == 302  # Redirect

def test_signup_duplicate_email():
    create_test_user(email='test@example.com')
    form = SignupForm(data={
        'email': 'test@example.com',
        'password': 'pass123',
        'password_confirm': 'pass123'
    })
    # Form should have error or view should prevent
    # Implement this in form clean() method
```

**Acceptance Criteria:**
- [ ] SignupForm validates correctly
- [ ] SignupView creates users
- [ ] Duplicate emails prevented
- [ ] Verification email sent
- [ ] Redirects to check-email page
- [ ] All tests pass

**Mark as [✓ DONE] when:** Users can sign up and receive verification emails.

---

#### TASK 2.4: Create Email Verification View
**Status:** [✓ DONE] ✓

**Objective:** Implement email verification endpoint.

**Requirements:**
- File: `users/views.py`
- Create `VerifyEmailView`:
  - GET: `/auth/verify-email/{token}/`
  - Calls `verify_email_token(token)`
  - If valid:
    - Mark user as verified
    - Set `is_email_verified=True`
    - Redirect to `/auth/login/` with success message
  - If invalid:
    - Render error template
    - Show message: "Token expired or invalid"
    - Link to request new verification email

- Create `CheckEmailView`:
  - GET: `/auth/check-email/`
  - Display message: "Check your email for verification link"
  - Option to resend email

- File: `marketplace/urls.py`
- Add patterns:
  ```python
  path('auth/verify-email/<str:token>/', VerifyEmailView.as_view(), name='verify_email'),
  path('auth/check-email/', CheckEmailView.as_view(), name='check_email'),
  ```

**Tests:**
```python
def test_verify_email_valid_token():
    user = create_test_user()
    token = generate_email_verification_token(user)
    response = client.get(f'/auth/verify-email/{token}/')
    user.refresh_from_db()
    assert user.is_email_verified == True
    assert response.status_code == 302  # Redirect

def test_verify_email_invalid_token():
    response = client.get('/auth/verify-email/invalid_token/')
    assert response.status_code == 200
    assert b'invalid' in response.content.lower()

def test_check_email_page_loads():
    response = client.get('/auth/check-email/')
    assert response.status_code == 200
    assert b'check your email' in response.content.lower()
```

**Acceptance Criteria:**
- [ ] Verify email view works with valid token
- [ ] Invalid tokens show error page
- [ ] Check email page displays
- [ ] Verified users can login
- [ ] All tests pass

**Mark as [✓ DONE] when:** Email verification flow complete.

---

#### TASK 2.5: Create Login View & Form
**Status:** [✓ DONE] ✓

**Objective:** Implement user login with email/password.

**Requirements:**
- File: `users/forms.py`
- Create `LoginForm`:
  ```python
  class LoginForm(forms.Form):
      email = forms.EmailField()
      password = forms.CharField(widget=forms.PasswordInput)
  ```

- File: `users/views.py`
- Create `LoginView` (FormView):
  - GET: Display login form
  - POST: Handle form submission
  - Use custom `authenticate(email=..., password=...)`
  - If authenticated:
    - Check if email is verified (if not, redirect to check-email)
    - Create session
    - Redirect to dashboard (determine based on user_type)
  - If not authenticated:
    - Display form with error: "Invalid email or password"

- File: `marketplace/urls.py`
- Add URL:
  ```python
  path('auth/login/', LoginView.as_view(), name='login'),
  ```

**Tests:**
```python
def test_login_form_valid():
    form = LoginForm(data={
        'email': 'test@example.com',
        'password': 'testpass123'
    })
    assert form.is_valid()

def test_login_view_authenticated():
    user = create_test_user()
    user.is_email_verified = True
    user.save()
    response = client.post('/auth/login/', {
        'email': 'test@example.com',
        'password': 'testpass123'
    })
    assert response.wsgi_request.user.is_authenticated
    assert response.status_code == 302

def test_login_unverified_email():
    user = create_test_user()
    # user.is_email_verified is False by default
    response = client.post('/auth/login/', {
        'email': 'test@example.com',
        'password': 'testpass123'
    })
    # Should redirect to check-email or show error
    assert response.status_code == 302

def test_login_invalid_credentials():
    response = client.post('/auth/login/', {
        'email': 'nonexistent@example.com',
        'password': 'wrongpass'
    })
    assert response.status_code == 200
    assert b'invalid' in response.content.lower()
```

**Acceptance Criteria:**
- [ ] LoginForm validates correctly
- [ ] Verified users can login
- [ ] Unverified users redirected to check-email
- [ ] Invalid credentials show error
- [ ] Session created on successful login
- [ ] All tests pass

**Mark as [✓ DONE] when:** Users can login with verified email.

---

#### TASK 2.6: Create Logout View & Password Reset
**Status:** [✓ DONE] ✓

**Objective:** Implement logout and password reset flows.

**Requirements:**
- File: `users/views.py`

**LogoutView:**
- POST: `/auth/logout/`
- Clears session
- Redirects to login page
- Success message: "You have been logged out"

**PasswordResetRequestView:**
- GET: `/auth/password-reset/`
- Display form asking for email
- POST: Sends password reset email with token

**PasswordResetForm:**
```python
class PasswordResetForm(forms.Form):
    email = forms.EmailField()
```

**PasswordResetConfirmView:**
- GET: `/auth/password-reset/{token}/`
- Display password change form
- POST: Validates new password, updates user, redirects to login

**PasswordResetConfirmForm:**
```python
class PasswordResetConfirmForm(forms.Form):
    password = forms.CharField(widget=forms.PasswordInput)
    password_confirm = forms.CharField(widget=forms.PasswordInput)
```

- File: `marketplace/urls.py`
- Add URLs:
  ```python
  path('auth/logout/', LogoutView.as_view(), name='logout'),
  path('auth/password-reset/', PasswordResetRequestView.as_view(), name='password_reset'),
  path('auth/password-reset/{token}/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
  ```

**Tests:**
```python
def test_logout_clears_session():
    user = create_test_user()
    user.is_email_verified = True
    user.save()
    client.post('/auth/login/', {...})
    response = client.post('/auth/logout/')
    assert not response.wsgi_request.user.is_authenticated

def test_password_reset_flow():
    user = create_test_user()
    response = client.post('/auth/password-reset/', {'email': user.email})
    # Check that token was generated
    user.refresh_from_db()
    assert user.password_reset_token is not None

def test_password_reset_confirm():
    user = create_test_user()
    token = generate_password_reset_token(user)
    response = client.post(f'/auth/password-reset/{token}/', {
        'password': 'newpass123',
        'password_confirm': 'newpass123'
    })
    # User should be able to login with new password
    user.refresh_from_db()
    assert user.check_password('newpass123')
```

**Acceptance Criteria:**
- [ ] Logout clears session
- [ ] Password reset email sent
- [ ] Password reset token validated
- [ ] New password can be set
- [ ] User can login with new password
- [ ] All tests pass

**Mark as [✓ DONE] when:** Full auth flow (signup → login → logout → reset) works.

---

#### TASK 2.7: Create Base Templates & Navigation
**Status:** [✓ DONE] ✓

**Objective:** Build HTML template structure with navigation.

**Requirements:**
- Directory: `marketplace/templates/`
- Create `base.html`:
  ```html
  <!DOCTYPE html>
  <html>
  <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <title>{% block title %}Massage Marketplace{% endblock %}</title>
      <link href="https://cdn.tailwindcss.com" rel="stylesheet">
  </head>
  <body class="bg-gray-50">
      <nav class="bg-white shadow">
          <div class="max-w-7xl mx-auto px-4">
              <div class="flex justify-between h-16">
                  <div class="flex items-center">
                      <a href="/" class="text-xl font-bold">Massage Marketplace</a>
                  </div>
                  <div class="flex items-center space-x-4">
                      {% if user.is_authenticated %}
                          <span>Hello, {{ user.email }}</span>
                          <a href="{% url 'dashboard' %}">Dashboard</a>
                          <a href="{% url 'logout' %}">Logout</a>
                      {% else %}
                          <a href="{% url 'login' %}">Login</a>
                          <a href="{% url 'signup' %}">Sign Up</a>
                      {% endif %}
                  </div>
              </div>
          </div>
      </nav>
      
      {% if messages %}
          <div class="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded">
              {% for message in messages %}
                  <p>{{ message }}</p>
              {% endfor %}
          </div>
      {% endif %}
      
      <div class="max-w-7xl mx-auto px-4 py-8">
          {% block content %}{% endblock %}
      </div>
  </body>
  </html>
  ```

- Create `auth/signup.html`:
  ```html
  {% extends "base.html" %}
  {% block title %}Sign Up - Massage Marketplace{% endblock %}
  {% block content %}
      <div class="max-w-md mx-auto bg-white p-8 rounded-lg shadow">
          <h2 class="text-2xl font-bold mb-6">Create Provider Account</h2>
          <form method="post">
              {% csrf_token %}
              {{ form.as_p }}
              <button type="submit" class="w-full bg-blue-600 text-white py-2 rounded">Sign Up</button>
          </form>
          <p class="mt-4">Already have an account? <a href="{% url 'login' %}">Login</a></p>
      </div>
  {% endblock %}
  ```

- Create `auth/login.html` (similar structure)
- Create `auth/check-email.html`
- Configure in `settings.py`:
  ```python
  TEMPLATES = [{
      'BACKEND': 'django.template.backends.django.DjangoTemplates',
      'DIRS': [BASE_DIR / 'marketplace' / 'templates'],
      'APP_DIRS': True,
  }]
  ```

**Tests:**
- [ ] Base template renders without errors
- [ ] Navigation shows login/signup for unauthenticated
- [ ] Navigation shows dashboard/logout for authenticated
- [ ] All auth templates render
- [ ] Messages display correctly

**Acceptance Criteria:**
- [ ] Base template created with navigation
- [ ] All auth templates created
- [ ] Responsive design (Tailwind)
- [ ] Messages and alerts working
- [ ] No broken links
- [ ] Mobile-friendly

**Mark as [✓ DONE] when:** Templates render and navigation works.

---

#### TASK 2.8: Create Provider Dashboard Skeleton
**Status:** [✓ DONE] ✓

**Objective:** Build dashboard view and template (populated in Week 3).

**Requirements:**
- File: `providers/views.py`
- Create `ProviderDashboardView`:
  - GET: `/provider/dashboard/`
  - Requires login
  - Requires user_type == 'provider'
  - Shows provider profile and services (to be implemented)
  - Template: `provider/dashboard.html`

- Middleware/Decorator: Create `provider_required` decorator:
  ```python
  def provider_required(view_func):
      def wrapper(request, *args, **kwargs):
          if request.user.user_type != 'provider':
              return redirect('login')
          return view_func(request, *args, **kwargs)
      return wrapper
  ```

- File: `marketplace/urls.py`
- Add URL:
  ```python
  path('provider/dashboard/', ProviderDashboardView.as_view(), name='dashboard'),
  ```

- File: `provider/dashboard.html`
- Create skeleton:
  ```html
  {% extends "base.html" %}
  {% block title %}Provider Dashboard{% endblock %}
  {% block content %}
      <div class="grid grid-cols-3 gap-6">
          <div class="col-span-2">
              <h2 class="text-2xl font-bold mb-4">Your Services</h2>
              <p>Services will be listed here</p>
          </div>
          <div>
              <h3 class="text-lg font-bold mb-4">Profile</h3>
              <p>Profile summary will appear here</p>
          </div>
      </div>
  {% endblock %}
  ```

**Tests:**
```python
def test_dashboard_requires_login():
    response = client.get('/provider/dashboard/')
    assert response.status_code == 302  # Redirect to login

def test_dashboard_loads_for_provider():
    user = create_test_user(user_type='provider')
    user.is_email_verified = True
    user.save()
    client.login(email=user.email, password='testpass123')
    response = client.get('/provider/dashboard/')
    assert response.status_code == 200

def test_provider_required_decorator():
    client_user = create_test_user(user_type='client')
    client_user.is_email_verified = True
    client_user.save()
    # Attempting to access provider dashboard should redirect
    response = client.get('/provider/dashboard/')
    # Should be redirected since user_type is 'client'
```

**Acceptance Criteria:**
- [ ] Dashboard view created and protected
- [ ] Provider decorator works
- [ ] Non-providers cannot access
- [ ] Dashboard template renders
- [ ] Skeleton ready for Week 3 work

**Mark as [✓ DONE] when:** Dashboard accessible to authenticated providers only.

---

#### TASK 2.9: Create Authentication Tests & Email Configuration
**Status:** [✓ DONE] ✓

**Objective:** Complete authentication testing and setup email in development.

**Requirements:**
- File: `users/tests.py`
- Write comprehensive tests for:
  - User creation and validation
  - Email backend authentication
  - Token generation and verification
  - Signup flow end-to-end
  - Login flow with verified/unverified users
  - Logout
  - Password reset
- File: `settings.py`
- Configure email for development:
  ```python
  EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
  EMAIL_HOST = 'smtp.gmail.com'
  EMAIL_PORT = 587
  EMAIL_USE_TLS = True
  EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
  EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
  DEFAULT_FROM_EMAIL = 'noreply@massagemarketplace.com'
  ```
- File: `.env.example`
- Add:
  ```
  EMAIL_HOST_USER=your_email@gmail.com
  EMAIL_HOST_PASSWORD=your_app_password
  ```

**Tests:**
- Run full test suite: `pytest users/ -v`
- All tests should pass

**Acceptance Criteria:**
- [ ] 20+ authentication tests written
- [ ] All tests pass
- [ ] Email backend configured
- [ ] Console email output working
- [ ] Test coverage > 85% for users app

**Mark as [✓ DONE] when:** Auth tests comprehensive and email configured.

---

### WEEK 3: Provider Profile & Service Management

#### TASK 3.1: Create Provider Profile Update View & Form
**Status:** [✓ DONE] ✓

**Objective:** Build form to edit provider profile (name, bio, phone, photo).

**Requirements:**
- File: `providers/forms.py`
- Create `ProviderProfileForm`:
  ```python
  class ProviderProfileForm(forms.ModelForm):
      class Meta:
          model = Provider
          fields = ['bio', 'phone', 'photo']
      # Add validation: phone must be 10+ digits
  ```

- File: `providers/views.py`
- Create `ProviderProfileUpdateView`:
  - GET: `/provider/profile/edit/`
  - Display pre-filled form with current data
  - POST: Save changes
  - Show validation errors on failure
  - Redirect to profile view on success
  - Decorator: `@provider_required`

- File: `marketplace/urls.py`
- Add URL:
  ```python
  path('provider/profile/edit/', ProviderProfileUpdateView.as_view(), name='profile_edit'),
  ```

- File: `provider/profile_edit.html`
- Create form template with image preview

**Tests:**
```python
def test_profile_form_valid():
    form = ProviderProfileForm(data={
        'bio': 'Licensed massage therapist',
        'phone': '+1234567890'
    })
    assert form.is_valid()

def test_profile_update_view():
    user = create_test_user(user_type='provider')
    provider = Provider.objects.get(user=user)
    response = client.post('/provider/profile/edit/', {
        'bio': 'New bio',
        'phone': '+9876543210'
    })
    provider.refresh_from_db()
    assert provider.bio == 'New bio'

def test_profile_photo_upload():
    # Test image file upload
    pass
```

**Acceptance Criteria:**
- [ ] ProfileForm created and validated
- [ ] Profile update view working
- [ ] Phone validation works
- [ ] Form displays current values
- [ ] Changes saved to database
- [ ] All tests pass

**Mark as [✓ DONE] when:** Provider can update profile information.

---

#### TASK 3.2: Create Provider Photo Upload & Storage
**Status:** [✓ DONE] ✓

**Objective:** Implement image upload with validation and local storage.

**Requirements:**
- File: `providers/models.py` (update)
- Ensure `photo` field in Provider model:
  ```python
  photo = models.ImageField(upload_to='providers/photos/', blank=True, null=True)
  ```

- File: `settings.py`
- Configure media handling:
  ```python
  MEDIA_URL = '/media/'
  MEDIA_ROOT = BASE_DIR / 'media'
  ```

- File: `marketplace/urls.py` (development)
- Add media serving (development only):
  ```python
  from django.conf import settings
  if settings.DEBUG:
      urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
  ```

- File: `providers/forms.py`
- Add image validation to form:
  ```python
  def clean_photo(self):
      photo = self.cleaned_data.get('photo')
      if photo:
          # Check file size < 5MB
          if photo.size > 5 * 1024 * 1024:
              raise ValidationError("Image must be < 5MB")
          # Check file format (JPEG, PNG, GIF)
          if not photo.content_type in ['image/jpeg', 'image/png', 'image/gif']:
              raise ValidationError("Only JPEG, PNG, GIF allowed")
      return photo
  ```

- Create image processing (resize):
  ```python
  from PIL import Image
  
  def save(self, *args, **kwargs):
      super().save(*args, **kwargs)
      if self.photo:
          # Resize image to max 800x800
          img = Image.open(self.photo.path)
          if img.height > 800 or img.width > 800:
              img.thumbnail((800, 800))
              img.save(self.photo.path)
  ```

**Tests:**
```python
def test_photo_upload():
    provider = create_test_provider()
    # Create test image
    from PIL import Image
    import io
    img = Image.new('RGB', (100, 100))
    img_io = io.BytesIO()
    img.save(img_io, 'JPEG')
    img_io.seek(0)
    
    provider.photo.save('test.jpg', img_io)
    provider.save()
    assert provider.photo.name.startswith('providers/photos/')

def test_photo_size_limit():
    # Test that oversized images are rejected
    pass

def test_photo_format_validation():
    # Test that invalid formats are rejected
    pass
```

**Acceptance Criteria:**
- [ ] Photo upload working
- [ ] File size validation (< 5MB)
- [ ] Format validation (JPEG, PNG, GIF)
- [ ] Images resized to max 800x800
- [ ] Media URL configured
- [ ] Photos accessible via URL
- [ ] All tests pass

**Mark as [✓ DONE] when:** Users can upload and view profile photos.

---

#### TASK 3.3: Create Certification Upload View
**Status:** [✓ DONE] ✓

**Objective:** Build form to upload and manage certifications.

**Requirements:**
- File: `providers/forms.py`
- Create `CertificationForm`:
  ```python
  class CertificationForm(forms.ModelForm):
      class Meta:
          model = Certification
          fields = ['name', 'image']
  ```

- File: `providers/views.py`
- Create `CertificationCreateView`:
  - GET/POST: `/provider/certifications/add/`
  - Form for name and image
  - Save certification
  - Redirect to profile
  - Decorator: `@provider_required`

- Create `CertificationDeleteView`:
  - POST: `/provider/certifications/{id}/delete/`
  - Only owner can delete
  - Redirect to profile

- Create `CertificationListView`:
  - Display on dashboard
  - Show all provider's certifications with delete buttons

- File: `marketplace/urls.py`
- Add URLs:
  ```python
  path('provider/certifications/add/', CertificationCreateView.as_view(), name='add_certification'),
  path('provider/certifications/<int:id>/delete/', CertificationDeleteView.as_view(), name='delete_certification'),
  ```

**Tests:**
```python
def test_add_certification():
    provider = create_test_provider()
    # Upload test image
    response = client.post('/provider/certifications/add/', {
        'name': 'Licensed Massage Therapist',
        'image': test_image_file
    })
    assert Certification.objects.filter(provider=provider).exists()

def test_delete_certification():
    cert = create_test_certification()
    response = client.post(f'/provider/certifications/{cert.id}/delete/')
    assert not Certification.objects.filter(id=cert.id).exists()

def test_certification_ownership():
    provider1 = create_test_provider()
    provider2 = create_test_provider()
    cert = Certification.objects.create(provider=provider1, name='LMT')
    # Provider2 should not be able to delete provider1's cert
    # Test this
```

**Acceptance Criteria:**
- [ ] Certification upload form working
- [ ] Multiple certifications per provider
- [ ] Delete functionality working
- [ ] Ownership verification works
- [ ] Images stored correctly
- [ ] All tests pass

**Mark as [✓ DONE] when:** Providers can upload and manage certifications.

---

#### TASK 3.4: Create Service CRUD Views
**Status:** [✓ DONE] ✓

**Objective:** Build complete Create, Read, Update, Delete for services.

**Requirements:**
- File: `providers/forms.py`
- Create `ServiceForm`:
  ```python
  class ServiceForm(forms.ModelForm):
      class Meta:
          model = Service
          fields = ['service_type', 'description', 'price', 'duration_minutes']
  ```

- File: `providers/views.py`
- Create `ServiceCreateView`:
  - GET/POST: `/provider/services/create/`
  - Form for service details
  - Decorator: `@provider_required`
  - Redirect to dashboard on success

- Create `ServiceUpdateView`:
  - GET/POST: `/provider/services/{id}/edit/`
  - Pre-fill form with current values
  - Only owner can edit
  - Decorator: `@provider_required`

- Create `ServiceDeleteView`:
  - POST: `/provider/services/{id}/delete/`
  - Confirmation page before delete
  - Only owner can delete
  - Decorator: `@provider_required`

- Create `ServiceListView`:
  - GET: `/provider/services/`
  - List all provider's services with edit/delete buttons

- File: `marketplace/urls.py`
- Add URLs:
  ```python
  path('provider/services/', ServiceListView.as_view(), name='services_list'),
  path('provider/services/create/', ServiceCreateView.as_view(), name='service_create'),
  path('provider/services/<int:id>/edit/', ServiceUpdateView.as_view(), name='service_edit'),
  path('provider/services/<int:id>/delete/', ServiceDeleteView.as_view(), name='service_delete'),
  ```

- File: `provider/service_form.html` (create/edit)
- File: `provider/service_list.html`

**Tests:**
```python
def test_create_service():
    provider = create_test_provider()
    response = client.post('/provider/services/create/', {
        'service_type': 'swedish',
        'description': 'Swedish massage',
        'price': '75.00',
        'duration_minutes': 60
    })
    assert Service.objects.filter(provider=provider).exists()

def test_service_price_validation():
    # Price must be >= 5.00
    form = ServiceForm(data={
        'service_type': 'swedish',
        'price': '3.00',
        'duration_minutes': 60
    })
    assert not form.is_valid()

def test_edit_service():
    service = create_test_service()
    response = client.post(f'/provider/services/{service.id}/edit/', {
        'price': '85.00'
    })
    service.refresh_from_db()
    assert service.price == 85.00

def test_delete_service():
    service = create_test_service()
    response = client.post(f'/provider/services/{service.id}/delete/')
    assert not Service.objects.filter(id=service.id).exists()

def test_service_ownership():
    # Only owner can edit/delete
    pass
```

**Acceptance Criteria:**
- [ ] Create service working
- [ ] Edit service working
- [ ] Delete service working
- [ ] Service list displays all services
- [ ] Ownership verification works
- [ ] Validation for price and duration works
- [ ] All tests pass

**Mark as [✓ DONE] when:** Full service CRUD operational.

---

#### TASK 3.5: Create Provider Dashboard Display
**Status:** [✓ DONE] ✓

**Objective:** Populate dashboard with profile and services overview.

**Requirements:**
- File: `providers/views.py`
- Update `ProviderDashboardView`:
  - Fetch provider profile
  - Fetch all provider's services
  - Fetch provider's average rating
  - Pass to template

- File: `provider/dashboard.html`
- Display:
  - Provider name, phone, bio, photo
  - Edit profile link
  - List of services (show/edit/delete)
  - Add new service button
  - Certifications with add/delete
  - Add certification button
  - Summary stats:
    - Number of services
    - Average rating
    - Total reviews

**Template Layout:**
```html
{% extends "base.html" %}
{% block content %}
    <div class="grid grid-cols-3 gap-6">
        <!-- Left: Services -->
        <div class="col-span-2">
            <h2 class="text-2xl font-bold mb-4">Your Services</h2>
            <!-- Service list with edit/delete -->
            <button>+ Add Service</button>
        </div>
        
        <!-- Right: Profile -->
        <div>
            <h3 class="text-lg font-bold mb-4">Profile</h3>
            <img src="{{ provider.photo.url }}" alt="">
            <p>{{ provider.user.email }}</p>
            <p>{{ provider.phone }}</p>
            <p>{{ provider.bio }}</p>
            <button>Edit Profile</button>
            
            <h4 class="text-md font-bold mt-6">Certifications</h4>
            <!-- List certifications -->
            <button>+ Add Certification</button>
            
            <div class="mt-6 p-4 bg-gray-100 rounded">
                <p>Rating: {{ provider.average_rating }}/5</p>
                <p>Reviews: {{ provider.reviews.count }}</p>
                <p>Services: {{ provider.services.count }}</p>
            </div>
        </div>
    </div>
{% endblock %}
```

**Tests:**
```python
def test_dashboard_shows_provider_info():
    provider = create_test_provider()
    provider.bio = "Expert massage therapist"
    provider.save()
    response = client.get('/provider/dashboard/')
    assert b"Expert massage therapist" in response.content

def test_dashboard_shows_services():
    provider = create_test_provider()
    service = Service.objects.create(provider=provider, service_type='swedish', price=75)
    response = client.get('/provider/dashboard/')
    assert b"swedish" in response.content.lower()

def test_dashboard_stats():
    provider = create_test_provider()
    Service.objects.create(provider=provider, service_type='swedish', price=75)
    Review.objects.create(provider=provider, rating=5, comment="Great")
    response = client.get('/provider/dashboard/')
    # Should show 1 service, 1 review, etc.
```

**Acceptance Criteria:**
- [ ] Dashboard displays provider info
- [ ] Dashboard shows all services
- [ ] Dashboard shows certifications
- [ ] Dashboard shows stats (services, rating, reviews)
- [ ] All links work (edit profile, edit service, add service, etc.)
- [ ] Responsive layout on mobile
- [ ] All tests pass

**Mark as [✓ DONE] when:** Dashboard fully functional with all provider info displayed.

---

#### TASK 3.6: Update Migrations & Run Locally
**Status:** [✓ DONE] ✓

**Objective:** Create and apply all database migrations.

**Requirements:**
- Run: `python manage.py makemigrations`
- Run: `python manage.py migrate`
- Verify no errors
- Create test fixtures:
  ```bash
  python manage.py shell
  >>> from tests.helpers import *
  >>> provider = create_test_provider()
  >>> service = create_test_service(provider)
  ```

- Verify all views load:
  - `/provider/dashboard/` - loads
  - `/provider/profile/edit/` - loads
  - `/provider/services/` - loads
  - `/provider/services/create/` - loads

**Tests:**
- `pytest providers/ -v`
- All tests pass

**Acceptance Criteria:**
- [ ] All migrations created and applied
- [ ] No migration errors
- [ ] Test data can be created
- [ ] All views load without errors
- [ ] All models working in shell
- [ ] Database is clean and ready

**Mark as [✓ DONE] when:** Migrations applied and all views working locally.

---

#### TASK 3.7: Refactor & DRY Templates
**Status:** [✓ DONE] ✓

**Objective:** Improve template consistency and reduce duplication.

**Requirements:**
- Create `includes/`:
  - `_form.html` (generic form rendering)
  - `_service_card.html` (service display component)
  - `_certification_card.html`
  - `_messages.html` (alerts)
  - `_pagination.html`

- Update templates to use includes:
  - `provider/dashboard.html`
  - `provider/service_form.html`
  - `provider/service_list.html`
  - All other templates

- Ensure consistent styling (Tailwind classes)
- Create `static/css/custom.css` if needed

**Tests:**
- Template rendering tests
- No broken includes
- All pages load without template errors

**Acceptance Criteria:**
- [ ] Templates DRY (no duplication)
- [ ] Includes created and used
- [ ] Consistent styling across all pages
- [ ] No template errors
- [ ] Code review approved

**Mark as [✓ DONE] when:** Templates refactored and consistent.

---

#### TASK 3.8: Create Comprehensive Tests & Documentation
**Status:** [✓ DONE] ✓

**Objective:** Full test coverage for Week 3 work, update documentation.

**Requirements:**
- Run: `pytest providers/ -v --cov=providers`
- Aim for >85% code coverage
- Document:
  - Update `CONTRIBUTING.md` with testing instructions
  - Create `docs/PROVIDER_FLOWS.md`:
    - Signup flow
    - Profile completion
    - Service creation
    - Certification upload
  - Create `docs/DATABASE_SCHEMA.md` with ER diagram (ASCII)

**Tests:**
- Test coverage > 85%
- All critical paths tested
- Edge cases covered

**Acceptance Criteria:**
- [ ] All Week 3 code tested
- [ ] Coverage > 85%
- [ ] Documentation updated
- [ ] CONTRIBUTING.md current
- [ ] Flows documented
- [ ] All tests passing

**Mark as [✓ DONE] when:** Tests comprehensive and docs updated.

---

### WEEK 4: Django Admin Extensions & Subscription Basics

#### TASK 4.1: Extend Django Admin with Custom Filters
**Status:** [✓ DONE] ✓

**Objective:** Build advanced admin interface for provider management.

**Requirements:**
- File: `providers/admin.py`
- Create custom admin classes:

**ProviderAdmin:**
```python
class ProviderAdmin(admin.ModelAdmin):
    list_display = ('user_email', 'phone', 'subscription_status', 'created_at')
    search_fields = ('user__email', 'phone')
    list_filter = ('subscription_status', 'subscription_payment_method', 'created_at')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('User', {'fields': ('user',)}),
        ('Contact', {'fields': ('phone', 'bio')}),
        ('Media', {'fields': ('photo',)}),
        ('Subscription', {'fields': (
            'subscription_status',
            'subscription_payment_method',
            'subscription_renewal_date'
        )}),
        ('Crypto', {'fields': ('crypto_address',)}),
        ('Dates', {'fields': ('created_at', 'updated_at')}),
    )
    inlines = [ServiceInline, CertificationInline]
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Email'
    
    actions = ['deactivate_subscriptions', 'suspend_accounts']
    
    def deactivate_subscriptions(self, request, queryset):
        queryset.update(subscription_status='inactive')
    
    def suspend_accounts(self, request, queryset):
        queryset.update(subscription_status='suspended')
```

**ServiceInline:**
```python
class ServiceInline(admin.TabularInline):
    model = Service
    extra = 1
    fields = ('service_type', 'price', 'duration_minutes', 'is_active')
```

**CertificationInline:**
```python
class CertificationInline(admin.TabularInline):
    model = Certification
    extra = 1
    fields = ('name', 'image')
```

- Register in admin.site

**Tests:**
```python
def test_provider_admin_list_display():
    # Navigate to admin and verify columns show
    pass

def test_admin_search_by_email():
    # Test search functionality
    pass

def test_admin_filter_by_status():
    # Test filters work
    pass

def test_admin_actions():
    # Test bulk actions (deactivate, suspend)
    pass
```

**Acceptance Criteria:**
- [ ] ProviderAdmin configured with list_display
- [ ] Search fields working
- [ ] Filters functional
- [ ] Inline Services and Certifications editable
- [ ] Bulk actions working
- [ ] Admin can navigate easily
- [ ] All tests pass

**Mark as [✓ DONE] when:** Admin interface fully configured and functional.

---

#### TASK 4.2: Create Provider List View (Internal)
**Status:** [✓ DONE] ✓

**Objective:** Build internal provider management page (precursor to payment management).

**Requirements:**
- File: `providers/views.py`
- Create `AdminProviderListView`:
  - GET: `/admin/providers/`
  - Requires admin login
  - Display table of all providers:
    - Email, Phone, Status, Services count, Rating
    - Links to edit/delete/suspend
  - Pagination (50 per page)
  - Search by email
  - Filter by status
  - Decorator: `@admin_required`

- File: `marketplace/urls.py`
- Add URL:
  ```python
  path('admin/providers/', AdminProviderListView.as_view(), name='admin_providers'),
  ```

- File: `admin/provider_list.html`
- Create table with:
  - Provider info
  - Subscription status
  - Action buttons

**Tests:**
```python
def test_admin_provider_list():
    admin_user = create_test_admin()
    client.login(email=admin_user.email, password='pass')
    response = client.get('/admin/providers/')
    assert response.status_code == 200

def test_non_admin_cannot_access():
    provider = create_test_provider()
    response = client.get('/admin/providers/')
    assert response.status_code == 302  # Redirect
```

**Acceptance Criteria:**
- [ ] Admin provider list page loads
- [ ] Search/filter working
- [ ] All providers displayed
- [ ] Non-admins cannot access
- [ ] Pagination working
- [ ] All tests pass

**Mark as [✓ DONE] when:** Admin can manage providers from internal page.

---

#### TASK 4.3: Create Subscription Settings Page (UI Only)
**Status:** [✓ DONE] ✓

**Objective:** Build provider subscription management interface (payment logic in Week 10).

**Requirements:**
- File: `providers/views.py`
- Create `ProviderSubscriptionView`:
  - GET: `/provider/subscription/`
  - Display current subscription status
  - Display subscription renewal date
  - Show payment method options (radio buttons)
  - Decorator: `@provider_required`

- File: `providers/forms.py`
- Create `SubscriptionSettingsForm` (basic, no payment logic yet):
  ```python
  class SubscriptionSettingsForm(forms.Form):
      payment_method = forms.ChoiceField(
          choices=[
              ('crypto_bitcoin', 'Bitcoin'),
              ('crypto_ethereum', 'Ethereum'),
              ('crypto_usdc', 'USDC'),
              ('bank_transfer', 'Bank Transfer'),
          ],
          widget=forms.RadioSelect
      )
  ```

- File: `marketplace/urls.py`
- Add URL:
  ```python
  path('provider/subscription/', ProviderSubscriptionView.as_view(), name='subscription'),
  ```

- File: `provider/subscription.html`
- Create form with:
  - Current status display
  - Renewal date display
  - Payment method selection
  - Submit button (to be functional in Week 10)

**Template Structure:**
```html
{% extends "base.html" %}
{% block content %}
    <div class="max-w-2xl mx-auto">
        <h2 class="text-2xl font-bold mb-6">Subscription Settings</h2>
        
        <div class="bg-white p-6 rounded-lg shadow mb-6">
            <h3 class="text-lg font-bold mb-4">Current Status</h3>
            <p>Status: <span class="font-bold">{{ provider.get_subscription_status_display }}</span></p>
            {% if provider.subscription_renewal_date %}
                <p>Renewal Date: {{ provider.subscription_renewal_date }}</p>
            {% endif %}
        </div>
        
        <form method="post" class="bg-white p-6 rounded-lg shadow">
            {% csrf_token %}
            <h3 class="text-lg font-bold mb-4">Select Payment Method</h3>
            {{ form.payment_method }}
            <button type="submit" class="mt-6 bg-blue-600 text-white px-4 py-2 rounded">
                Continue to Payment
            </button>
        </form>
    </div>
{% endblock %}
```

**Tests:**
```python
def test_subscription_view_loads():
    provider = create_test_provider()
    response = client.get('/provider/subscription/')
    assert response.status_code == 200

def test_subscription_form_choices():
    form = SubscriptionSettingsForm()
    assert len(form.fields['payment_method'].choices) == 4

def test_requires_provider_login():
    response = client.get('/provider/subscription/')
    assert response.status_code == 302  # Redirect to login
```

**Acceptance Criteria:**
- [ ] Subscription page loads
- [ ] Current status displayed
- [ ] Renewal date shown (if active)
- [ ] Payment method selection form working
- [ ] Form choices correct
- [ ] Requires provider login
- [ ] All tests pass

**Mark as [✓ DONE] when:** Subscription UI page complete (functionality added in Week 10).

---

#### TASK 4.4: Create Subscribe/Unsubscribe Logic
**Status:** [✓ DONE] ✓

**Objective:** Implement subscription activation/deactivation.

**Requirements:**
- File: `providers/models.py` (update Provider model)
- Add method:
  ```python
  def activate_subscription(self, payment_method):
      """Activate subscription for 30 days from today"""
      self.subscription_status = 'active'
      self.subscription_payment_method = payment_method
      self.subscription_renewal_date = now() + timedelta(days=30)
      self.save()
  
  def deactivate_subscription(self):
      """Deactivate subscription"""
      self.subscription_status = 'inactive'
      self.save()
  
  def is_subscription_active(self):
      return self.subscription_status == 'active'
  ```

- File: `providers/views.py`
- Update `ProviderSubscriptionView` POST handler:
  - Get payment_method from form
  - Create SubscriptionPayment record (status='pending')
  - Call `provider.activate_subscription(payment_method)`
  - Save crypto_address if payment_method is crypto
  - Redirect to payment confirmation page
  - Send confirmation email

- File: `provider/subscription_confirm.html`
- Display:
  - Subscription activated message
  - Renewal date
  - Next steps based on payment method

**Tests:**
```python
def test_activate_subscription():
    provider = create_test_provider()
    provider.activate_subscription('crypto_bitcoin')
    assert provider.subscription_status == 'active'
    assert provider.subscription_renewal_date is not None

def test_deactivate_subscription():
    provider = create_test_provider()
    provider.activate_subscription('crypto_bitcoin')
    provider.deactivate_subscription()
    assert provider.subscription_status == 'inactive'

def test_subscription_activation_flow():
    response = client.post('/provider/subscription/', {
        'payment_method': 'crypto_bitcoin'
    })
    # Provider subscription should be active
    # SubscriptionPayment record created
    # Confirmation page should load
```

**Acceptance Criteria:**
- [ ] activate_subscription() method works
- [ ] deactivate_subscription() method works
- [ ] Subscription status tracked correctly
- [ ] Renewal date calculated (30 days)
- [ ] SubscriptionPayment record created
- [ ] Confirmation email sent
- [ ] All tests pass

**Mark as [✓ DONE] when:** Providers can activate/deactivate subscriptions.

---

#### TASK 4.5: Create Payment Admin View (Crypto & Bank)
**Status:** [✓ DONE] ✓

**Objective:** Build admin interface for payment verification queue.

**Requirements:**
- File: `payments/views.py`
- Create `AdminPaymentListView`:
  - GET: `/admin/payments/`
  - Display all pending payments
  - Columns: Provider, Amount, Payment Method, Date, Status
  - Filter by status (pending, completed, failed)
  - Filter by payment_method
  - Link to payment detail view
  - Decorator: `@admin_required`

- Create `AdminPaymentDetailView`:
  - GET: `/admin/payments/{id}/`
  - Display payment details
  - Show provider info
  - Show payment info
  - Buttons to approve/reject (Week 10)
  - For crypto: Show transaction hash entry field
  - For bank: Show bank details confirmation

- File: `marketplace/urls.py`
- Add URLs:
  ```python
  path('admin/payments/', AdminPaymentListView.as_view(), name='admin_payments'),
  path('admin/payments/<int:id>/', AdminPaymentDetailView.as_view(), name='admin_payment_detail'),
  ```

- File: `admin/payment_list.html` and `admin/payment_detail.html`

**Tests:**
```python
def test_payment_list_loads():
    admin_user = create_test_admin()
    client.login(email=admin_user.email, password='pass')
    response = client.get('/admin/payments/')
    assert response.status_code == 200

def test_payment_list_shows_pending():
    admin_user = create_test_admin()
    payment = create_test_payment(status='pending')
    client.login(email=admin_user.email, password='pass')
    response = client.get('/admin/payments/')
    assert payment.provider.user.email.encode() in response.content

def test_payment_detail_loads():
    payment = create_test_payment()
    response = client.get(f'/admin/payments/{payment.id}/')
    assert response.status_code == 200
```

**Acceptance Criteria:**
- [ ] Payment list page loads
- [ ] Pending payments displayed
- [ ] Filtering by status works
- [ ] Payment detail page works
- [ ] Only admins can access
- [ ] All tests pass

**Mark as [✓ DONE] when:** Admin payment queue operational.

---

#### TASK 4.6: Create Payment Confirmation Email
**Status:** [✓ DONE] ✓

**Objective:** Build email templates for subscription confirmations.

**Requirements:**
- File: `marketplace/templates/emails/subscription_confirmation.txt`
- File: `marketplace/templates/emails/subscription_confirmation.html`

**Email Content:**
```
Subject: Subscription Activated - Massage Marketplace

Hi {{ provider.user.email }},

Your subscription to Massage Marketplace has been activated!

Subscription Details:
- Amount: ${{ amount }}/month
- Payment Method: {{ payment_method_display }}
- Renewal Date: {{ renewal_date }}

{% if payment_method == 'crypto' %}
Your payment address: {{ crypto_address }}
Please send {{ amount }} to this address by {{ due_date }}.
{% endif %}

{% if payment_method == 'bank_transfer' %}
We will contact you with bank transfer instructions.
{% endif %}

Your services are now visible to clients!

Best regards,
The Massage Marketplace Team
```

- File: `providers/views.py`
- Update `activate_subscription()` to send email:
  ```python
  from django.core.mail import send_mail
  from django.template.loader import render_to_string
  
  def send_subscription_confirmation(provider, payment_method):
      html_message = render_to_string('emails/subscription_confirmation.html', {
          'provider': provider,
          'amount': 29.99,
          'payment_method_display': get_payment_method_display(payment_method),
          'renewal_date': provider.subscription_renewal_date,
      })
      send_mail(
          'Subscription Activated - Massage Marketplace',
          '',
          'noreply@massagemarketplace.com',
          [provider.user.email],
          html_message=html_message,
      )
  ```

**Tests:**
```python
def test_subscription_email_sent():
    # Mock email backend
    with patch('django.core.mail.send_mail') as mock_send:
        provider = create_test_provider()
        send_subscription_confirmation(provider, 'crypto_bitcoin')
        mock_send.assert_called_once()
        args = mock_send.call_args
        assert provider.user.email in args[0][3]  # recipients list

def test_email_contains_crypto_address():
    # If crypto payment, email should include address
    pass
```

**Acceptance Criteria:**
- [ ] Email templates created
- [ ] HTML and plain text versions
- [ ] Email sent on subscription activation
- [ ] Email contains correct details
- [ ] All tests pass

**Mark as [✓ DONE] when:** Subscription confirmation emails working.

---

#### TASK 4.7: Create Comprehensive Admin Testing
**Status:** [✓ DONE] ✓

**Objective:** Full test coverage for admin features.

**Requirements:**
- Write tests for:
  - Admin authentication
  - Admin provider list/detail views
  - Admin payment list/detail views
  - Admin filters and search
  - Provider bulk actions
  - All admin forms

- File: `tests/test_admin.py`
- Test coverage > 90% for admin views

**Tests:**
- `pytest tests/test_admin.py -v --cov=...`

**Acceptance Criteria:**
- [ ] All admin views tested
- [ ] Coverage > 90%
- [ ] All critical paths covered
- [ ] Edge cases tested
- [ ] All tests passing

**Mark as [✓ DONE] when:** Admin functionality fully tested.

---

#### TASK 4.8: Sprint 1 Completion & Documentation
**Status:** [✓ DONE] ✓

**Objective:** Finalize Sprint 1, document progress, prepare for Sprint 2.

**Requirements:**
- Update `README.md`:
  - Sprint 1 completion date
  - Current features list
  - Next steps
  
- Update `CONTRIBUTING.md`:
  - Current codebase status
  - Developer setup instructions
  - Testing procedures
  
- Create `docs/ARCHITECTURE.md`:
  - High-level architecture
  - App structure
  - Data flow
  
- Create `docs/SPRINT1_SUMMARY.md`:
  - What was built
  - What works
  - Known limitations
  - Ready for Sprint 2

- Final test run: `pytest -v`
- All tests passing
- No warnings or errors

- Git commit: "Sprint 1 complete: Provider portal with auth, profiles, services"

**Acceptance Criteria:**
- [ ] README updated
- [ ] CONTRIBUTING.md current
- [ ] Architecture documented
- [ ] Sprint summary written
- [ ] All tests passing
- [ ] Clean git history
- [ ] Code review approved

**Mark as [✓ DONE] when:** Sprint 1 documentation complete and team ready for Sprint 2.

---

## SPRINT 2: Marketplace & Core Features

### WEEK 5: Client Marketplace - Provider Directory

#### TASK 5.1: Create Public Provider List View (No Auth Required)
**Status:** [✓ DONE] ✓

**Objective:** Build public provider directory accessible to anyone.

**Requirements:**
- File: `clients/views.py` (create new app)
- Create `ProviderDirectoryView`:
  - GET: `/providers/` (or just `/`)
  - No authentication required
  - Display all providers with subscription_status == 'active'
  - Paginate: 20 providers per page
  - Show provider cards with:
    - Photo
    - Name
    - Average rating (stars)
    - Number of services
    - Link to provider detail page

- File: `clients/models.py`
- Create helper method on Provider:
  ```python
  def average_rating(self):
      from django.db.models import Avg
      avg = self.reviews.aggregate(Avg('rating'))['rating__avg']
      return round(avg, 1) if avg else 0
  
  def is_active_subscription(self):
      return self.subscription_status == 'active'
  ```

- File: `marketplace/urls.py`
- Add URL:
  ```python
  path('providers/', ProviderDirectoryView.as_view(), name='providers'),
  path('', ProviderDirectoryView.as_view(), name='home'),
  ```

- File: `clients/provider_list.html`
- Create card template

**Tests:**
```python
def test_provider_directory_loads():
    response = client.get('/providers/')
    assert response.status_code == 200

def test_provider_list_shows_active_only():
    active = create_test_provider()
    active.subscription_status = 'active'
    active.save()
    
    inactive = create_test_provider()
    inactive.subscription_status = 'inactive'
    inactive.save()
    
    response = client.get('/providers/')
    assert active.user.email.encode() in response.content
    assert inactive.user.email.encode() not in response.content

def test_provider_card_shows_info():
    provider = create_test_provider()
    provider.subscription_status = 'active'
    provider.save()
    
    Review.objects.create(provider=provider, rating=5)
    Review.objects.create(provider=provider, rating=4)
    
    response = client.get('/providers/')
    # Should show rating and name
    assert b'4.5' in response.content or b'4' in response.content

def test_pagination_works():
    # Create 25 providers
    for i in range(25):
        p = create_test_provider()
        p.subscription_status = 'active'
        p.save()
    
    response = client.get('/providers/')
    assert b'Page 1' in response.content or b'next' in response.content.lower()
```

**Acceptance Criteria:**
- [ ] Provider list page loads (no auth required)
- [ ] Only active providers shown
- [ ] Provider cards display correctly
- [ ] Pagination working (20 per page)
- [ ] No auth required
- [ ] All tests pass

**Mark as [✓ DONE] when:** Public provider directory accessible.

---

#### TASK 5.2: Create Provider Detail View (Public Profile)
**Status:** [✓ DONE] ✓

**Objective:** Build public provider profile page.

**Requirements:**
- File: `clients/views.py`
- Create `ProviderDetailView`:
  - GET: `/providers/{id}/` or `/providers/{slug}/`
  - Display provider profile:
    - Photo, name, bio, phone
    - Services list with prices/durations
    - Certifications with images
    - Reviews with ratings/comments
    - Average rating (stars)
    - Contact button (email, phone)
  - No auth required
  - 404 if provider not found or inactive

- File: `providers/models.py` (update)
- Add slug field for URL-friendly names:
  ```python
  slug = models.SlugField(unique=True)
  
  def save(self, *args, **kwargs):
      if not self.slug:
          self.slug = slugify(self.user.email.split('@')[0])
      super().save(*args, **kwargs)
  ```

- File: `marketplace/urls.py`
- Add URL:
  ```python
  path('providers/<slug:slug>/', ProviderDetailView.as_view(), name='provider_detail'),
  ```

- File: `clients/provider_detail.html`
- Create template with sections:
  - Header (photo, name, rating)
  - About (bio, contact info)
  - Services (list with prices)
  - Certifications (with images)
  - Reviews (sorted newest first)
  - Contact CTA

**Tests:**
```python
def test_provider_detail_loads():
    provider = create_test_provider()
    provider.subscription_status = 'active'
    provider.save()
    response = client.get(f'/providers/{provider.slug}/')
    assert response.status_code == 200

def test_provider_detail_inactive_404():
    provider = create_test_provider()
    provider.subscription_status = 'inactive'
    provider.save()
    response = client.get(f'/providers/{provider.slug}/')
    assert response.status_code == 404

def test_provider_detail_shows_services():
    provider = create_test_provider()
    provider.subscription_status = 'active'
    provider.save()
    service = Service.objects.create(
        provider=provider,
        service_type='swedish',
        price=75,
        duration_minutes=60
    )
    response = client.get(f'/providers/{provider.slug}/')
    assert b'75' in response.content
    assert b'60' in response.content

def test_provider_detail_shows_reviews():
    provider = create_test_provider()
    provider.subscription_status = 'active'
    provider.save()
    Review.objects.create(provider=provider, rating=5, comment="Great!")
    response = client.get(f'/providers/{provider.slug}/')
    assert b'Great!' in response.content
    assert b'★★★★★' in response.content or b'5' in response.content

def test_provider_detail_shows_certifications():
    provider = create_test_provider()
    provider.subscription_status = 'active'
    provider.save()
    cert = Certification.objects.create(provider=provider, name="LMT")
    response = client.get(f'/providers/{provider.slug}/')
    assert b'LMT' in response.content
```

**Acceptance Criteria:**
- [ ] Provider detail page loads
- [ ] Shows provider info (photo, name, bio, phone)
- [ ] Shows all services with prices/durations
- [ ] Shows certifications
- [ ] Shows reviews
- [ ] Shows average rating
- [ ] Inactive providers return 404
- [ ] All tests pass

**Mark as [✓ DONE] when:** Provider detail pages fully functional.

---

#### TASK 5.3: Create Service Display Component
**Status:** [✓ DONE] ✓

**Objective:** Build reusable service card component.

**Requirements:**
- File: `marketplace/templates/includes/_service_card.html`
- Component displays:
  - Service type (as readable name)
  - Price (formatted as currency)
  - Duration (as readable time)
  - Description (if available)

- Update `clients/provider_detail.html` to use component
- Ensure consistent styling across app

**Template:**
```html
<div class="border border-gray-200 rounded-lg p-4 mb-4">
    <div class="flex justify-between items-start">
        <div>
            <h4 class="font-bold text-lg">{{ service.get_service_type_display }}</h4>
            <p class="text-gray-600">{{ service.description }}</p>
        </div>
        <div class="text-right">
            <p class="text-2xl font-bold text-green-600">${{ service.price }}</p>
            <p class="text-gray-500">{{ service.duration_minutes }} min</p>
        </div>
    </div>
</div>
```

**Tests:**
- Template renders without errors
- Prices formatted correctly
- Durations display correctly

**Acceptance Criteria:**
- [ ] Service card component created
- [ ] Displays all info correctly
- [ ] Reusable across app
- [ ] Styled consistently

**Mark as [✓ DONE] when:** Service component created and tested.

---

#### TASK 5.4: Optimize Database Queries
**Status:** [✓ DONE] ✓

**Objective:** Improve performance for provider list/detail views.

**Requirements:**
- Update `ProviderDirectoryView` querysets:
  ```python
  def get_queryset(self):
      return Provider.objects.filter(
          subscription_status='active',
          user__is_email_verified=True
      ).select_related('user').prefetch_related('services', 'reviews')
  ```

- Update `ProviderDetailView` to use select_related/prefetch_related
- Add database indexes:
  ```python
  class Meta:
      indexes = [
          models.Index(fields=['subscription_status']),
          models.Index(fields=['user', 'subscription_status']),
      ]
  ```

- Run query profiling:
  - Check number of queries
  - Aim for <5 queries per page load

**Tests:**
```python
def test_provider_list_query_count():
    # Create 10 providers with services
    for i in range(10):
        p = create_test_provider()
        for j in range(3):
            Service.objects.create(provider=p, service_type='swedish', price=75)
    
    with assert_num_queries(3):  # Should be ~3 queries, not 20+
        response = client.get('/providers/')

def test_provider_detail_query_count():
    provider = create_test_provider()
    Service.objects.create(provider=provider, service_type='swedish', price=75)
    
    with assert_num_queries(4):  # Should be ~4 queries
        response = client.get(f'/providers/{provider.slug}/')
```

**Acceptance Criteria:**
- [ ] Query count optimized
- [ ] select_related/prefetch_related used
- [ ] Database indexes created
- [ ] <5 queries per page
- [ ] Performance tests passing

**Mark as [✓ DONE] when:** Database queries optimized.

---

#### TASK 5.5: Add Pagination & Breadcrumbs
**Status:** [✓ DONE] ✓

**Objective:** Implement pagination and navigation breadcrumbs.

**Requirements:**
- File: `marketplace/templates/includes/_pagination.html`
- Component displays:
  - Previous/Next buttons
  - Page numbers
  - Current page indicator
  - Total pages

- Add to `clients/provider_list.html`
- Add breadcrumbs to `clients/provider_detail.html`:
  ```html
  <nav class="breadcrumb">
      <a href="/">Home</a> > 
      <a href="/providers/">Providers</a> > 
      <span>{{ provider.user.get_full_name }}</span>
  </nav>
  ```

**Tests:**
- Pagination displays correctly
- Links work
- Breadcrumbs show correct path
- Mobile responsive

**Acceptance Criteria:**
- [ ] Pagination component created
- [ ] Works correctly
- [ ] Breadcrumbs display
- [ ] Mobile friendly

**Mark as [✓ DONE] when:** Pagination and breadcrumbs working.

---

#### TASK 5.6: Mobile Responsiveness & Styling
**Status:** [✓ DONE] ✓

**Objective:** Ensure views are mobile-friendly.

**Requirements:**
- Test on mobile browsers:
  - iOS Safari
  - Android Chrome
- Ensure:
  - Images resize properly
  - Text readable on small screens
  - Buttons touch-friendly
  - No horizontal scroll
  - Menu responsive

- Use Tailwind responsive classes:
  - `grid-cols-1 md:grid-cols-2 lg:grid-cols-4`
  - `text-lg md:text-xl lg:text-2xl`
  - `hidden md:block`

**Tests:**
- Responsive layout tests
- Mobile browser testing
- No layout shifts

**Acceptance Criteria:**
- [ ] Mobile responsive
- [ ] Touch-friendly buttons
- [ ] Images scale properly
- [ ] No horizontal scroll
- [ ] All tests passing

**Mark as [✓ DONE] when:** All views mobile-friendly.

---

#### TASK 5.7: Create Week 5 Tests & Documentation
**Status:** [✓ DONE] ✓

**Objective:** Comprehensive testing and documentation for Week 5.

**Requirements:**
- Test coverage > 85% for clients app
- Update `docs/CLIENT_FLOWS.md`:
  - Browse providers
  - View provider profile
  - Contact provider
- Update `README.md` with feature list
- Run: `pytest clients/ -v --cov=clients`

**Acceptance Criteria:**
- [ ] Coverage > 85%
- [ ] All tests passing
- [ ] Documentation updated
- [ ] Code reviewed

**Mark as [✓ DONE] when:** Week 5 complete and tested.

---

### WEEK 7: Reviews System

#### TASK 7.1: Create Review Submission Form
**Status:** [ ] TODO

**Objective:** Build form for clients to submit reviews (5-star rating + comment).

**Requirements:**
- File: `reviews/forms.py` (if needed) or inline form
- Create review form with:
  - Rating field (1-5 stars, required)
  - Comment field (TextArea, max 250 characters, required)
  - Client name field (optional, CharField)
- Star rating input (radio buttons or select)
- Character counter for comment field
- Validation: 1 ≤ rating ≤ 5, comment ≤ 250 chars
- Display on provider detail page

**Tests:**
```python
def test_review_form_valid():
    form_data = {'rating': 5, 'comment': 'Great service!', 'client_name': 'John'}
    form = ReviewForm(data=form_data)
    assert form.is_valid()

def test_review_form_rating_required():
    form_data = {'comment': 'Great service!'}
    form = ReviewForm(data=form_data)
    assert not form.is_valid()

def test_review_form_comment_max_length():
    form_data = {'rating': 5, 'comment': 'x' * 251}
    form = ReviewForm(data=form_data)
    assert not form.is_valid()
```

**Acceptance Criteria:**
- [ ] Review form displays on provider detail page
- [ ] Rating field works (1-5 stars)
- [ ] Comment field has character limit
- [ ] Client name is optional
- [ ] Form validation works
- [ ] All tests pass

**Mark as [✓ DONE] when:** Review form displays and validates correctly.

---

#### TASK 7.2: Create Review Submission View
**Status:** [ ] TODO

**Objective:** Handle POST request for review submission.

**Requirements:**
- File: `reviews/views.py`
- Create `ReviewSubmitView` (FormView or CreateView):
  - POST `/providers/<slug>/review/`
  - Validates form data
  - Creates Review object
  - Links to provider
  - Redirects back to provider detail
  - Shows success message
- Enforce one review per email/IP per provider (basic spam prevention)
- Use database unique constraint: `unique_together = ['provider', 'client_email']`

**Tests:**
```python
def test_submit_review_success():
    provider = create_test_provider()
    response = client.post(
        f'/providers/{provider.user.email}/review/',
        {'rating': 5, 'comment': 'Great!', 'client_name': 'John', 'client_email': 'john@example.com'}
    )
    assert response.status_code == 302  # Redirect
    assert Review.objects.filter(provider=provider).count() == 1

def test_submit_review_duplicate_prevention():
    provider = create_test_provider()
    Review.objects.create(provider=provider, rating=5, comment='First', client_email='john@example.com')

    response = client.post(
        f'/providers/{provider.user.email}/review/',
        {'rating': 4, 'comment': 'Second', 'client_email': 'john@example.com'}
    )
    # Should fail due to unique constraint
    assert Review.objects.filter(provider=provider).count() == 1
```

**Acceptance Criteria:**
- [ ] Review submission view handles POST
- [ ] Creates Review object
- [ ] Links review to provider
- [ ] Redirects with success message
- [ ] Spam prevention works (1 review per email per provider)
- [ ] All tests pass

**Mark as [✓ DONE] when:** Review submission works and spam prevention is active.

---

#### TASK 7.3: Display Reviews on Provider Detail Page
**Status:** [ ] TODO

**Objective:** Show all reviews on provider profile page.

**Requirements:**
- File: `templates/clients/provider_detail.html` (already has reviews section)
- Update to show:
  - All reviews for provider
  - Newest first (order by -created_at)
  - Star rating (visual stars)
  - Comment text
  - Client name (if provided) or "Anonymous"
  - Review date
- Empty state: "No reviews yet. Be the first to review!"
- Reviews section already exists, just needs enhancement

**Tests:**
```python
def test_provider_detail_shows_reviews():
    provider = create_test_provider()
    Review.objects.create(provider=provider, rating=5, comment='Great!', client_name='John')
    Review.objects.create(provider=provider, rating=4, comment='Good', client_name='Jane')

    response = client.get(f'/providers/{provider.user.email}/')
    assert b'Great!' in response.content
    assert b'Good' in response.content
    assert b'John' in response.content
    assert b'Jane' in response.content

def test_provider_detail_no_reviews():
    provider = create_test_provider()
    response = client.get(f'/providers/{provider.user.email}/')
    assert b'No reviews yet' in response.content
```

**Acceptance Criteria:**
- [ ] Reviews display on provider detail page
- [ ] Newest reviews shown first
- [ ] Star rating displays visually
- [ ] Client name or "Anonymous" shown
- [ ] Review date displayed
- [ ] Empty state works
- [ ] All tests pass

**Mark as [✓ DONE] when:** Reviews display correctly on provider profiles.

---

#### TASK 7.4: Admin Review Moderation
**Status:** [ ] TODO

**Objective:** Allow admins to moderate reviews (approve/flag/delete).

**Requirements:**
- Update `Review` model:
  - Add `status` field (choices: 'pending', 'approved', 'flagged')
  - Add `moderated_by` ForeignKey to User (nullable)
  - Add `moderated_at` DateTimeField (nullable)
- Create admin views:
  - List all reviews with status filters
  - Approve/flag/delete actions
- Django admin integration:
  - Add Review to admin
  - Add list filters: status, provider, rating
  - Add search: comment, client_name
  - Add bulk actions: approve, flag, delete

**Tests:**
```python
def test_review_model_has_status():
    provider = create_test_provider()
    review = Review.objects.create(provider=provider, rating=5, comment='Test')
    assert review.status == 'pending'  # Default

def test_admin_can_approve_review():
    admin_user = create_admin_user()
    review = create_test_review()

    # Simulate admin approval
    review.status = 'approved'
    review.moderated_by = admin_user
    review.save()

    assert review.status == 'approved'
    assert review.moderated_by == admin_user
```

**Acceptance Criteria:**
- [ ] Review model has status field
- [ ] Admin can view all reviews
- [ ] Admin can filter by status
- [ ] Admin can approve/flag/delete reviews
- [ ] Moderation tracked (who, when)
- [ ] Django admin configured
- [ ] All tests pass

**Mark as [✓ DONE] when:** Admin review moderation is functional.

---

#### TASK 7.5: Email Notifications for New Reviews
**Status:** [ ] TODO

**Objective:** Send email to admin when new review is submitted.

**Requirements:**
- File: `reviews/views.py`
- In `ReviewSubmitView.form_valid()`:
  - Send email to admin(s) after review submission
  - Email subject: "New Review Submitted - [Provider Name]"
  - Email body includes:
    - Provider name and email
    - Rating (stars)
    - Comment excerpt
    - Link to provider detail page
    - Link to admin review moderation
- Use Django's send_mail()
- Fail silently (don't break submission if email fails)

**Tests:**
```python
def test_review_submission_sends_email():
    provider = create_test_provider()

    with patch('django.core.mail.send_mail') as mock_send_mail:
        client.post(
            f'/providers/{provider.user.email}/review/',
            {'rating': 5, 'comment': 'Great!', 'client_email': 'test@example.com'}
        )

        assert mock_send_mail.called
        args = mock_send_mail.call_args[0]
        assert 'New Review Submitted' in args[0]  # Subject

def test_review_submission_works_if_email_fails():
    provider = create_test_provider()

    with patch('django.core.mail.send_mail', side_effect=Exception('Email failed')):
        response = client.post(
            f'/providers/{provider.user.email}/review/',
            {'rating': 5, 'comment': 'Great!', 'client_email': 'test@example.com'}
        )

        # Should still succeed
        assert response.status_code == 302
        assert Review.objects.count() == 1
```

**Acceptance Criteria:**
- [ ] Email sent to admin on new review
- [ ] Email contains review details
- [ ] Email has links to provider and moderation
- [ ] Email failure doesn't break submission
- [ ] All tests pass

**Mark as [✓ DONE] when:** Email notifications work without breaking submission.

---

#### TASK 7.6: Update Average Rating Display
**Status:** [ ] TODO

**Objective:** Update provider average rating calculation to use new review system.

**Requirements:**
- Model already has `average_rating()` method
- Verify it works with new reviews
- Update provider directory to show ratings
- Update provider detail to show ratings
- Add review count next to rating
- Empty state: "No ratings yet" instead of "0.0"

**Tests:**
```python
def test_average_rating_calculation():
    provider = create_test_provider()
    Review.objects.create(provider=provider, rating=5, comment='Great!')
    Review.objects.create(provider=provider, rating=4, comment='Good')
    Review.objects.create(provider=provider, rating=3, comment='OK')

    avg_rating = provider.average_rating()
    assert avg_rating == 4.0

def test_average_rating_with_no_reviews():
    provider = create_test_provider()
    avg_rating = provider.average_rating()
    assert avg_rating == 0

def test_provider_list_shows_ratings():
    provider = create_test_provider()
    Review.objects.create(provider=provider, rating=5, comment='Great!')

    response = client.get('/providers/')
    assert b'5.0' in response.content or b'5' in response.content
```

**Acceptance Criteria:**
- [ ] Average rating calculates correctly
- [ ] Displays on provider cards
- [ ] Displays on provider detail
- [ ] Shows review count
- [ ] Empty state for no ratings
- [ ] All tests pass

**Mark as [✓ DONE] when:** Average ratings display correctly everywhere.

---

#### TASK 7.7: Week 7 Tests & Documentation
**Status:** [ ] TODO

**Objective:** Comprehensive testing and documentation for reviews system.

**Requirements:**
- Test coverage > 85% for reviews app
- Create `docs/REVIEW_FLOWS.md`:
  - How to submit a review
  - Review moderation process
  - Spam prevention details
  - Admin review management
- Update `README.md` with review features
- Create admin guide for review moderation

**Tests:**
- Run full test suite
- Verify all review flows work end-to-end
- Test edge cases (duplicate reviews, invalid data)
- Test email notifications

**Acceptance Criteria:**
- [ ] Coverage > 85%
- [ ] All tests passing
- [ ] Documentation complete
- [ ] Admin guide created
- [ ] Code reviewed

**Mark as [✓ DONE] when:** Week 7 complete and documented.

---

### WEEK 8: Payment Substrate & Crypto Forms

#### TASK 8.1: Update SubscriptionPayment Model
**Status:** [ ] TODO

**Objective:** Ensure SubscriptionPayment model has all required fields.

**Requirements:**
- File: `payments/models.py`
- Verify/add fields:
  - `provider` (ForeignKey to Provider)
  - `amount` (DecimalField, default 29.99)
  - `payment_method` (CharField, choices: 'crypto_btc', 'crypto_eth', 'crypto_usdc', 'bank_transfer')
  - `transaction_reference` (CharField, for crypto transaction ID or bank reference)
  - `status` (CharField, choices: 'pending', 'completed', 'failed')
  - `created_at`, `updated_at`
- Add methods:
  - `mark_completed()` - Set status to completed
  - `mark_failed()` - Set status to failed

**Tests:**
```python
def test_subscription_payment_creation():
    provider = create_test_provider()
    payment = SubscriptionPayment.objects.create(
        provider=provider,
        amount=29.99,
        payment_method='crypto_btc',
        status='pending'
    )
    assert payment.status == 'pending'
    assert payment.amount == Decimal('29.99')

def test_mark_payment_completed():
    payment = create_test_payment()
    payment.mark_completed()
    assert payment.status == 'completed'
```

**Acceptance Criteria:**
- [ ] All fields present and working
- [ ] Payment methods include all crypto + bank
- [ ] Status transitions work
- [ ] Migration created
- [ ] All tests pass

**Mark as [✓ DONE] when:** SubscriptionPayment model is complete.

---

#### TASK 8.2: Create Payment Method Selection Form
**Status:** [ ] TODO

**Objective:** Allow providers to choose payment method (crypto or bank transfer).

**Requirements:**
- File: `providers/forms.py`
- Update or create `SubscriptionSettingsForm`:
  - Payment method radio buttons:
    - Bitcoin (BTC)
    - Ethereum (ETH)
    - USDC (stablecoin)
    - Bank Transfer
  - Each option shows description/instructions
- Form displays current subscription status
- Shows renewal date if active

**Tests:**
```python
def test_payment_method_form_valid():
    form_data = {'payment_method': 'crypto_btc'}
    form = SubscriptionSettingsForm(data=form_data)
    assert form.is_valid()

def test_payment_method_choices():
    form = SubscriptionSettingsForm()
    choices = dict(form.fields['payment_method'].choices)
    assert 'crypto_btc' in choices
    assert 'crypto_eth' in choices
    assert 'bank_transfer' in choices
```

**Acceptance Criteria:**
- [ ] Form has payment method selection
- [ ] All payment options available
- [ ] Descriptions clear
- [ ] Form validates
- [ ] All tests pass

**Mark as [✓ DONE] when:** Payment method form works correctly.

---

#### TASK 8.3: Create Crypto Payment Form
**Status:** [ ] TODO

**Objective:** Display crypto payment instructions and wallet address.

**Requirements:**
- File: `templates/providers/subscription.html`
- For crypto payments, display:
  - Platform wallet address (read-only)
  - QR code (optional, use qrcode library)
  - Payment amount (29.99 USD equivalent in crypto)
  - Instructions: "Send exactly X BTC/ETH/USDC to this address"
  - Warning: "Payment may take up to 1 hour to confirm"
- Store crypto addresses in settings or database
- Provider can paste their transaction ID for verification

**Tests:**
```python
def test_crypto_payment_page_shows_address():
    provider = create_test_provider()
    client.force_login(provider.user)

    response = client.get('/provider/subscription/crypto/btc/')
    assert b'Send payment to:' in response.content
    assert b'1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2' in response.content  # Example BTC address

def test_transaction_id_submission():
    provider = create_test_provider()
    client.force_login(provider.user)

    response = client.post('/provider/subscription/crypto/submit/', {
        'payment_method': 'crypto_btc',
        'transaction_id': '0x123456789abcdef'
    })

    assert response.status_code == 302
    payment = SubscriptionPayment.objects.filter(provider=provider).first()
    assert payment.transaction_reference == '0x123456789abcdef'
```

**Acceptance Criteria:**
- [ ] Crypto payment page displays address
- [ ] Shows payment amount
- [ ] Shows instructions
- [ ] Provider can submit transaction ID
- [ ] QR code displays (optional)
- [ ] All tests pass

**Mark as [✓ DONE] when:** Crypto payment UI is functional.

---

#### TASK 8.4: Create Bank Transfer Payment Form
**Status:** [ ] TODO

**Objective:** Collect bank transfer details from provider.

**Requirements:**
- File: `providers/forms.py` and `templates/providers/subscription_bank.html`
- Form fields:
  - Bank name
  - Account holder name
  - Account number (encrypted before storage)
  - Routing number / SWIFT code
  - Reference number (auto-generated)
- Display platform's bank details:
  - "Send payment to our bank account:"
  - Bank name, account number, routing
  - Reference: [Provider-ID-Date]
- Store provider's bank details encrypted (use cryptography library or Django's Fernet)

**Tests:**
```python
def test_bank_transfer_form_valid():
    form_data = {
        'bank_name': 'Chase Bank',
        'account_holder': 'John Doe',
        'account_number': '1234567890',
        'routing_number': '021000021'
    }
    form = BankTransferForm(data=form_data)
    assert form.is_valid()

def test_bank_details_encrypted():
    provider = create_test_provider()
    form = BankTransferForm(data={
        'bank_name': 'Chase',
        'account_holder': 'John',
        'account_number': '1234567890',
        'routing_number': '021000021'
    })
    form.instance.provider = provider
    form.save()

    # Bank account should be encrypted
    provider.refresh_from_db()
    assert provider.bank_account_encrypted != '1234567890'
    assert len(provider.bank_account_encrypted) > 20  # Encrypted is longer
```

**Acceptance Criteria:**
- [ ] Bank transfer form collects all details
- [ ] Platform bank details displayed
- [ ] Reference number generated
- [ ] Bank account encrypted before storage
- [ ] Form validates
- [ ] All tests pass

**Mark as [✓ DONE] when:** Bank transfer form works and encrypts data.

---

#### TASK 8.5: Create Subscription Activation Logic
**Status:** [ ] TODO

**Objective:** Activate subscription when payment method is selected.

**Requirements:**
- File: `providers/models.py` and `providers/views.py`
- When provider submits payment form:
  - Create SubscriptionPayment record with status='pending'
  - Set provider.subscription_status = 'active' (temporary, pending verification)
  - Set provider.subscription_renewal_date = today + 30 days
  - Set provider.subscription_payment_method
  - Send confirmation email to provider
- Email includes:
  - Payment instructions
  - Renewal date
  - How to check payment status

**Tests:**
```python
def test_subscription_activation():
    provider = create_test_provider()
    assert provider.subscription_status == 'inactive'

    provider.activate_subscription('crypto_btc')
    provider.refresh_from_db()

    assert provider.subscription_status == 'active'
    assert provider.subscription_payment_method == 'crypto_btc'
    assert provider.subscription_renewal_date is not None

def test_subscription_payment_created():
    provider = create_test_provider()
    provider.activate_subscription('crypto_btc')

    payment = SubscriptionPayment.objects.filter(provider=provider).first()
    assert payment is not None
    assert payment.status == 'pending'
    assert payment.payment_method == 'crypto_btc'
```

**Acceptance Criteria:**
- [ ] Subscription activates on payment submission
- [ ] SubscriptionPayment record created
- [ ] Renewal date set to 30 days
- [ ] Confirmation email sent
- [ ] Status set to pending
- [ ] All tests pass

**Mark as [✓ DONE] when:** Subscription activation works correctly.

---

#### TASK 8.6: Week 8 Tests & Documentation
**Status:** [ ] TODO

**Objective:** Comprehensive testing and documentation for payment system.

**Requirements:**
- Test coverage > 85% for payments app
- Create `docs/PAYMENT_FLOWS.md`:
  - How to subscribe (crypto and bank)
  - Payment verification process
  - Admin payment approval workflow
  - Troubleshooting payment issues
- Update `README.md` with payment features
- Test all payment flows end-to-end

**Acceptance Criteria:**
- [ ] Coverage > 85%
- [ ] All tests passing
- [ ] Documentation complete
- [ ] Payment flows documented
- [ ] Code reviewed

**Mark as [✓ DONE] when:** Week 8 complete and documented.

---

## SPRINT 3: Admin Dashboard, Payments, & Launch (Weeks 9-12)

### WEEK 9: Admin Dashboard

#### TASK 9.1: Create Admin Dashboard Landing Page
**Status:** [ ] TODO

**Objective:** Build admin dashboard with key metrics and navigation.

**Requirements:**
- File: `templates/admin/dashboard.html`
- Display:
  - Total providers (active/inactive counts)
  - Total services
  - Total reviews
  - Pending payments count
  - Revenue metrics (total, this month)
- Navigation to:
  - Provider management
  - Payment queue
  - Review moderation
  - Analytics
- Use AdminRequiredMixin for access control

**Acceptance Criteria:**
- [ ] Dashboard displays all metrics
- [ ] Navigation links work
- [ ] Only admins can access
- [ ] Responsive design
- [ ] All tests pass

**Mark as [✓ DONE] when:** Admin dashboard is functional.

---

#### TASK 9.2: Admin Provider Management
**Status:** [ ] TODO

**Objective:** Allow admins to manage all providers (search, filter, edit).

**Requirements:**
- Already exists: `AdminProviderListView`
- Enhance with:
  - Advanced search (email, name, city)
  - Filters: status, payment method, join date
  - Bulk actions: suspend, activate
  - Export to CSV
- Provider detail page for admins:
  - Edit profile
  - View services
  - View payment history
  - Suspend/unsuspend account

**Acceptance Criteria:**
- [ ] Admin can search providers
- [ ] Admin can filter by multiple fields
- [ ] Admin can edit provider details
- [ ] Admin can suspend/activate accounts
- [ ] All tests pass

**Mark as [✓ DONE] when:** Admin provider management is complete.

---

#### TASK 9.3: Admin Analytics Dashboard
**Status:** [ ] TODO

**Objective:** Display platform analytics for admins.

**Requirements:**
- File: `templates/admin/analytics.html`
- Charts (use Chart.js or similar):
  - Provider signups over time
  - Revenue over time
  - Average rating trend
  - Service type distribution
- Metrics:
  - Conversion rate (signups to paid)
  - Average revenue per provider
  - Churn rate
  - Active providers

**Acceptance Criteria:**
- [ ] Analytics page displays charts
- [ ] Key metrics calculated correctly
- [ ] Data updates in real-time
- [ ] Exports available
- [ ] All tests pass

**Mark as [✓ DONE] when:** Analytics dashboard is functional.

---

### WEEK 10: Payment Monitoring

#### TASK 10.1: Setup Crypto Payment Monitoring
**Status:** [ ] TODO

**Objective:** Monitor Bitcoin/Ethereum/USDC wallets for incoming payments.

**Requirements:**
- Install web3.py and blockchain API libraries
- Create management command: `python manage.py monitor_crypto_payments`
- For each pending crypto payment:
  - Check blockchain for transaction
  - Match transaction to provider
  - Update payment status
  - Send confirmation email
- APIs to use:
  - Bitcoin: Blockchain.com API (free)
  - Ethereum/USDC: Etherscan API (free tier)
- Run as cron job every hour

**Acceptance Criteria:**
- [ ] Can query blockchain APIs
- [ ] Matches transactions to providers
- [ ] Updates payment status
- [ ] Sends confirmation emails
- [ ] All tests pass

**Mark as [✓ DONE] when:** Crypto monitoring works automatically.

---

#### TASK 10.2: Admin Bank Transfer Verification
**Status:** [ ] TODO

**Objective:** Allow admins to manually verify bank transfers.

**Requirements:**
- Already exists: `AdminPaymentListView`, `AdminPaymentDetailView`
- Add actions:
  - Mark as completed (with confirmation)
  - Mark as failed (with reason)
  - Request more info from provider
- Payment detail page shows:
  - Provider bank details (decrypted for admin)
  - Reference number
  - Amount and date
  - Approve/reject buttons

**Acceptance Criteria:**
- [ ] Admin can view pending bank transfers
- [ ] Admin can approve/reject payments
- [ ] Confirmation emails sent
- [ ] Status updates correctly
- [ ] All tests pass

**Mark as [✓ DONE] when:** Bank transfer verification works.

---

### WEEK 11: Security & Infrastructure

#### TASK 11.1: Security Audit
**Status:** [ ] TODO

**Objective:** Perform comprehensive security audit and fixes.

**Requirements:**
- Check all forms for CSRF protection
- Verify XSS prevention (template escaping)
- SQL injection prevention (use ORM only)
- Rate limiting on login/signup
- Password hashing (verify PBKDF2/Argon2)
- HTTPS enforcement
- Secure headers (CSP, HSTS)
- Environment variable security

**Acceptance Criteria:**
- [ ] Security checklist complete
- [ ] All vulnerabilities fixed
- [ ] Rate limiting implemented
- [ ] Secure headers configured
- [ ] Security tests pass

**Mark as [✓ DONE] when:** Security audit passed.

---

#### TASK 11.2: Infrastructure Setup
**Status:** [ ] TODO

**Objective:** Setup production infrastructure (VPS, database, storage).

**Requirements:**
- Provision VPS (DigitalOcean/Linode)
- Install PostgreSQL
- Setup Minio or S3 for media files
- Configure Nginx + Gunicorn
- Setup systemd services
- Configure domain and DNS
- Install SSL certificates (Let's Encrypt)
- Setup backups (daily database, weekly files)

**Acceptance Criteria:**
- [ ] VPS provisioned and configured
- [ ] PostgreSQL running
- [ ] Media storage working
- [ ] Nginx + Gunicorn configured
- [ ] SSL certificates installed
- [ ] Backups automated

**Mark as [✓ DONE] when:** Infrastructure is production-ready.

---

### WEEK 12: Testing & Launch

#### TASK 12.1: Beta Testing
**Status:** [ ] TODO

**Objective:** Test with real users before public launch.

**Requirements:**
- Onboard 5-10 beta providers
- Test full flow: signup → profile → service → payment
- Test on multiple devices:
  - Desktop (Chrome, Firefox, Safari, Edge)
  - Mobile (iOS Safari, Chrome Mobile)
- Collect feedback
- Fix critical bugs
- Test payment flows (testnet for crypto)

**Acceptance Criteria:**
- [ ] 5+ beta providers onboarded
- [ ] All flows tested end-to-end
- [ ] Mobile and desktop testing complete
- [ ] Critical bugs fixed
- [ ] Feedback collected

**Mark as [✓ DONE] when:** Beta testing complete.

---

#### TASK 12.2: Legal Documentation
**Status:** [ ] TODO

**Objective:** Create Terms of Service, Privacy Policy, and Payment Policy.

**Requirements:**
- Terms of Service
  - User obligations
  - Service terms
  - Liability limitations
- Privacy Policy
  - Data collection
  - Data usage
  - GDPR compliance
- Payment Policy
  - Subscription terms
  - Refund policy
  - Payment methods
- Display links in footer
- Require acceptance on signup

**Acceptance Criteria:**
- [ ] Terms of Service created
- [ ] Privacy Policy created
- [ ] Payment Policy created
- [ ] Links in footer
- [ ] Acceptance required on signup

**Mark as [✓ DONE] when:** Legal documents complete and live.

---

#### TASK 12.3: Production Launch
**Status:** [ ] TODO

**Objective:** Deploy to production and go live.

**Requirements:**
- Database migration to production
- Static files collection
- Environment variables configured
- Monitoring and logging active
- Backups running
- SSL certificate valid
- Domain configured
- Announce launch
- Monitor for 48 hours

**Acceptance Criteria:**
- [ ] App live at production URL
- [ ] All pages load < 2 seconds
- [ ] SSL certificate valid
- [ ] Monitoring active
- [ ] Backups running
- [ ] Launch announced

**Mark as [✓ DONE] when:** Platform is live and stable.

---

## TASK STATUS TRACKING

Use this format to track completion:

```markdown
## Week 1
- [✓] TASK 1.1: Initialize Django Project
- [✓] TASK 1.2: Custom User Model
- [✓] TASK 1.3: Provider Model
- [ ] TASK 1.4: Service & Certification Models
- [ ] TASK 1.5: Review & Payment Models
- [ ] TASK 1.6: Django Admin Setup
- [ ] TASK 1.7: Test Fixtures
- [ ] TASK 1.8: Git Setup

## Week 2
- [ ] TASK 2.1: Email Authentication Backend
- [ ] TASK 2.2: Email Verification System
- [ ] TASK 2.3: Signup Flow
[...]
```

---

## NEXT STEPS

1. **Start with TASK 1.1** immediately
2. **Mark complete as you finish** each task
3. **Run tests after each task** to verify
4. **Commit to Git** after task completion
5. **Update this file** with progress
6. **Move to next task** only when previous is done

---

**Last Updated:** Task list created and ready for development  
**Status:** Ready for Sprint 1 Week 1 execution  
**Estimated Completion:** 12 weeks with 2-3 developers
