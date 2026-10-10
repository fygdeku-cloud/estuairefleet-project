from celery import shared_task
from django.utils import timezone

from .models import Alert, AlertStatus
from .services import escalate_alert


@shared_task
def escalate_timed_out_alerts():
    alerts = Alert.objects.filter(
        status=AlertStatus.TRIGGERED,
        response_deadline__lte=timezone.now(),
    )
    for alert in alerts:
        escalate_alert(alert=alert)
    return alerts.count()
