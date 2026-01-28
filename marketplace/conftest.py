"""
Pytest configuration for Django test suite.
Sets up optimized settings for fast test execution.
"""

import os
import django
from django.conf import settings

# Use optimized test settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'marketplace.test_settings')

# Configure Django
django.setup()
