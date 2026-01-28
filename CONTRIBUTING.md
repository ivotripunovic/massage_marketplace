# Contributing to Massage Marketplace

## Development Workflow

### 1. Feature Branches
Always create a feature branch for new work:

```bash
git checkout -b feature/task-name
```

Branch naming convention:
- `feature/task-description` - New features
- `fix/bug-description` - Bug fixes
- `refactor/improvement` - Code improvements

### 2. Commits

Write clear, descriptive commit messages:

```
[TASK-ID] Brief description of change

Longer explanation if needed. Reference any related issues.

- Bullet point 1
- Bullet point 2
```

Example:
```
[1.1] Initialize Django project with models

- Created Django 5.0 project with 5 apps
- Added custom User model with email-based auth
- Configured database settings
- Added requirements.txt with dependencies
```

### 3. Code Style

#### Python
- Use PEP 8 style guide
- 4 spaces for indentation
- Max line length: 99 characters
- Use type hints where appropriate

```python
# Good
def create_user(email: str, password: str) -> User:
    """Create a new user."""
    return User.objects.create_user(email=email, password=password)
```

#### Django
- Use class-based views for most views
- Keep models in `models.py`
- Register models in `admin.py`
- Create forms in `forms.py`
- Organize templates in `templates/<app>/`

### 4. Testing Requirements

**All code must be tested before committing.**

Run tests locally:
```bash
# Run all tests
python manage.py test users providers reviews payments

# Run specific app tests
python manage.py test users

# Run with verbosity
python manage.py test users -v 2

# Run specific test class
python manage.py test users.tests.CustomUserModelTests
```

**Test Coverage Requirements:**
- Models: 100% coverage
- Forms: 100% coverage
- Views: 100% coverage
- Utils: 100% coverage

**Test File Naming:**
- `tests.py` - Main tests for models
- `test_forms.py` - Form tests
- `test_views.py` - View tests
- `test_utils.py` - Utility function tests

### 5. Pull Request Process

1. Push your feature branch
2. Create a pull request with:
   - Descriptive title
   - Summary of changes
   - Related issues/tasks
   - Test results showing all passing

3. Code review checklist:
   - [ ] All tests pass
   - [ ] Code follows style guide
   - [ ] Models have proper validation
   - [ ] Views have appropriate decorators/mixins
   - [ ] Forms validate correctly
   - [ ] Templates are properly structured
   - [ ] No hardcoded credentials or sensitive data
   - [ ] Documentation is updated

### 6. Documentation

- Update `README.md` for setup changes
- Update `PROGRESS.md` when tasks are completed
- Add docstrings to all functions and classes
- Comment complex logic
- Update this file with any new conventions

## Task Workflow

Each task follows this pattern:

1. **Plan**: Read requirements in TASK_LIST.md
2. **Implement**: Write code with tests
3. **Test**: Run full test suite (all passing)
4. **Document**: Update PROGRESS.md
5. **Mark Complete**: Update TASK_LIST.md status to [✓ DONE]
6. **Commit**: Push changes with clear commit message

## Running the Project Locally

```bash
# Activate virtual environment
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Start development server
python manage.py runserver

# Access admin
# http://localhost:8000/admin
```

## Database

### Migrations
Always create migrations after model changes:
```bash
python manage.py makemigrations
python manage.py migrate
```

### Resetting Database (Development Only)
```bash
rm db.sqlite3
python manage.py migrate
python manage.py createsuperuser
```

## Common Commands

```bash
# Run tests
python manage.py test <app>

# Create migration
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Check for issues
python manage.py check

# Shell with context
python manage.py shell

# Create fixture (for testing data)
python manage.py dumpdata > fixtures.json
python manage.py loaddata fixtures.json
```

## Environment Variables

Copy `.env.example` to `.env` and update values:
```bash
cp .env.example .env
```

Never commit `.env` file (it's in `.gitignore`).

## Git Workflow Summary

```bash
# 1. Create feature branch
git checkout -b feature/task-name

# 2. Make changes and test
python manage.py test

# 3. Stage and commit
git add .
git commit -m "[TASK-ID] Clear description"

# 4. Push to remote
git push origin feature/task-name

# 5. Create pull request and merge after review
```

## Questions?

Check:
1. TASK_LIST.md for specific requirements
2. PROGRESS.md for what's been done
3. README.md for setup help
4. This file for conventions
