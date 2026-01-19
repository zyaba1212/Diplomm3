#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
from dotenv import load_dotenv

def main():
    """Run administrative tasks."""
    # Load environment variables
    load_dotenv()
    
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'z96a.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    
    # Add custom commands
    from django.core.management.commands.runserver import Command as runserver
    runserver.default_port = os.getenv('PORT', '8000')
    runserver.default_addr = os.getenv('HOST', '127.0.0.1')
    
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()