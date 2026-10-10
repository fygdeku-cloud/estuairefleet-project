from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from estuairefleet.core.models import BaseModel


class NotificationChannel(models.TextChoices):
    IN_APP = "in_app", _("Dans l'application")
    EMAIL = "email", _("E-mail")
    SMS = "sms", _("SMS")


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
