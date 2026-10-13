from celery import shared_task
from django.utils import timezone

from .models import Alert, AlertStatus
from .services import escalate_alert


@shared_task
def escalate_timed_out_alerts():
    alerts = Alert.objects.filter(
        status=AlertStatus.TRIGGERED,
        response_deadline__isnull=False,
        response_deadline__lte=timezone.now(),
    )
    count = 0
    for alert in alerts:
        escalate_alert(alert=alert)
        count += 1
    return count
