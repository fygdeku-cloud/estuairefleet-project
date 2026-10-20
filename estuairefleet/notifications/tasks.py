from celery import shared_task

from .models import Notification, NotificationStatus
from .services import dispatch_notification


@shared_task
def dispatch_pending_notifications():
    count = 0
    notifications = Notification.objects.filter(
        status=NotificationStatus.PENDING,
        channel__in=("email", "sms"),
    ).order_by("created_at")[:100]
    for notification in notifications.iterator(chunk_size=100):
        try:
            dispatch_notification(notification=notification)
        except Exception:
            continue
        count += 1
    return count
