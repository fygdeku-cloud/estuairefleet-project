from datetime import timedelta

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from estuairefleet.core.constants import INTERMEDIATE_ALERT_DELAY
from estuairefleet.signals.selectors import get_active_signals_for_route

from .models import Alert, AlertResponse, AlertStatus, DriverResponseType


@transaction.atomic
def evaluate_route_alert(*, route) -> Alert | None:
    active_signals = get_active_signals_for_route(route.pk).select_for_update()
    count = active_signals.count()
    oldest_waiting = active_signals.order_by("created_at").first()
    intermediate = oldest_waiting and oldest_waiting.created_at <= timezone.now() - INTERMEDIATE_ALERT_DELAY
    if count < route.alert_threshold and not intermediate:
        return None
    alert = Alert.objects.filter(
        route=route,
        status__in=(AlertStatus.PENDING, AlertStatus.TRIGGERED, AlertStatus.IN_PROGRESS, AlertStatus.ESCALATED),
    ).first()
    if not alert:
        alert = Alert.objects.create(
            route=route,
            threshold=route.alert_threshold,
            status=AlertStatus.TRIGGERED,
            priority=count >= route.alert_threshold,
            response_deadline=timezone.now() + timedelta(minutes=5),
            signal_count=count,
        )
    else:
        alert.signal_count = count
        alert.priority = alert.priority or count >= route.alert_threshold
        alert.save(update_fields=["signal_count", "priority", "updated_at"])
    alert.signals.set(active_signals)
    return alert


@transaction.atomic
def respond_to_alert(*, alert: Alert, driver, response_type, eta_minutes=None, reason="", relay_bus=None):
    if not alert.route.buses.filter(driver=driver).exists():
        raise PermissionDenied("Cette alerte ne concerne pas votre bus.")
    if alert.status not in (AlertStatus.TRIGGERED, AlertStatus.ESCALATED):
        raise ValidationError("Cette alerte n'accepte plus de réponse.")
    response = AlertResponse(
        alert=alert,
        driver=driver,
        response_type=response_type,
        eta_minutes=eta_minutes,
        reason=reason,
        relay_bus=relay_bus,
    )
    response.full_clean()
    response.save()
    alert.status = AlertStatus.IN_PROGRESS
    alert.save(update_fields=["status", "updated_at"])
    return response


@transaction.atomic
def escalate_alert(*, alert: Alert) -> Alert:
    if alert.status in (AlertStatus.RESOLVED, AlertStatus.ESCALATED):
        return alert
    alert.status = AlertStatus.ESCALATED
    alert.escalated_at = timezone.now()
    alert.save(update_fields=["status", "escalated_at", "updated_at"])
    return alert


def validate_response_type(value):
    if value not in DriverResponseType.values:
        raise ValidationError("Réponse chauffeur non reconnue.")
