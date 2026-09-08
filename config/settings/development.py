import os

from .base import *


DEBUG = os.environ.get("DJANGO_DEBUG", "True").lower() == "true"
EMAIL_BACKEND = "django.core.mail.backends.filebased.EmailBackend"
EMAIL_FILE_PATH = BASE_DIR / ".tools" / "emails"
