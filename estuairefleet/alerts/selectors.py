from django.db.models import F, QuerySet
from django.utils import timezone

from estuairefleet.core.geo import haversine_m
from estuairefleet.fleet.models import Bus
from estuairefleet.fleet.selectors import get_nearest_available_bus
from estuairefleet.signals.models import SignalStatus

from .models import Alert, AlertStatus, AlertThresholdSchedule

OPEN_ALERT_STATUSES = (
    AlertStatus.PENDING,
    AlertStatus.TRIGGERED,
    AlertStatus.IN_PROGRESS,
    AlertStatus.RELAY,
    AlertStatus.ESCALATED,
)


def get_open_alerts() -> QuerySet[Alert]:
    return Alert.objects.filter(status__in=OPEN_ALERT_STATUSES).select_related("route").prefetch_related("signals")


def get_alerts_for_driver(driver) -> QuerySet[Alert]:
    return get_open_alerts().filter(route__buses__chauffeur__user=driver).distinct()


def get_active_signal_count(route) -> int:
    return route.signals.filter(status=SignalStatus.ACTIF, expires_at__gt=timezone.now()).count()


def get_relay_bus_proposal(alert: Alert):
    signal = alert.signals.filter(status=SignalStatus.ACTIF).order_by("created_at").first()
    if not signal or signal.position_lat is None or signal.position_lng is None:
        return None
    return get_nearest_available_bus(latitude=signal.position_lat, longitude=signal.position_lng)


def get_alert_detail(alert_id, *, driver=None) -> Alert:
    queryset = get_open_alerts().select_related("route", "response")
    if driver is not None:
        queryset = queryset.filter(route__buses__chauffeur__user=driver)
    return queryset.get(pk=alert_id)


def get_threshold_for_route(route, *, at=None):
    at = at or timezone.localtime()
    for schedule in AlertThresholdSchedule.objects.filter(route=route, is_active=True).order_by("start_time"):
        if schedule.matches(at.time()):
            return schedule.threshold
    return route.seuil_alerte


def get_next_relay_bus(alert, *, excluded_ids=()):
    signal = alert.signals.filter(status=SignalStatus.ACTIF).order_by("created_at").first()
    if not signal or signal.position_lat is None or signal.position_lng is None:
        return None
    excluded = set(excluded_ids) | set(alert.route.buses.values_list("pk", flat=True))
    candidates = (
        Bus.objects.filter(
            status__in=("disponible", "en_route"),
            chauffeur__isnull=False,
            places_occupees__lt=F("capacity"),
            position_lat__isnull=False,
            position_lng__isnull=False,
        )
        .exclude(pk__in=excluded)
        .select_related("chauffeur__user")
    )
    return min(
        candidates,
        key=lambda bus: haversine_m(
            (float(signal.position_lat), float(signal.position_lng)),
            (bus.position_lat, bus.position_lng),
        ),
        default=None,
    )
