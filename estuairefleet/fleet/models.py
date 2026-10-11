from uuid import uuid4

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from estuairefleet.core import conf
from estuairefleet.core.geo import is_valid_lat_lng
from estuairefleet.core.models import BaseModel

from .validators import validate_days_of_week, validate_horaires, validate_itinerary


def _default_trajet_code():
    return f"trajet-{uuid4().hex[:10]}"


class Direction(models.TextChoices):
    ALLER = "aller", _("Aller")
    RETOUR = "retour", _("Retour")


class BusStatus(models.TextChoices):
    HORS_SERVICE = "hors_service", _("Hors service")
    DISPONIBLE = "disponible", _("Disponible")
    EN_ROUTE = "en_route", _("En route")
    PLEIN = "plein", _("Plein")
    INDISPONIBLE = "indisponible", _("Indisponible")


class Campus(BaseModel):
    name = models.CharField(_("nom"), max_length=120)
    code = models.SlugField(_("code"), max_length=32, unique=True)
    address = models.CharField(_("adresse"), max_length=255, blank=True)
    latitude = models.DecimalField(_("latitude"), max_digits=9, decimal_places=6)
    longitude = models.DecimalField(_("longitude"), max_digits=9, decimal_places=6)
    radius_m = models.PositiveIntegerField(_("rayon de géorepérage (m)"), default=conf.GEOFENCE_RADIUS_M)
    is_active = models.BooleanField(_("actif"), default=True)

    class Meta:
        verbose_name = _("campus")
        verbose_name_plural = _("campus")
        ordering = ("name",)

    def clean(self):
        if not is_valid_lat_lng(self.latitude, self.longitude):
            raise ValidationError(_("Les coordonnées du campus sont invalides."))

    @property
    def point(self):
        return float(self.latitude), float(self.longitude)

    @property
    def geofence_radius_m(self):
        return self.radius_m

    def __str__(self):
        return f"{self.code} — {self.name}"


class Trajet(BaseModel):
    name = models.CharField(_("nom"), max_length=150)
    code = models.SlugField(_("code"), max_length=40, unique=True, default=_default_trajet_code)
    direction = models.CharField(_("sens"), max_length=10, choices=Direction.choices, default=Direction.ALLER)
    campuses = models.ManyToManyField(Campus, related_name="trajets", blank=True, verbose_name=_("campus desservis"))
    itinerary = models.JSONField(_("itinéraire"), default=list, validators=[validate_itinerary])
    horaires = models.JSONField(_("horaires"), default=list, validators=[validate_horaires])
    service_start = models.TimeField(_("début du service"), null=True, blank=True)
    service_end = models.TimeField(_("fin du service"), null=True, blank=True)
    days_of_week = models.JSONField(_("jours de service"), default=list, validators=[validate_days_of_week])
    seuil_alerte = models.PositiveIntegerField(_("seuil d'alerte"), default=conf.ALERT_THRESHOLD_DEFAULT)
    signal_ttl_minutes = models.PositiveIntegerField(
        _("durée de vie du signal (minutes)"), default=conf.SIGNAL_TTL_MINUTES
    )
    geofence_radius_m = models.PositiveIntegerField(_("rayon de géorepérage (m)"), default=conf.GEOFENCE_RADIUS_M)
    is_active = models.BooleanField(_("actif"), default=True)

    class Meta:
        verbose_name = _("trajet")
        verbose_name_plural = _("trajets")
        ordering = ("name", "direction")

    def __init__(self, *args, **kwargs):
        if "route_type" in kwargs and "direction" not in kwargs:
            kwargs["direction"] = Direction.ALLER if kwargs.pop("route_type") == "outbound" else Direction.RETOUR
        if "alert_threshold" in kwargs and "seuil_alerte" not in kwargs:
            kwargs["seuil_alerte"] = kwargs.pop("alert_threshold")
        if "signal_lifetime_minutes" in kwargs and "signal_ttl_minutes" not in kwargs:
            kwargs["signal_ttl_minutes"] = kwargs.pop("signal_lifetime_minutes")
        super().__init__(*args, **kwargs)

    def clean(self):
        if self.seuil_alerte < 1:
            raise ValidationError({"seuil_alerte": _("Le seuil doit être supérieur à zéro.")})
        if self.service_start and self.service_end and self.service_start == self.service_end:
            raise ValidationError({"service_end": _("La plage horaire doit avoir une durée positive.")})

    def is_in_service(self, now=None):
        now = now or timezone.localtime()
        if not self.is_active or (self.days_of_week and now.weekday() not in self.days_of_week):
            return False
        if not self.service_start or not self.service_end:
            return True
        current = now.time()
        return (
            self.service_start <= current <= self.service_end
            if self.service_start <= self.service_end
            else current >= self.service_start or current <= self.service_end
        )

    @property
    def polyline(self):
        return self.itinerary or []

    @property
    def route_type(self):
        return self.direction

    @property
    def alert_threshold(self):
        return self.seuil_alerte

    @property
    def signal_lifetime_minutes(self):
        return self.signal_ttl_minutes

    def __str__(self):
        return self.name


