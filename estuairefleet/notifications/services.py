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
