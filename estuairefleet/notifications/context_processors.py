from .selectors import get_unread_notification_count


def notification_summary(request):
    if not request.user.is_authenticated:
        return {"unread_notification_count": 0}
    return {"unread_notification_count": get_unread_notification_count(request.user)}
