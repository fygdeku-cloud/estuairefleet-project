from django.db.models import QuerySet

from .models import Notification


def get_unread_notifications_for_user(user) -> QuerySet[Notification]:
    return Notification.objects.filter(recipient=user, read_at__isnull=True)
