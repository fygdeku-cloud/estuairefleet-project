import pytest
from django.core.exceptions import PermissionDenied

from estuairefleet.notifications.services import create_in_app_notification, mark_notification_read
from estuairefleet.users.models import User


@pytest.mark.django_db
def test_notification_can_only_be_read_by_recipient():
    recipient = User.objects.create_user(email="recipient@example.test", password="password")
    other = User.objects.create_user(email="other@example.test", password="password")
    notification = create_in_app_notification(recipient=recipient, title="Information", message="Départ confirmé.")

    with pytest.raises(PermissionDenied):
        mark_notification_read(notification=notification, user=other)
    mark_notification_read(notification=notification, user=recipient)
    notification.refresh_from_db()
    assert notification.read_at is not None
