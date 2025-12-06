"""
WSGI config for medicine_qr_app project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os
from pathlib import Path

from django.core.wsgi import get_wsgi_application
from django.conf import settings
from whitenoise import WhiteNoise

# Ensure settings module is set for production environments
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medicine_qr_app.settings')

# Base Django WSGI application
application = get_wsgi_application()

# Add WhiteNoise for efficient static file serving in production
# This complements the middleware and works with collected static files.
static_root = Path(getattr(settings, 'STATIC_ROOT', Path(__file__).resolve().parent.parent / 'staticfiles'))
application = WhiteNoise(application, root=str(static_root), autorefresh=False)
