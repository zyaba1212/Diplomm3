"""
WSGI config for z96a project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangodocs/en/stable/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'z96a.settings')

application = get_wsgi_application()