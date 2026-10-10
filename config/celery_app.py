import os
from logging.config import dictConfig

from celery import Celery
from celery.signals import setup_logging
from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

app = Celery("estuairefleet")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.conf.beat_schedule = {
    "expire-location-signals": {
        "task": "estuairefleet.signals.tasks.expire_signals",
        "schedule": 60.0,
    },
    "escalate-timed-out-alerts": {
        "task": "estuairefleet.alerts.tasks.escalate_timed_out_alerts",
        "schedule": 60.0,
    },
}


@setup_logging.connect
def config_loggers(*args, **kwargs):
    dictConfig(settings.LOGGING)


app.autodiscover_tasks()
