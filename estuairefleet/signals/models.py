from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from estuairefleet.core.models import BaseModel


class SignalStatus(models.TextChoices):
    INACTIF = "inactif", _("Inactif")
    ACTIF = "actif", _("Actif")
    EXPIRE = "expire", _("Expiré")
    ANNULE = "annule", _("Annulé")
    PRIS_EN_CHARGE = "pris_en_charge", _("Pris en charge")


class Signal(BaseModel):
    student = models.ForeignKey(
        "users.Student", on_delete=models.CASCADE, related_name="signals", verbose_name=_("étudiant"), null=True
    )
    trajet = models.ForeignKey(
        "fleet.Trajet", on_delete=models.CASCADE, related_name="signals", verbose_name=_("trajet"), null=True
    )
    position_lat = models.DecimalField(_("latitude"), max_digits=9, decimal_places=6, null=True, blank=True)
    position_lng = models.DecimalField(_("longitude"), max_digits=9, decimal_places=6, null=True, blank=True)
    accuracy_m = models.FloatField(_("précision GPS (m)"), null=True, blank=True)
    status = models.CharField(_("statut"), max_length=20, choices=SignalStatus.choices, default=SignalStatus.ACTIF)
    expires_at = models.DateTimeField(_("expire le"))
    renewed_count = models.PositiveIntegerField(_("renouvellements"), default=0)
    taken_at = models.DateTimeField(_("pris en charge le"), null=True, blank=True)
    taken_by_bus = models.ForeignKey(
        "fleet.Bus", on_delete=models.SET_NULL, related_name="signals_taken", null=True, blank=True
    )
    closed_by = models.ForeignKey(
        "users.User", on_delete=models.SET_NULL, related_name="signals_closed", null=True, blank=True
    )
    flagged_false = models.BooleanField(_("signal déclaré introuvable"), default=False)
    flagged_by = models.ForeignKey(
        "users.User", on_delete=models.SET_NULL, related_name="signals_flagged", null=True, blank=True
    )
    flagged_at = models.DateTimeField(_("déclaré introuvable le"), null=True, blank=True)

    class Meta:
        verbose_name = _("signal de localisation")
        verbose_name_plural = _("signaux de localisation")
        constraints = [
            models.UniqueConstraint(
                fields=("student",), condition=Q(status="actif"), name="uniq_active_signal_per_student"
            ),
            models.CheckConstraint(
                condition=Q(expires_at__gt=models.F("created_at")), name="signal_expires_after_creation"
            ),
        ]
        indexes = [
            models.Index(fields=("trajet", "status", "expires_at")),
            models.Index(fields=("status", "expires_at")),
        ]

    def clean(self):
        if self.status == SignalStatus.ACTIF and self.expires_at <= self.created_at:
            raise ValidationError({"expires_at": _("Un signal actif doit expirer dans le futur.")})

    @property
    def is_active(self):
        return self.status == SignalStatus.ACTIF and self.expires_at > timezone.now()

    @property
    def seconds_left(self):
        return max(0, int((self.expires_at - timezone.now()).total_seconds())) if self.is_active else 0

    @property
    def age_seconds(self):
        return max(0, int((timezone.now() - self.created_at).total_seconds()))

    @property
    def route(self):
        return self.trajet

    def __str__(self):
        return f"{self.student} — {self.trajet}"
