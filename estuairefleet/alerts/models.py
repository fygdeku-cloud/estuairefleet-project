from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from estuairefleet.core.models import BaseModel


class AlertStatus(models.TextChoices):
    PENDING = "pending", _("En attente")
    TRIGGERED = "triggered", _("Déclenchée")
    IN_PROGRESS = "in_progress", _("En cours")
    RESOLVED = "resolved", _("Résolue")
    ESCALATED = "escalated", _("Escalade")


class DriverResponseType(models.TextChoices):
    ARRIVING = "arriving", _("J'arrive")
    UNAVAILABLE = "unavailable", _("Indisponible")


class Alert(BaseModel):
    route = models.ForeignKey(
        "fleet.Trajet", on_delete=models.CASCADE, related_name="alerts", verbose_name=_("trajet")
    )
    signals = models.ManyToManyField(
        "signals.Signal", related_name="alerts", blank=True, verbose_name=_("signaux concernés")
    )
    status = models.CharField(_("statut"), max_length=20, choices=AlertStatus.choices, default=AlertStatus.PENDING)
    threshold = models.PositiveIntegerField(_("seuil"), default=5)
    signal_count = models.PositiveIntegerField(_("nombre de signaux"), default=0)
    priority = models.BooleanField(_("prioritaire"), default=False)
    response_deadline = models.DateTimeField(_("délai de réponse"), null=True, blank=True)
    escalated_at = models.DateTimeField(_("escaladée le"), null=True, blank=True)
    resolved_at = models.DateTimeField(_("résolue le"), null=True, blank=True)

    class Meta:
        verbose_name = _("alerte")
        verbose_name_plural = _("alertes")
        constraints = [
            models.CheckConstraint(condition=models.Q(threshold__gt=0), name="alert_threshold_positive"),
            models.UniqueConstraint(
                fields=("route",),
                condition=Q(
                    status__in=[
                        AlertStatus.PENDING,
                        AlertStatus.TRIGGERED,
                        AlertStatus.IN_PROGRESS,
                        AlertStatus.ESCALATED,
                    ]
                ),
                name="one_open_alert_per_route",
            ),
        ]
        indexes = [models.Index(fields=("route", "status", "created_at"))]

    def __str__(self):
        return f"{self.route} — {self.get_status_display()}"

    def clean(self):
        if self.threshold < 1:
            raise ValidationError({"threshold": _("Le seuil doit être supérieur à zéro.")})
        if self.priority and self.signal_count < self.threshold:
            raise ValidationError({"priority": _("Une alerte prioritaire doit atteindre le seuil configuré.")})

    def mark_resolved(self):
        self.status = AlertStatus.RESOLVED
        self.resolved_at = timezone.now()
        self.save(update_fields=["status", "resolved_at", "updated_at"])


class AlertResponse(BaseModel):
    alert = models.OneToOneField(Alert, on_delete=models.CASCADE, related_name="response", verbose_name=_("alerte"))
    driver = models.ForeignKey(
        "users.User", on_delete=models.PROTECT, related_name="alert_responses", verbose_name=_("chauffeur")
    )
    response_type = models.CharField(_("réponse"), max_length=20, choices=DriverResponseType.choices)
    eta_minutes = models.PositiveIntegerField(_("ETA en minutes"), null=True, blank=True)
    reason = models.TextField(_("motif"), blank=True)
    relay_bus = models.ForeignKey(
        "fleet.Bus",
        on_delete=models.SET_NULL,
        related_name="relay_responses",
        null=True,
        blank=True,
        verbose_name=_("bus relais"),
    )
    responded_at = models.DateTimeField(_("répondu le"), auto_now_add=True)

    class Meta:
        verbose_name = _("réponse chauffeur")
        verbose_name_plural = _("réponses chauffeurs")

    def clean(self):
        if self.response_type == DriverResponseType.ARRIVING and self.eta_minutes is None:
            raise ValidationError({"eta_minutes": _("Une ETA est obligatoire pour la réponse « J'arrive ».")})
        if self.response_type == DriverResponseType.UNAVAILABLE and not self.reason:
            raise ValidationError({"reason": _("Un motif est obligatoire si le chauffeur est indisponible.")})
        if self.response_type == DriverResponseType.UNAVAILABLE and not self.relay_bus_id:
            raise ValidationError({"relay_bus": _("Un bus relais doit être proposé.")})
