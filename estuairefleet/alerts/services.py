from datetime import timedelta

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from estuairefleet.core.constants import INTERMEDIATE_ALERT_DELAY
from estuairefleet.notifications.services import create_in_app_notification
from estuairefleet.signals.selectors import get_active_signals_for_trajet

from .models import Alert, AlertResponse, AlertStatus, DriverResponseType
from .selectors import OPEN_ALERT_STATUSES


def _is_transport_admin(user):
    return bool(user and (user.is_superuser or user.role in {"admin", "administrator"}))


@transaction.atomic
def evaluate_route_alert(*, route) -> Alert | None:
    locked_route = type(route).objects.select_for_update().get(pk=route.pk)
    active_signals = get_active_signals_for_trajet(locked_route).select_for_update()
    count = active_signals.count()
    oldest_waiting = active_signals.order_by("created_at").first()
    intermediate = bool(oldest_waiting and oldest_waiting.created_at <= timezone.now() - INTERMEDIATE_ALERT_DELAY)
    if count < locked_route.seuil_alerte and not intermediate:
        return None

    alert = Alert.objects.select_for_update().filter(route=locked_route, status__in=OPEN_ALERT_STATUSES).first()
    now = timezone.now()
    if alert is None:
        alert = Alert.objects.create(
            route=locked_route,
            threshold=locked_route.seuil_alerte,
            status=AlertStatus.TRIGGERED,
            priority=count >= locked_route.seuil_alerte,
            response_deadline=now + timedelta(minutes=5),
            signal_count=count,
        )
        drivers = [bus.chauffeur.user for bus in locked_route.buses.select_related("chauffeur__user") if bus.chauffeur]
        for driver in drivers:
            create_in_app_notification(
                recipient=driver,
                title="Nouvelle alerte sur votre trajet",
                message=f"{count} signal(s) actif(s) attendent sur {locked_route.name}.",
                metadata={"alert_id": str(alert.pk), "route_id": str(locked_route.pk)},
            )
    else:
        alert.signal_count = count
        alert.priority = alert.priority or count >= locked_route.seuil_alerte
        alert.save(update_fields=["signal_count", "priority", "updated_at"])
    alert.signals.set(active_signals)
    return alert


@transaction.atomic
def respond_to_alert(*, alert: Alert, driver, response_type, eta_minutes=None, reason="", relay_bus=None):
    locked = Alert.objects.select_for_update().select_related("route").get(pk=alert.pk)
    if not locked.route.buses.filter(chauffeur__user=driver).exists():
        raise PermissionDenied("Cette alerte ne concerne pas votre bus.")
    if locked.status not in (AlertStatus.TRIGGERED, AlertStatus.ESCALATED):
        raise ValidationError("Cette alerte n'accepte plus de réponse.")
    response = AlertResponse(
        alert=locked,
        driver=driver,
        response_type=response_type,
        eta_minutes=eta_minutes,
        reason=reason,
        relay_bus=relay_bus,
    )
    response.full_clean()
    response.save()
    locked.status = AlertStatus.IN_PROGRESS
    locked.save(update_fields=["status", "updated_at"])
    return response


@transaction.atomic
def escalate_alert(*, alert: Alert) -> Alert:
    locked = Alert.objects.select_for_update().get(pk=alert.pk)
    if locked.status in (AlertStatus.RESOLVED, AlertStatus.ESCALATED):
        return locked
    locked.status = AlertStatus.ESCALATED
    locked.escalated_at = timezone.now()
    locked.save(update_fields=["status", "escalated_at", "updated_at"])
    return locked


@transaction.atomic
def resolve_alert(*, alert: Alert, by) -> Alert:
    if not _is_transport_admin(by):
        raise PermissionDenied("Seul un responsable transport peut clôturer une alerte.")
    locked = Alert.objects.select_for_update().get(pk=alert.pk)
    locked.mark_resolved()
    return locked


def validate_response_type(value):
    if value not in DriverResponseType.values:
        raise ValidationError("Réponse chauffeur non reconnue.")
