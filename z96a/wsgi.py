"""
WSGI config for z96a project.
"""
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'z96a.settings')
application = get_wsgi_application()