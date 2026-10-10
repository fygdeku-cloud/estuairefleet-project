from django.db.models import QuerySet
from django.utils import timezone

from estuairefleet.fleet.selectors import get_nearest_available_bus
from estuairefleet.signals.models import SignalStatus

from .models import Alert, AlertStatus


def get_open_alerts() -> QuerySet[Alert]:
    return (
        Alert.objects.filter(
            status__in=(AlertStatus.PENDING, AlertStatus.TRIGGERED, AlertStatus.IN_PROGRESS, AlertStatus.ESCALATED),
        )
        .select_related("route")
        .prefetch_related("signals")
    )


def get_alerts_for_driver(driver) -> QuerySet[Alert]:
    return get_open_alerts().filter(route__buses__driver=driver).distinct()


def get_active_signal_count(route) -> int:
    return route.signals.filter(status=SignalStatus.ACTIVE, expires_at__gt=timezone.now()).count()


def get_relay_bus_proposal(alert: Alert):
    signal = alert.signals.filter(status=SignalStatus.ACTIVE).order_by("created_at").first()
    if not signal:
        return None
    return get_nearest_available_bus(latitude=signal.position_lat, longitude=signal.position_lng)
