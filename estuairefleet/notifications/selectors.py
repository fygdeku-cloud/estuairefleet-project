from django.core.cache import cache
from django.db.models import QuerySet

from .models import Notification


def get_notifications_for_user(user) -> QuerySet[Notification]:
    return Notification.objects.filter(recipient=user).order_by("-created_at")


def get_unread_notifications_for_user(user) -> QuerySet[Notification]:
    return get_notifications_for_user(user).filter(read_at__isnull=True)


def get_unread_notification_count(user) -> int:
    key = f"estuairefleet:notifications:unread:{user.pk}"
    return cache.get_or_set(key, lambda: get_unread_notifications_for_user(user).count(), timeout=10)
