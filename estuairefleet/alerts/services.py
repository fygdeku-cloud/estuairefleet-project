from datetime import timedelta

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from estuairefleet.core import conf
from estuairefleet.core.constants import INTERMEDIATE_ALERT_DELAY
from estuairefleet.notifications.services import create_in_app_notification
from estuairefleet.signals.selectors import get_active_signals_for_trajet

from .models import Alert, AlertRelayAttempt, AlertResponse, AlertStatus, DriverResponseType
from .selectors import OPEN_ALERT_STATUSES, get_next_relay_bus, get_threshold_for_route


def _is_transport_admin(user):
    return bool(user and (user.is_superuser or user.role in {"admin", "administrator"}))


@transaction.atomic
def evaluate_route_alert(*, route) -> Alert | None:
    locked_route = type(route).objects.select_for_update().get(pk=route.pk)
    active_signals = get_active_signals_for_trajet(locked_route).select_for_update()
    count = active_signals.count()
    threshold = get_threshold_for_route(locked_route)
    oldest_waiting = active_signals.order_by("created_at").first()
    intermediate = bool(oldest_waiting and oldest_waiting.created_at <= timezone.now() - INTERMEDIATE_ALERT_DELAY)
    if count < threshold and not intermediate:
        return None

    alert = Alert.objects.select_for_update().filter(route=locked_route, status__in=OPEN_ALERT_STATUSES).first()
    now = timezone.now()
    if alert is None:
        alert = Alert.objects.create(
            route=locked_route,
            threshold=threshold,
            status=AlertStatus.TRIGGERED,
            priority=count >= threshold,
            response_deadline=now + timedelta(minutes=conf.ALERT_RESPONSE_TIMEOUT_MINUTES),
            triggered_at=now,
            signal_count=count,
        )
        drivers = [bus.chauffeur.user for bus in locked_route.buses.select_related("chauffeur__user") if bus.chauffeur]
        for driver in drivers:
            create_in_app_notification(
                recipient=driver,
                title="Nouvelle alerte sur votre trajet",
                message=f"{count} signal(s) actif(s) attendent sur {locked_route.name}.",
                metadata={"alert_id": str(alert.pk), "route_id": str(locked_route.pk)},
                notification_type="alert",
                event_key=f"alert:{alert.pk}:driver:{driver.pk}:created",
            )
    else:
        alert.signal_count = count
        alert.priority = alert.priority or count >= threshold
        alert.save(update_fields=["signal_count", "priority", "updated_at"])
    alert.signals.set(active_signals)
    return alert


@transaction.atomic
def respond_to_alert(*, alert: Alert, driver, response_type, eta_minutes=None, reason="", relay_bus=None):
    locked = Alert.objects.select_for_update().select_related("route").get(pk=alert.pk)
    is_route_driver = locked.route.buses.filter(chauffeur__user=driver).exists()
    is_relay_driver = bool(
        locked.relay_bus_id and locked.relay_bus.chauffeur and locked.relay_bus.chauffeur.user_id == driver.pk
    )
    if not (is_route_driver or is_relay_driver):
        raise PermissionDenied("Cette alerte ne concerne pas votre bus.")
    if locked.status not in (AlertStatus.TRIGGERED, AlertStatus.IN_PROGRESS, AlertStatus.ESCALATED, AlertStatus.RELAY):
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
    existing_response = AlertResponse.objects.filter(alert=locked).first()
    if existing_response:
        response.pk = existing_response.pk
        response.responded_at = existing_response.responded_at
    response.save()
    if response_type == DriverResponseType.ARRIVING:
        locked.status = AlertStatus.RESOLVED
        locked.resolved_at = timezone.now()
        locked.save(update_fields=["status", "resolved_at", "updated_at"])
        _notify_waiting_students(
            locked,
            "Votre signal a été pris en charge par le chauffeur.",
            notification_type="signal_taken",
            event_suffix=f"taken:{driver.pk}",
        )
        _notify_transport_admins(
            title="Réponse chauffeur enregistrée",
            message=f"Le chauffeur a accepté l'alerte du trajet {locked.route.name}.",
            alert=locked,
            event_suffix=f"response:{driver.pk}",
        )
    else:
        locked.status = AlertStatus.RELAY
        locked.motif = reason
        locked.relay_bus = relay_bus
        locked.response_deadline = timezone.now() + timedelta(minutes=conf.ALERT_RESPONSE_TIMEOUT_MINUTES)
        locked.save(update_fields=["status", "motif", "relay_bus", "response_deadline", "updated_at"])
        if relay_bus and relay_bus.chauffeur:
            AlertRelayAttempt.objects.get_or_create(alert=locked, bus=relay_bus)
            create_in_app_notification(
                recipient=relay_bus.chauffeur.user,
                title="Demande de relais prioritaire",
                message=f"Un relais est demandé pour le trajet {locked.route.name}.",
                metadata={"alert_id": str(locked.pk), "relay": True},
                notification_type="alert",
                event_key=f"alert:{locked.pk}:relay:{relay_bus.pk}",
            )
        _notify_transport_admins(
            title="Chauffeur indisponible",
            message=f"Un relais est demandé pour le trajet {locked.route.name}.",
            alert=locked,
            event_suffix=f"unavailable:{driver.pk}",
        )
    return response


