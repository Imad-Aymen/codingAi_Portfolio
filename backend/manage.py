#!/usr/bin/env python3
"""Standard Django management utility.

Basic commands:
    python manage.py makemigrations
    python manage.py migrate
    python manage.py runserver 0.0.0.0:8000
"""

import os
import sys


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Could not import Django. Activate the virtual environment and run: pip install -r requirements.txt"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
