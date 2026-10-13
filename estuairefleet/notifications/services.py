from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.utils import timezone

from .models import Notification, NotificationStatus


@transaction.atomic
def create_in_app_notification(*, recipient, title, message, metadata=None) -> Notification:
    return Notification.objects.create(
        recipient=recipient,
        title=title,
        message=message,
        metadata=metadata or {},
        channel="in_app",
        status=NotificationStatus.SENT,
        sent_at=timezone.now(),
    )


@transaction.atomic
def mark_notification_read(*, notification, user) -> Notification:
    locked = Notification.objects.select_for_update().get(pk=notification.pk)
    if locked.recipient_id != user.pk:
        raise PermissionDenied("Cette notification ne vous est pas destinée.")
    if locked.read_at is None:
        locked.read_at = timezone.now()
        locked.save(update_fields=["read_at", "updated_at"])
    return locked
