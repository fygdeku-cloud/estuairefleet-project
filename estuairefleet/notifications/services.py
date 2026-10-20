from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.utils import timezone

from .models import Notification, NotificationStatus
from .providers import provider_for


@transaction.atomic
def create_in_app_notification(
    *, recipient, title, message, metadata=None, notification_type="information", event_key=None
) -> Notification:
    defaults = {
        "title": title,
        "message": message,
        "notification_type": notification_type,
        "metadata": metadata or {},
        "channel": "in_app",
        "status": NotificationStatus.SENT,
        "sent_at": timezone.now(),
    }
    if event_key:
        notification, _ = Notification.objects.get_or_create(
            recipient=recipient,
            event_key=event_key,
            defaults=defaults,
        )
    else:
        notification = Notification.objects.create(recipient=recipient, **defaults)
    cache.delete(f"estuairefleet:notifications:unread:{recipient.pk}")
    return notification


@transaction.atomic
def create_notification(
    *, recipient, title, message, channel="in_app", notification_type="information", metadata=None, event_key=None
):
    notification = Notification.objects.create(
        recipient=recipient,
        title=title,
        message=message,
        channel=channel,
        notification_type=notification_type,
        metadata=metadata or {},
        event_key=event_key,
    )
    if channel == "in_app":
        notification.status = NotificationStatus.SENT
        notification.sent_at = timezone.now()
        notification.save(update_fields=["status", "sent_at", "updated_at"])
        cache.delete(f"estuairefleet:notifications:unread:{recipient.pk}")
    return notification


@transaction.atomic
def dispatch_notification(*, notification):
    locked = Notification.objects.select_for_update().select_related("recipient").get(pk=notification.pk)
    if locked.status != NotificationStatus.PENDING:
        return locked
    if locked.channel == "in_app":
        locked.status = NotificationStatus.SENT
        locked.sent_at = timezone.now()
        locked.save(update_fields=["status", "sent_at", "updated_at"])
        cache.delete(f"estuairefleet:notifications:unread:{locked.recipient_id}")
        return locked
    provider = provider_for(locked.channel)
    if provider is None:
        raise ValueError("Canal de notification non pris en charge.")
    try:
        reference = provider.send(
            recipient=locked.recipient, title=locked.title, message=locked.message
        )
    except Exception:
        locked.status = NotificationStatus.FAILED
        locked.failed_at = timezone.now()
        locked.save(update_fields=["status", "failed_at", "updated_at"])
        raise
    locked.status = NotificationStatus.SENT
    locked.sent_at = timezone.now()
    locked.provider_reference = reference
    locked.save(update_fields=["status", "sent_at", "provider_reference", "updated_at"])
    return locked


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
                event_key=f"announcement:{announcement.pk}:{recipient.pk}",
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
        cache.delete(f"estuairefleet:notifications:unread:{user.pk}")
    return locked
