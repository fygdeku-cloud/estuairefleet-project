from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from estuairefleet.core.models import BaseModel
from estuairefleet.core.validators import validate_latitude, validate_longitude, validate_positive_integer


class RouteType(models.TextChoices):
    OUTBOUND = "outbound", _("Aller")
    RETURN = "return", _("Retour")


class BusStatus(models.TextChoices):
    OUT_OF_SERVICE = "out_of_service", _("Hors service")
    AVAILABLE = "available", _("Disponible")
    EN_ROUTE = "en_route", _("En route")
    FULL = "full", _("Plein")
    UNAVAILABLE = "unavailable", _("Indisponible")


class Campus(BaseModel):
    code = models.CharField(_("code"), max_length=20, unique=True)
    name = models.CharField(_("nom"), max_length=120)
    address = models.CharField(_("adresse"), max_length=255, blank=True)
    latitude = models.DecimalField(_("latitude"), max_digits=9, decimal_places=6, validators=[validate_latitude])
    longitude = models.DecimalField(_("longitude"), max_digits=9, decimal_places=6, validators=[validate_longitude])
    geofence_radius_m = models.PositiveIntegerField(_("rayon de géorepérage (m)"), default=1000)
    is_active = models.BooleanField(_("actif"), default=True)

    class Meta:
        verbose_name = _("campus")
        verbose_name_plural = _("campus")
        ordering = ("name",)

    def __str__(self):
        return f"{self.code} — {self.name}"


class Trajet(BaseModel):
    name = models.CharField(_("nom"), max_length=150)
    route_type = models.CharField(_("type"), max_length=20, choices=RouteType.choices)
    description = models.TextField(_("description"), blank=True)
    itinerary = models.JSONField(_("itinéraire"), default=list, blank=True)
    stops = models.JSONField(_("arrêts"), default=list, blank=True)
    campuses = models.ManyToManyField(Campus, related_name="routes", blank=True, verbose_name=_("campus desservis"))
    departure_time = models.TimeField(_("heure de départ"), null=True, blank=True)
    arrival_time = models.TimeField(_("heure d'arrivée"), null=True, blank=True)
    alert_threshold = models.PositiveIntegerField(_("seuil d'alerte"), default=5)
    signal_lifetime_minutes = models.PositiveIntegerField(_("durée de vie du signal (minutes)"), default=20)
    is_active = models.BooleanField(_("actif"), default=True)

    class Meta:
        verbose_name = _("trajet")
        verbose_name_plural = _("trajets")
        ordering = ("name",)

    def __str__(self):
        return self.name

    def clean(self):
        if self.departure_time and self.arrival_time and self.arrival_time <= self.departure_time:
            raise ValidationError({"arrival_time": _("L'heure d'arrivée doit suivre l'heure de départ.")})
        if self.alert_threshold < 1:
            raise ValidationError({"alert_threshold": _("Le seuil doit être supérieur à zéro.")})


class Bus(BaseModel):
    registration_number = models.CharField(_("immatriculation"), max_length=32, unique=True)
    name = models.CharField(_("nom interne"), max_length=80, blank=True)
    capacity = models.PositiveIntegerField(_("capacité"), validators=[validate_positive_integer])
    status = models.CharField(_("statut"), max_length=20, choices=BusStatus.choices, default=BusStatus.AVAILABLE)
    driver = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        related_name="buses",
        null=True,
        blank=True,
        limit_choices_to={"role": "driver"},
        verbose_name=_("chauffeur"),
    )
    routes = models.ManyToManyField(Trajet, related_name="buses", blank=True, verbose_name=_("trajets desservis"))
    position_lat = models.DecimalField(
        _("latitude actuelle"), max_digits=9, decimal_places=6, null=True, blank=True, validators=[validate_latitude]
    )
    position_lng = models.DecimalField(
        _("longitude actuelle"), max_digits=9, decimal_places=6, null=True, blank=True, validators=[validate_longitude]
    )
    eta_minutes = models.PositiveIntegerField(_("ETA en minutes"), null=True, blank=True)
    occupied_seats = models.PositiveIntegerField(
        _("places occupées"), default=0, validators=[validate_positive_integer]
    )
    last_position_at = models.DateTimeField(_("dernière position"), null=True, blank=True)

    class Meta:
        verbose_name = _("bus")
        verbose_name_plural = _("bus")
        ordering = ("registration_number",)

    def __str__(self):
        return self.name or self.registration_number

    def clean(self):
        if self.occupied_seats > self.capacity:
            raise ValidationError({"occupied_seats": _("Les places occupées ne peuvent pas dépasser la capacité.")})

    @property
    def available_seats(self):
        return max(self.capacity - self.occupied_seats, 0)
