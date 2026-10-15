from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.utils import timezone

from .models import Notification, NotificationStatus
from .providers import provider_for


@transaction.atomic
def create_in_app_notification(
    *, recipient, title, message, metadata=None, notification_type="information"
) -> Notification:
    return Notification.objects.create(
        recipient=recipient,
        title=title,
        message=message,
        notification_type=notification_type,
        metadata=metadata or {},
        channel="in_app",
        status=NotificationStatus.SENT,
        sent_at=timezone.now(),
    )


@transaction.atomic
def create_notification(
    *, recipient, title, message, channel="in_app", notification_type="information", metadata=None
):
    notification = Notification.objects.create(
        recipient=recipient,
        title=title,
        message=message,
        channel=channel,
        notification_type=notification_type,
        metadata=metadata or {},
    )
    if channel == "in_app":
        notification.status = NotificationStatus.SENT
        notification.sent_at = timezone.now()
        notification.save(update_fields=["status", "sent_at", "updated_at"])
    return notification


@transaction.atomic
def dispatch_notification(*, notification):
    if notification.channel == "in_app":
        return notification
    provider = provider_for(notification.channel)
    if provider is None:
        raise ValueError("Canal de notification non pris en charge.")
    try:
        reference = provider.send(
            recipient=notification.recipient, title=notification.title, message=notification.message
        )
    except Exception:
        notification.status = NotificationStatus.FAILED
        notification.failed_at = timezone.now()
        notification.save(update_fields=["status", "failed_at", "updated_at"])
        raise
    notification.status = NotificationStatus.SENT
    notification.sent_at = timezone.now()
    notification.provider_reference = reference
    notification.save(update_fields=["status", "sent_at", "provider_reference", "updated_at"])
    return notification


@transaction.atomic
def publish_announcement(*, title, message, by, audience="all"):
    from .models import Announcement

    announcement = Announcement.objects.create(title=title, message=message, audience=audience, created_by=by)
    recipients = by.__class__.objects.filter(is_active=True)
    if audience != "all":
        recipients = recipients.filter(role=audience)
    Notification.objects.bulk_create(
        [
            Notification(
                recipient=recipient,
                title=title,
                message=message,
                notification_type="announcement",
                channel="in_app",
                status=NotificationStatus.SENT,
                sent_at=timezone.now(),
            )
            for recipient in recipients
        ]
    )
    announcement.publish()
    return announcement


@transaction.atomic
def mark_notification_read(*, notification, user) -> Notification:
    locked = Notification.objects.select_for_update().get(pk=notification.pk)
    if locked.recipient_id != user.pk:
        raise PermissionDenied("Cette notification ne vous est pas destinée.")
    if locked.read_at is None:
        locked.read_at = timezone.now()
        locked.save(update_fields=["read_at", "updated_at"])
    return locked
