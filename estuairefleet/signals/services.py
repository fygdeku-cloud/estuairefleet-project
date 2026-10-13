from datetime import timedelta

from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError, connections, transaction
from django.utils import timezone

from estuairefleet.core import conf
from estuairefleet.core.exceptions import (
    ActiveSignalExists,
    ConsentRequired,
    OutOfZone,
    RateLimitExceeded,
    RenewalLimitReached,
)
from estuairefleet.users.services import register_abuse_warning

from .events import signal_emitted, signal_state_changed
from .models import Signal, SignalStatus
from .selectors import get_active_signal_for_student, resolve_trajet_for_position


def _profile(student):
    return student.student if hasattr(student, "student") else student


def _notify(event, signal):
    connections["default"].on_commit(lambda: event.send(sender=Signal, signal=signal))


@transaction.atomic
def emit_signal(*, student, lat=None, lng=None, accuracy=None, trajet=None, route=None, latitude=None, longitude=None):
    """Émet un signal actif après consentement et contrôle géographique."""
    lat = lat if lat is not None else latitude
    lng = lng if lng is not None else longitude
    legacy_route = route is not None and trajet is None
    student = _profile(student)
    locked_student = type(student).objects.select_for_update().select_related("user").get(pk=student.pk)
    if not locked_student.user.is_active:
        raise PermissionDenied("Ce compte n'est pas actif.")
    if not locked_student.has_location_consent:
        raise ConsentRequired("Le consentement de géolocalisation est requis avant l'émission.")
    if locked_student.is_signal_suspended:
        end = timezone.localtime(locked_student.signals_suspended_until)
        raise PermissionDenied(f"Les signaux sont suspendus jusqu'au {end:%d/%m/%Y à %H:%M}.")
    key = f"signal-attempts:{locked_student.pk}:{timezone.now():%Y%m%d%H%M}"
    attempts = cache.get(key, 0)
    if attempts >= 5:
        raise RateLimitExceeded("Trop de tentatives en une minute. Veuillez patienter.")
    cache.set(key, attempts + 1, timeout=60)
    now = timezone.now()
    Signal.objects.filter(student=locked_student, status=SignalStatus.ACTIF, expires_at__lte=now).update(
        status=SignalStatus.EXPIRE, updated_at=now
    )
    existing = get_active_signal_for_student(locked_student)
    if existing:
        if legacy_route:
            existing.position_lat, existing.position_lng = lat, lng
            existing.expires_at = timezone.now() + timedelta(minutes=existing.trajet.signal_ttl_minutes)
            existing.save(update_fields=["position_lat", "position_lng", "expires_at", "updated_at"])
            return existing
        raise ActiveSignalExists("Vous avez déjà un signal actif.")
    trajet = trajet or route
    if trajet is None:
        candidates = resolve_trajet_for_position(locked_student, lat, lng)
        if not candidates:
            raise OutOfZone("Vous êtes hors de la zone de ramassage. Rapprochez-vous d'un arrêt.")
        trajet = candidates[0]
    elif trajet not in resolve_trajet_for_position(locked_student, lat, lng):
        raise OutOfZone("Vous êtes hors de la zone du trajet sélectionné.")
    try:
        signal = Signal.objects.create(
            student=locked_student,
            trajet=trajet,
            position_lat=lat,
            position_lng=lng,
            accuracy_m=accuracy,
            status=SignalStatus.ACTIF,
            expires_at=timezone.now() + timedelta(minutes=trajet.signal_ttl_minutes),
        )
    except IntegrityError as exc:
        raise ActiveSignalExists("Vous avez déjà un signal actif.") from exc
    _notify(signal_emitted, signal)
    _notify(signal_state_changed, signal)
    return signal


@transaction.atomic
def cancel_signal(*, signal, by):
    if not (by.is_superuser or by.role in {"admin", "administrator"} or signal.student.user_id == by.id):
        raise PermissionDenied("Vous ne pouvez annuler que votre propre signal.")
    locked = Signal.objects.select_for_update().get(pk=signal.pk)
    if locked.status == SignalStatus.ACTIF:
        locked.status = SignalStatus.ANNULE
        locked.save(update_fields=["status", "updated_at"])
        _notify(signal_state_changed, locked)
    return locked


