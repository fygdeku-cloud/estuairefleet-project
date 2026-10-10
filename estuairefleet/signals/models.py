from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from estuairefleet.core.models import BaseModel
from estuairefleet.core.validators import validate_latitude, validate_longitude


class SignalStatus(models.TextChoices):
    INACTIVE = "inactive", _("Inactif")
    ACTIVE = "active", _("Actif")
    EXPIRED = "expired", _("Expiré")
    CANCELLED = "cancelled", _("Annulé")
    TAKEN_OVER = "taken_over", _("Pris en charge")


class Signal(BaseModel):
    student = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="location_signals",
        limit_choices_to={"role": "student"},
        verbose_name=_("étudiant"),
    )
    route = models.ForeignKey(
        "fleet.Trajet", on_delete=models.CASCADE, related_name="signals", verbose_name=_("trajet")
    )
    position_lat = models.DecimalField(_("latitude"), max_digits=9, decimal_places=6, validators=[validate_latitude])
    position_lng = models.DecimalField(_("longitude"), max_digits=9, decimal_places=6, validators=[validate_longitude])
    status = models.CharField(_("statut"), max_length=20, choices=SignalStatus.choices, default=SignalStatus.ACTIVE)
    expires_at = models.DateTimeField(_("expire le"))
    cancelled_at = models.DateTimeField(_("annulé le"), null=True, blank=True)
    taken_over_at = models.DateTimeField(_("pris en charge le"), null=True, blank=True)

    class Meta:
        verbose_name = _("signal de localisation")
        verbose_name_plural = _("signaux de localisation")
        constraints = [
            models.UniqueConstraint(
                fields=("student",),
                condition=Q(status=SignalStatus.ACTIVE),
                name="one_active_signal_per_student",
            ),
        ]
        indexes = [
            models.Index(fields=("route", "status", "expires_at")),
            models.Index(fields=("student", "status")),
        ]

    def __str__(self):
        return f"{self.student} — {self.route}"

    def clean(self):
        if self.expires_at and self.expires_at <= timezone.now() and self.status == SignalStatus.ACTIVE:
            raise ValidationError({"expires_at": _("Un signal actif doit expirer dans le futur.")})

    @property
    def is_active(self):
        return self.status == SignalStatus.ACTIVE and self.expires_at > timezone.now()

    def expire(self):
        if self.status == SignalStatus.ACTIVE:
            self.status = SignalStatus.EXPIRED
            self.save(update_fields=["status", "updated_at"])
