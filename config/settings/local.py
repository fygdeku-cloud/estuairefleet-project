from .base import *

DEBUG = True
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "0.0.0.0"]
# Mailpit captures all local e-mails through its SMTP endpoint. The web UI is
# exposed by Docker Compose on http://localhost:8025.
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = env.str("MAILPIT_HOST", default="mailpit")
EMAIL_PORT = env.int("MAILPIT_SMTP_PORT", default=1025)
EMAIL_USE_TLS = False
EMAIL_USE_SSL = False
INSTALLED_APPS = ["whitenoise.runserver_nostatic", *INSTALLED_APPS]
INSTALLED_APPS += ["debug_toolbar", "django_extensions"]
MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]
INTERNAL_IPS = ["127.0.0.1", "10.0.2.2"]
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