@transaction.atomic
def renew_signal(*, signal, by):
    if signal.student.user_id != by.id:
        raise PermissionDenied("Vous ne pouvez renouveler que votre propre signal.")
    locked = Signal.objects.select_for_update().select_related("trajet").get(pk=signal.pk)
    if locked.status != SignalStatus.ACTIF or locked.expires_at <= timezone.now():
        raise PermissionDenied("Ce signal n'est plus actif.")
    if locked.renewed_count >= conf.SIGNAL_MAX_RENEWALS:
        raise RenewalLimitReached("La limite de renouvellements est atteinte.")
    locked.renewed_count += 1
    locked.expires_at = timezone.now() + timedelta(minutes=locked.trajet.signal_ttl_minutes)
    locked.save(update_fields=["renewed_count", "expires_at", "updated_at"])
    return locked


@transaction.atomic
def close_signal(*, signal, by, bus=None):
    locked = Signal.objects.select_for_update().select_related("trajet", "student").get(pk=signal.pk)
    is_admin = by.is_superuser or by.role in {"admin", "administrator"}
    if not is_admin:
        if (
            by.role != "driver"
            or not getattr(by, "chauffeur", None)
            or not by.chauffeur.bus
            or by.chauffeur.bus.trajet_id != locked.trajet_id
        ):
            raise PermissionDenied("Seul le chauffeur du trajet concerné peut clôturer ce signal.")
        bus = bus or by.chauffeur.bus
    if locked.status == SignalStatus.ACTIF:
        locked.status = SignalStatus.PRIS_EN_CHARGE
        locked.taken_at, locked.taken_by_bus, locked.closed_by = timezone.now(), bus, by
        locked.save(update_fields=["status", "taken_at", "taken_by_bus", "closed_by", "updated_at"])
        _notify(signal_state_changed, locked)
    return locked


@transaction.atomic
def close_signals_for_trajet(*, trajet, by, bus=None):
    signals = list(Signal.objects.select_for_update().filter(trajet=trajet, status=SignalStatus.ACTIF))
    for signal in signals:
        close_signal(signal=signal, by=by, bus=bus)
    return len(signals)


@transaction.atomic
def expire_signal(signal):
    locked = Signal.objects.select_for_update().get(pk=signal.pk)
    if locked.status == SignalStatus.ACTIF and locked.expires_at <= timezone.now():
        locked.status = SignalStatus.EXPIRE
        locked.save(update_fields=["status", "updated_at"])
        _notify(signal_state_changed, locked)
    return locked


@transaction.atomic
def expire_stale_signals(now=None):
    now = now or timezone.now()
    signals = list(Signal.objects.select_for_update().filter(status=SignalStatus.ACTIF, expires_at__lte=now))
    for signal in signals:
        signal.status = SignalStatus.EXPIRE
        signal.save(update_fields=["status", "updated_at"])
    return len(signals)


@transaction.atomic
def flag_false_signal(*, signal, by):
    is_admin = by.is_superuser or by.role in {"admin", "administrator"}
    if not is_admin and (
        by.role != "driver" or not getattr(by, "chauffeur", None) or by.chauffeur.bus.trajet_id != signal.trajet_id
    ):
        raise PermissionDenied("Seul le chauffeur du trajet concerné peut signaler un point introuvable.")
    locked = Signal.objects.select_for_update().select_related("student").get(pk=signal.pk)
    locked.flagged_false, locked.flagged_by, locked.flagged_at = True, by, timezone.now()
    locked.status = SignalStatus.ANNULE
    locked.save(update_fields=["flagged_false", "flagged_by", "flagged_at", "status", "updated_at"])
    register_abuse_warning(student=locked.student)
    _notify(signal_state_changed, locked)
    return locked


@transaction.atomic
def purge_old_positions(now=None):
    threshold = (now or timezone.now()) - timedelta(days=conf.POSITION_RETENTION_DAYS)
    return Signal.objects.filter(created_at__lt=threshold, position_lat__isnull=False).update(
        position_lat=None, position_lng=None, accuracy_m=None
    )
