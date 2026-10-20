from celery import shared_task
from django.utils import timezone

from estuairefleet.fleet.models import Trajet
from estuairefleet.signals.models import Signal, SignalStatus

from .models import Alert, AlertStatus
from .services import escalate_alert, evaluate_route_alert


@shared_task
def escalate_timed_out_alerts():
    alerts = Alert.objects.filter(
        status__in=(AlertStatus.TRIGGERED, AlertStatus.IN_PROGRESS, AlertStatus.RELAY),
        response_deadline__isnull=False,
        response_deadline__lte=timezone.now(),
    ).order_by("response_deadline")[:100]
    count = 0
    for alert in alerts.iterator(chunk_size=100):
        escalate_alert(alert=alert)
        count += 1
    return count


@shared_task
def evaluate_active_routes():
    count = 0
    route_ids = (
        Signal.objects.filter(status=SignalStatus.ACTIF, expires_at__gt=timezone.now(), trajet__is_active=True)
        .values_list("trajet_id", flat=True)
        .distinct()
    )
    for route in Trajet.objects.filter(pk__in=route_ids).only("pk").iterator(chunk_size=100):
        if evaluate_route_alert(route=route) is not None:
            count += 1
    return count
