from django.db.models import QuerySet
from django.utils import timezone

from estuairefleet.fleet.selectors import get_nearest_available_bus
from estuairefleet.signals.models import SignalStatus

from .models import Alert, AlertStatus

OPEN_ALERT_STATUSES = (
    AlertStatus.PENDING,
    AlertStatus.TRIGGERED,
    AlertStatus.IN_PROGRESS,
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
