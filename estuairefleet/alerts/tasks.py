from celery import shared_task
from django.utils import timezone

from estuairefleet.fleet.models import Trajet

from .models import Alert, AlertStatus
from .services import escalate_alert, evaluate_route_alert


@shared_task
def escalate_timed_out_alerts():
    alerts = Alert.objects.filter(
        status__in=(AlertStatus.TRIGGERED, AlertStatus.IN_PROGRESS, AlertStatus.RELAY),
        response_deadline__isnull=False,
        response_deadline__lte=timezone.now(),
    )
    count = 0
    for alert in alerts:
        escalate_alert(alert=alert)
        count += 1
    return count


@shared_task
def evaluate_active_routes():
    count = 0
    for route in Trajet.objects.filter(is_active=True):
        if evaluate_route_alert(route=route) is not None:
            count += 1
    return count
