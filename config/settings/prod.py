from config.env import env
from google.oauth2 import service_account

from .base import *

DEBUG = False

ADMINS = [
    ("Sakaria Ndadi", "oipapi.ndadi@gmail.com"),
]

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["127.0.0.1"])

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("POSTGRES_DB"),
        "USER": env("POSTGRES_USER"),
        "PASSWORD": env("POSTGRES_PASSWORD"),
        "HOST": env("POSTGRES_HOST", default="localhost"),
        "PORT": env("POSTGRES_PORT", default="5432"),
    },
}

# DATABASES = {
#     "default": {
#         "ENGINE": "django.db.backends.sqlite3",
#         "NAME": os.path.join(BASE_DIR, "db.sqlite3"),
#     }
# }

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = env("EMAIL_HOST")
EMAIL_PORT = env("EMAIL_PORT")
EMAIL_USE_TLS = env("EMAIL_USE_TLS")
EMAIL_HOST_USER = env("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD")


CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": env("REDIS_URL"),
    }
}

# Security
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = True
X_FRAME_OPTIONS = "DENY"

# Google cloud storage
GS_CREDENTIALS = service_account.Credentials.from_service_account_file(
    os.path.join(BASE_DIR, "credentials.json")
)
GS_BUCKET_NAME = env("GS_BUCKET_NAME")
GS_PROJECT_ID = env("GS_PROJECT_ID")
STORAGES["default"] = {
    "BACKEND": "storages.backends.gcloud.GoogleCloudStorage",
}
MEDIA_URL = f"https://storage.googleapis.com/{GS_BUCKET_NAME}/media/"