@transaction.atomic
def escalate_alert(*, alert: Alert) -> Alert:
    locked = Alert.objects.select_for_update().get(pk=alert.pk)
    if locked.status == AlertStatus.RESOLVED:
        return locked
    if locked.response_deadline and locked.response_deadline > timezone.now():
        return locked
    if locked.status == AlertStatus.RELAY:
        relay_bus = get_next_relay_bus(locked, excluded_ids=locked.relay_attempts.values_list("bus_id", flat=True))
        if relay_bus:
            locked.relay_bus = relay_bus
            locked.response_deadline = timezone.now() + timedelta(minutes=conf.ALERT_RESPONSE_TIMEOUT_MINUTES)
            locked.save(update_fields=["relay_bus", "response_deadline", "updated_at"])
            AlertRelayAttempt.objects.get_or_create(alert=locked, bus=relay_bus)
            create_in_app_notification(
                recipient=relay_bus.chauffeur.user,
                title="Demande de relais prioritaire",
                message=f"Un relais est demandé pour le trajet {locked.route.name}.",
                metadata={"alert_id": str(locked.pk), "relay": True},
                notification_type="alert",
                event_key=f"alert:{locked.pk}:relay:{relay_bus.pk}",
            )
            return locked
    locked.status = AlertStatus.ESCALATED
    locked.escalated_at = timezone.now()
    locked.save(update_fields=["status", "escalated_at", "updated_at"])
    _notify_waiting_students(
        locked,
        "La prise en charge de votre signal est escaladée au responsable transport.",
        notification_type="escalation",
        event_suffix="escalated",
    )
    _notify_transport_admins(
        title="Alerte escaladée",
        message=f"Aucune réponse n'a été reçue pour le trajet {locked.route.name}.",
        alert=locked,
        event_suffix="escalated",
    )
    return locked


@transaction.atomic
def respond_to_relay(*, alert, driver, accepted, reason=""):
    locked = Alert.objects.select_for_update().select_related("relay_bus__chauffeur").get(pk=alert.pk)
    if not locked.relay_bus or not locked.relay_bus.chauffeur or locked.relay_bus.chauffeur.user_id != driver.pk:
        raise PermissionDenied("Cette demande de relais ne concerne pas votre bus.")
    attempt = AlertRelayAttempt.objects.select_for_update().get(alert=locked, bus=locked.relay_bus)
    attempt.accepted, attempt.reason, attempt.responded_at = accepted, reason, timezone.now()
    attempt.save(update_fields=["accepted", "reason", "responded_at", "updated_at"])
    if accepted:
        locked.status = AlertStatus.RESOLVED
        locked.resolved_at = timezone.now()
        locked.save(update_fields=["status", "resolved_at", "updated_at"])
        _notify_waiting_students(
            locked,
            "Un bus relais a accepté votre demande.",
            notification_type="signal_taken",
            event_suffix=f"relay-taken:{driver.pk}",
        )
    else:
        locked.response_deadline = timezone.now()
        locked.save(update_fields=["response_deadline", "updated_at"])
        return escalate_alert(alert=locked)
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


def _notify_waiting_students(alert, message, *, notification_type="signal_taken", event_suffix="taken"):
    from estuairefleet.notifications.services import create_in_app_notification

    for signal in alert.signals.filter(status="actif").select_related("student__user"):
        create_in_app_notification(
            recipient=signal.student.user,
            title="Signal pris en charge",
            message=message,
            metadata={"alert_id": str(alert.pk)},
            notification_type=notification_type,
            event_key=f"alert:{alert.pk}:student:{signal.student_id}:{event_suffix}",
        )


def _notify_transport_admins(*, title, message, alert, event_suffix):
    from estuairefleet.users.models import User

    for user in User.objects.filter(is_active=True, role__in=("admin", "administrator", "staff")):
        create_in_app_notification(
            recipient=user,
            title=title,
            message=message,
            metadata={"alert_id": str(alert.pk)},
            notification_type="escalation" if "escalad" in title.lower() else "alert",
            event_key=f"alert:{alert.pk}:admin:{user.pk}:{event_suffix}",
        )
