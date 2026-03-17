#!/bin/bash
# Convenience script to run tests with optimized settings
# Usage: ./test.sh [app_name]

source venv/bin/activate

if [ -z "$1" ]; then
    # Run all tests (sandbox integration tests excluded — run separately, see below)
    python marketplace/manage.py test users providers reviews payments.tests users.test_security users.test_legal --settings=marketplace.test_settings
else
    # Run specific app tests
    python marketplace/manage.py test "$1" --settings=marketplace.test_settings
fi
