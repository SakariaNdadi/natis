"""
WSGI config for config project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/wsgi/
"""

import os
from .env import env

from django.core.wsgi import get_wsgi_application

DJANGO_SETTINGS_MODULE = env(
    "DJANGO_SETTINGS_MODULE", default="config.settings.development"
)

application = get_wsgi_application()
