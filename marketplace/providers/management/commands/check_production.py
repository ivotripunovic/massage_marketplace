"""Management command to validate production readiness.

Usage:
    python manage.py check_production
"""

import os
import sys

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Validate production readiness of the application settings'

    def handle(self, *args, **options):
        errors = []
        warnings = []
        passed = []

        # 1. DEBUG must be False
        if settings.DEBUG:
            errors.append('DEBUG is True. Set DEBUG=False in .env for production.')
        else:
            passed.append('DEBUG is False')

        # 2. SECRET_KEY must not be the insecure default
        if 'insecure' in settings.SECRET_KEY:
            errors.append('SECRET_KEY contains "insecure". Generate a new SECRET_KEY for production.')
        else:
            passed.append('SECRET_KEY is not the default insecure key')

        # 3. ALLOWED_HOSTS must be configured
        if not settings.ALLOWED_HOSTS or settings.ALLOWED_HOSTS == ['localhost', '127.0.0.1']:
            warnings.append('ALLOWED_HOSTS only includes localhost. Add your production domain.')
        else:
            passed.append(f'ALLOWED_HOSTS configured: {settings.ALLOWED_HOSTS}')

        # 4. Database should be PostgreSQL in production
        db_engine = settings.DATABASES['default']['ENGINE']
        if 'sqlite' in db_engine:
            warnings.append(f'Database is SQLite ({db_engine}). Use PostgreSQL for production.')
        else:
            passed.append(f'Database engine: {db_engine}')

        # 5. Email backend should not be console
        if 'console' in settings.EMAIL_BACKEND:
            warnings.append('EMAIL_BACKEND is console. Configure SMTP for production email delivery.')
        else:
            passed.append(f'EMAIL_BACKEND: {settings.EMAIL_BACKEND}')

        # 6. Security settings (only applicable when DEBUG=False)
        if not settings.DEBUG:
            security_checks = [
                ('SECURE_SSL_REDIRECT', True),
                ('SECURE_HSTS_SECONDS', 31536000),
                ('SESSION_COOKIE_SECURE', True),
                ('CSRF_COOKIE_SECURE', True),
            ]
            for setting_name, expected in security_checks:
                value = getattr(settings, setting_name, None)
                if value != expected:
                    errors.append(f'{setting_name} is {value}, expected {expected}')
                else:
                    passed.append(f'{setting_name} = {value}')

        # 7. Cookie security
        if not settings.SESSION_COOKIE_HTTPONLY:
            errors.append('SESSION_COOKIE_HTTPONLY is False')
        else:
            passed.append('SESSION_COOKIE_HTTPONLY is True')

        if not settings.CSRF_COOKIE_HTTPONLY:
            errors.append('CSRF_COOKIE_HTTPONLY is False')
        else:
            passed.append('CSRF_COOKIE_HTTPONLY is True')

        # 8. STATIC_ROOT must be set
        if not settings.STATIC_ROOT:
            errors.append('STATIC_ROOT is not configured. Run collectstatic before deployment.')
        else:
            passed.append(f'STATIC_ROOT: {settings.STATIC_ROOT}')

        # 9. Check crypto addresses are not defaults
        btc = settings.PLATFORM_CRYPTO_ADDRESSES.get('crypto_bitcoin', '')
        if btc == '1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa':
            warnings.append('CRYPTO_BITCOIN_ADDRESS is the Satoshi genesis address (placeholder). Set your real address.')

        # 10. Rate limiting is configured
        if not getattr(settings, 'RATE_LIMIT_RULES', {}):
            warnings.append('RATE_LIMIT_RULES is empty. Rate limiting is disabled.')
        else:
            passed.append(f'Rate limiting configured: {len(settings.RATE_LIMIT_RULES)} rules')

        # Print results
        self.stdout.write('')
        self.stdout.write('=' * 60)
        self.stdout.write('  PRODUCTION READINESS CHECK')
        self.stdout.write('=' * 60)
        self.stdout.write('')

        if passed:
            self.stdout.write(self.style.SUCCESS(f'  PASSED ({len(passed)}):'))
            for msg in passed:
                self.stdout.write(self.style.SUCCESS(f'    [OK] {msg}'))
            self.stdout.write('')

        if warnings:
            self.stdout.write(self.style.WARNING(f'  WARNINGS ({len(warnings)}):'))
            for msg in warnings:
                self.stdout.write(self.style.WARNING(f'    [!!] {msg}'))
            self.stdout.write('')

        if errors:
            self.stdout.write(self.style.ERROR(f'  ERRORS ({len(errors)}):'))
            for msg in errors:
                self.stdout.write(self.style.ERROR(f'    [XX] {msg}'))
            self.stdout.write('')

        self.stdout.write('=' * 60)
        if errors:
            self.stdout.write(self.style.ERROR(
                f'  RESULT: NOT READY - {len(errors)} error(s), {len(warnings)} warning(s)'
            ))
            sys.exit(1)
        elif warnings:
            self.stdout.write(self.style.WARNING(
                f'  RESULT: READY WITH WARNINGS - {len(warnings)} warning(s)'
            ))
        else:
            self.stdout.write(self.style.SUCCESS('  RESULT: PRODUCTION READY'))
        self.stdout.write('=' * 60)
        self.stdout.write('')
