# Massage Marketplace

A Django-based marketplace platform for massage therapy services.

## Local Development Setup

### Prerequisites
- Python 3.11+
- PostgreSQL 12+
- pip

### Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd directory_listing
   ```

2. **Create and activate virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your local settings
   ```

5. **Create PostgreSQL database:**
   ```bash
   createdb massage_marketplace
   ```

6. **Run migrations:**
   ```bash
   python manage.py migrate
   ```

7. **Create superuser:**
   ```bash
   python manage.py createsuperuser
   ```

8. **Run development server:**
   ```bash
   python manage.py runserver
   ```

   Server will be available at `http://localhost:8000`

## Accessing Admin Panel

Navigate to `http://localhost:8000/admin` and log in with your superuser credentials.

## Project Structure

```
marketplace/
├── users/              # Custom user model
├── providers/          # Provider profiles and services
├── clients/            # Client management
├── reviews/            # Review system
├── payments/           # Payment processing
├── marketplace/        # Main project settings
├── manage.py           # Django management script
└── requirements.txt    # Python dependencies
```

## Key Features

- **Custom User Model**: Email-based authentication with user types (provider, client, admin)
- **Provider Management**: Profiles with services, certifications, and subscriptions
- **Payment Processing**: Support for crypto (Bitcoin, Ethereum, USDC) and bank transfers
- **Review System**: Client reviews for providers
- **Admin Dashboard**: Payment verification and provider management

## Testing

Run tests with pytest:
```bash
pytest
```

## Documentation

See `TASK_LIST.md` for implementation roadmap and detailed task specifications.
