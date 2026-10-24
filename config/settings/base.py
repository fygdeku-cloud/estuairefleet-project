"""Shared settings for all environments."""

import ssl
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent
APPS_DIR = BASE_DIR / "estuairefleet"
env = environ.Env()
if env.bool("DJANGO_READ_DOT_ENV_FILE", default=False):
    env.read_env(str(BASE_DIR / ".env"))

DEBUG = env.bool("DJANGO_DEBUG", default=False)
SECRET_KEY = env.str("DJANGO_SECRET_KEY", default="unsafe-development-key")
TIME_ZONE = "Africa/Douala"
LANGUAGE_CODE = "fr"
LANGUAGES = (("fr", "Français"), ("en", "English"))
USE_I18N = True
USE_TZ = True
LOCALE_PATHS = [str(BASE_DIR / "locale")]
SITE_ID = 1

DATABASES = {
    "default": env.db(
        "DATABASE_URL",
        default=(
            f"postgresql://{env.str('POSTGRES_USER', default='postgres')}:"
            f"{env.str('POSTGRES_PASSWORD', default='postgres')}@"
            f"{env.str('POSTGRES_HOST', default='localhost')}:"
            f"{env.str('POSTGRES_PORT', default='5432')}/"
            f"{env.str('POSTGRES_DB', default='estuairefleet')}"
        ),
    ),
}
DATABASES["default"]["ATOMIC_REQUESTS"] = True
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

ESTUAIREFLEET_SIGNAL_TTL_MINUTES = env.int("ESTUAIREFLEET_SIGNAL_TTL_MINUTES", default=20)
ESTUAIREFLEET_SIGNAL_MAX_RENEWALS = env.int("ESTUAIREFLEET_SIGNAL_MAX_RENEWALS", default=3)
ESTUAIREFLEET_GEOFENCE_RADIUS_M = env.int("ESTUAIREFLEET_GEOFENCE_RADIUS_M", default=500)
ESTUAIREFLEET_ALERT_THRESHOLD_DEFAULT = env.int("ESTUAIREFLEET_ALERT_THRESHOLD_DEFAULT", default=5)
ESTUAIREFLEET_ABUSE_WARNINGS_BEFORE_SUSPENSION = env.int("ESTUAIREFLEET_ABUSE_WARNINGS_BEFORE_SUSPENSION", default=2)
ESTUAIREFLEET_SUSPENSION_HOURS = env.int("ESTUAIREFLEET_SUSPENSION_HOURS", default=24)
ESTUAIREFLEET_BUS_POSITION_STALE_SECONDS = env.int("ESTUAIREFLEET_BUS_POSITION_STALE_SECONDS", default=60)
ESTUAIREFLEET_POLL_INTERVAL_SECONDS = env.int("ESTUAIREFLEET_POLL_INTERVAL_SECONDS", default=5)
ESTUAIREFLEET_POSITION_RETENTION_DAYS = env.int("ESTUAIREFLEET_POSITION_RETENTION_DAYS", default=30)
ESTUAIREFLEET_AVG_BUS_SPEED_KMH = env.int("ESTUAIREFLEET_AVG_BUS_SPEED_KMH", default=20)
ESTUAIREFLEET_OTP_EXPIRY_MINUTES = env.int("ESTUAIREFLEET_OTP_EXPIRY_MINUTES", default=10)
ESTUAIREFLEET_OTP_MAX_ATTEMPTS = env.int("ESTUAIREFLEET_OTP_MAX_ATTEMPTS", default=5)
ESTUAIREFLEET_OTP_SESSION_AGE_SECONDS = env.int("ESTUAIREFLEET_OTP_SESSION_AGE_SECONDS", default=3600)

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

DJANGO_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.sites",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.admin",
    "django.forms",
]
THIRD_PARTY_APPS = [
    "allauth",
    "allauth.account",
    "django_celery_beat",
    "rest_framework",
    "rest_framework.authtoken",
    "corsheaders",
    "drf_spectacular",
]
LOCAL_APPS = [
    "estuairefleet.core",
    "estuairefleet.users",
    "estuairefleet.fleet",
    "estuairefleet.signals",
    "estuairefleet.alerts",
    "estuairefleet.intercampus",
    "estuairefleet.notifications",
]
INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS
MIGRATION_MODULES = {"sites": "estuairefleet.contrib.sites.migrations"}

AUTH_USER_MODEL = "users.User"
AUTHENTICATION_BACKENDS = [
    "estuairefleet.users.backends.IdentifierBackend",
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]
LOGIN_REDIRECT_URL = "core:home"
LOGIN_URL = "users:login"
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
]
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "estuairefleet.users.middleware.ForcePasswordChangeMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "allauth.account.middleware.AccountMiddleware",
]

STATIC_ROOT = str(BASE_DIR / "staticfiles")
STATIC_URL = "/static/"
STATICFILES_DIRS = [str(APPS_DIR / "static")]
STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
]
MEDIA_ROOT = str(APPS_DIR / "media")
MEDIA_URL = "/media/"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [str(APPS_DIR / "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.i18n",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "django.template.context_processors.tz",
                "estuairefleet.notifications.context_processors.notification_summary",
            ],
        },
    },
]
FORM_RENDERER = "django.forms.renderers.TemplatesSetting"
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
X_FRAME_OPTIONS = "DENY"
EMAIL_BACKEND = env.str("DJANGO_EMAIL_BACKEND", default="django.core.mail.backends.smtp.EmailBackend")
EMAIL_HOST = env.str("EMAIL_HOST", default="localhost")
EMAIL_PORT = env.int("EMAIL_PORT", default=25)
EMAIL_HOST_USER = env.str("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env.str("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=False)
EMAIL_TIMEOUT = 5
DEFAULT_FROM_EMAIL = env.str("DJANGO_DEFAULT_FROM_EMAIL", default="EstuaireFleet <noreply@estuairefleet.local>")
ADMINS = [("INSAM", "transport@insam.cm")]
MANAGERS = ADMINS
ADMIN_URL = env.str("DJANGO_ADMIN_URL", default="admin/")

REDIS_URL = env.str("REDIS_URL", default="redis://localhost:6379/0")
REDIS_SSL = REDIS_URL.startswith("rediss://")
CELERY_TIMEZONE = TIME_ZONE
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_BROKER_USE_SSL = {"ssl_cert_reqs": ssl.CERT_NONE} if REDIS_SSL else None
CELERY_RESULT_EXTENDED = True
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"
CELERY_TASK_ALWAYS_EAGER = False

ACCOUNT_ALLOW_REGISTRATION = env.bool("DJANGO_ACCOUNT_ALLOW_REGISTRATION", default=False)
ACCOUNT_LOGIN_METHODS = {"email"}
ACCOUNT_SIGNUP_FIELDS = ["email*", "password1*", "password2*"]
ACCOUNT_USER_MODEL_USERNAME_FIELD = None
ACCOUNT_EMAIL_VERIFICATION = "optional"
ACCOUNT_ADAPTER = "estuairefleet.users.adapters.AccountAdapter"
ACCOUNT_FORMS = {"signup": "estuairefleet.users.forms.UserSignupForm"}

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.TokenAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 50,
}
CORS_URLS_REGEX = r"^/api/.*$"
SPECTACULAR_SETTINGS = {
    "TITLE": "EstuaireFleet API",
    "DESCRIPTION": "API de préparation de la plateforme transport INSAM.",
    "VERSION": "0.1.0",
    "SERVE_PERMISSIONS": ["rest_framework.permissions.IsAdminUser"],
    "SCHEMA_PATH_PREFIX": "/api/",
}
