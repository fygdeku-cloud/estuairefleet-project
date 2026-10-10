from .base import *

SECRET_KEY = "test-secret-key"
TEST_RUNNER = "django.test.runner.DiscoverRunner"
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "test.sqlite3"}}
MIGRATION_MODULES = {**MIGRATION_MODULES, "sites": "django.contrib.sites.migrations"}