class Stop(BaseModel):
    trajet = models.ForeignKey(Trajet, on_delete=models.CASCADE, related_name="stops", verbose_name=_("trajet"))
    name = models.CharField(_("nom"), max_length=120)
    latitude = models.DecimalField(_("latitude"), max_digits=9, decimal_places=6)
    longitude = models.DecimalField(_("longitude"), max_digits=9, decimal_places=6)
    order = models.PositiveIntegerField(_("ordre"))

    class Meta:
        verbose_name = _("arrêt")
        verbose_name_plural = _("arrêts")
        ordering = ("order",)
        constraints = [models.UniqueConstraint(fields=("trajet", "order"), name="unique_stop_order_per_trajet")]
        indexes = [models.Index(fields=("trajet", "order"))]

    @property
    def point(self):
        return float(self.latitude), float(self.longitude)

    def __str__(self):
        return f"{self.order}. {self.name}"


class Bus(BaseModel):
    plate_number = models.CharField(_("immatriculation"), max_length=32, unique=True, default="UNKNOWN")
    label = models.CharField(_("nom interne"), max_length=80, blank=True)
    capacity = models.PositiveIntegerField(_("capacité"))
    status = models.CharField(_("statut"), max_length=20, choices=BusStatus.choices, default=BusStatus.HORS_SERVICE)
    chauffeur = models.OneToOneField(
        "users.Chauffeur",
        on_delete=models.SET_NULL,
        related_name="bus",
        null=True,
        blank=True,
        verbose_name=_("chauffeur"),
    )
    trajet = models.ForeignKey(
        Trajet, on_delete=models.SET_NULL, related_name="buses", null=True, blank=True, verbose_name=_("trajet")
    )
    position_lat = models.DecimalField(_("latitude actuelle"), max_digits=9, decimal_places=6, null=True, blank=True)
    position_lng = models.DecimalField(_("longitude actuelle"), max_digits=9, decimal_places=6, null=True, blank=True)
    position_updated_at = models.DateTimeField(_("position mise à jour le"), null=True, blank=True)
    eta = models.DateTimeField(_("arrivée estimée"), null=True, blank=True)
    places_occupees = models.PositiveIntegerField(_("places occupées"), default=0)
    status_changed_at = models.DateTimeField(_("statut modifié le"), null=True, blank=True)

    class Meta:
        verbose_name = _("bus")
        verbose_name_plural = _("bus")
        ordering = ("plate_number",)
        constraints = [
            models.CheckConstraint(condition=models.Q(capacity__gt=0), name="bus_capacity_positive"),
            models.CheckConstraint(condition=models.Q(places_occupees__gte=0), name="bus_occupancy_positive"),
        ]
        indexes = [models.Index(fields=("status",)), models.Index(fields=("trajet", "status"))]

    def clean(self):
        errors = {}
        if self.capacity <= 0:
            errors["capacity"] = _("La capacité doit être supérieure à zéro.")
        if self.places_occupees > self.capacity:
            errors["places_occupees"] = _("Les places occupées ne peuvent pas dépasser la capacité.")
        if (
            self.position_lat is not None
            and self.position_lng is not None
            and not is_valid_lat_lng(self.position_lat, self.position_lng)
        ):
            errors["position_lat"] = _("La position du bus est invalide.")
        if errors:
            raise ValidationError(errors)

    @property
    def is_full(self):
        return self.places_occupees >= self.capacity

    @property
    def free_seats(self):
        return max(self.capacity - self.places_occupees, 0)

    @property
    def available_seats(self):
        return self.free_seats

    def has_fresh_position(self, now=None):
        now = now or timezone.now()
        return bool(
            self.position_updated_at
            and (now - self.position_updated_at).total_seconds() <= conf.BUS_POSITION_STALE_SECONDS
        )

    @property
    def registration_number(self):
        return self.plate_number

    @property
    def name(self):
        return self.label

    @property
    def occupied_seats(self):
        return self.places_occupees

    def __str__(self):
        return self.label or self.plate_number
