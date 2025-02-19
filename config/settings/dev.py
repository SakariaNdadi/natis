from .base import *

DEBUG = True

ALLOWED_HOSTS = ["*"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(BASE_DIR, "db.sqlite3"),
    }
}

INSTALLED_APPS.append("django_browser_reload")

MIDDLEWARE.append("django_browser_reload.middleware.BrowserReloadMiddleware")

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
