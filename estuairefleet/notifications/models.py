from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from estuairefleet.core.models import BaseModel


class NotificationChannel(models.TextChoices):
    IN_APP = "in_app", _("Dans l'application")
    EMAIL = "email", _("E-mail")
    SMS = "sms", _("SMS")


class NotificationType(models.TextChoices):
    INFORMATION = "information", _("Information")
    BUS_APPROACHING = "bus_approaching", _("Bus en approche")
    DELAY = "delay", _("Retard")
    CANCELLATION = "cancellation", _("Annulation")
    BUS_CHANGE = "bus_change", _("Changement de bus")
    SIGNAL_TAKEN = "signal_taken", _("Signal pris en charge")
    ALERT = "alert", _("Alerte")
    ESCALATION = "escalation", _("Escalade")
    INTERCAMPUS = "intercampus", _("Cours inter-campus")
    ANNOUNCEMENT = "announcement", _("Annonce")


class NotificationStatus(models.TextChoices):
    PENDING = "pending", _("En attente")
    SENT = "sent", _("Envoyée")
    FAILED = "failed", _("Échec")


class Notification(BaseModel):
    recipient = models.ForeignKey(
        "users.User", on_delete=models.CASCADE, related_name="notifications", verbose_name=_("destinataire")
    )
    title = models.CharField(_("titre"), max_length=160)
    message = models.TextField(_("message"))
    notification_type = models.CharField(
        _("type"), max_length=32, choices=NotificationType.choices, default=NotificationType.INFORMATION
    )
    channel = models.CharField(
        _("canal"), max_length=20, choices=NotificationChannel.choices, default=NotificationChannel.IN_APP
    )
    status = models.CharField(
        _("statut"), max_length=20, choices=NotificationStatus.choices, default=NotificationStatus.PENDING
    )
    read_at = models.DateTimeField(_("lue le"), null=True, blank=True)
    sent_at = models.DateTimeField(_("envoyée le"), null=True, blank=True)
    failed_at = models.DateTimeField(_("échouée le"), null=True, blank=True)
    provider_reference = models.CharField(_("référence prestataire"), max_length=120, blank=True)
    metadata = models.JSONField(_("métadonnées"), default=dict, blank=True)

    class Meta:
        verbose_name = _("notification")
        verbose_name_plural = _("notifications")
        ordering = ("-created_at",)
        indexes = [models.Index(fields=("recipient", "status", "created_at"))]

    def __str__(self):
        return f"{self.recipient} — {self.title}"

    def mark_read(self):
        self.read_at = timezone.now()
        self.save(update_fields=["read_at", "updated_at"])

    def markRead(self):  # noqa: N802
        return self.mark_read()

    @property
    def read(self):
        return self.read_at is not None


class Announcement(BaseModel):
    title = models.CharField(_("titre"), max_length=160)
    message = models.TextField(_("message"))
    audience = models.CharField(_("public"), max_length=32, default="all")
    published_at = models.DateTimeField(_("publiée le"), null=True, blank=True)
    is_active = models.BooleanField(_("active"), default=True)
    created_by = models.ForeignKey(
        "users.User", on_delete=models.SET_NULL, related_name="announcements", null=True, blank=True
    )

    class Meta:
        verbose_name = _("annonce")
        verbose_name_plural = _("annonces")
        ordering = ("-published_at", "-created_at")

    def publish(self):
        self.published_at = timezone.now()
        self.is_active = True
        self.save(update_fields=["published_at", "is_active", "updated_at"])
        return self
