from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from estuairefleet.core.models import BaseModel


class IntercampusCourseStatus(models.TextChoices):
    PLANNED = "planned", _("Planifié")
    CONFIRMED = "confirmed", _("Confirmé")
    COMPLETED = "completed", _("Terminé")
    CANCELLED = "cancelled", _("Annulé")


class CourseChangeType(models.TextChoices):
    NONE = "none", _("Aucun changement")
    ADVANCED = "advanced", _("Avancé")
    EXTENDED = "extended", _("Prolongé")
    CANCELLED = "cancelled", _("Annulé")


class CoursInterCampus(BaseModel):
    group = models.CharField(_("groupe"), max_length=120)
    campus_depart = models.ForeignKey(
        "fleet.Campus",
        on_delete=models.PROTECT,
        related_name="intercampus_departures",
        verbose_name=_("campus de départ"),
    )
    campus_arrivee = models.ForeignKey(
        "fleet.Campus",
        on_delete=models.PROTECT,
        related_name="intercampus_arrivals",
        verbose_name=_("campus d'arrivée"),
    )
    start_at = models.DateTimeField(_("début du cours"))
    horaire_fin = models.DateTimeField(_("fin du cours"))
    effectif = models.PositiveIntegerField(_("effectif"), default=0)
    bus_affecte = models.ForeignKey(
        "fleet.Bus",
        on_delete=models.SET_NULL,
        related_name="intercampus_courses",
        null=True,
        blank=True,
        verbose_name=_("bus affecté"),
    )
    notify_before_minutes = models.PositiveIntegerField(_("notification préalable (minutes)"), default=30)
    status = models.CharField(
        _("statut"), max_length=20, choices=IntercampusCourseStatus.choices, default=IntercampusCourseStatus.PLANNED
    )
    driver_notified_at = models.DateTimeField(_("chauffeur notifié le"), null=True, blank=True)
    reminder_sent_at = models.DateTimeField(_("rappel envoyé le"), null=True, blank=True)
    change_type = models.CharField(
        _("type de changement"), max_length=20, choices=CourseChangeType.choices, default=CourseChangeType.NONE
    )
    change_note = models.TextField(_("note de changement"), blank=True)
    last_changed_at = models.DateTimeField(_("modifié métier le"), null=True, blank=True)

    class Meta:
        verbose_name = _("cours inter-campus")
        verbose_name_plural = _("cours inter-campus")
        ordering = ("start_at",)
        constraints = [
            models.CheckConstraint(
                condition=~models.Q(campus_depart=models.F("campus_arrivee")),
                name="intercampus_different_campuses",
            ),
            models.CheckConstraint(
                condition=models.Q(horaire_fin__gt=models.F("start_at")),
                name="intercampus_end_after_start",
            ),
        ]

    def __str__(self):
        return f"{self.group} — {self.campus_depart} → {self.campus_arrivee}"

    def clean(self):
        if self.campus_depart_id == self.campus_arrivee_id:
            raise ValidationError(_("Les campus de départ et d'arrivée doivent être différents."))
        if self.horaire_fin <= self.start_at:
            raise ValidationError({"horaire_fin": _("La fin doit suivre le début du cours.")})
