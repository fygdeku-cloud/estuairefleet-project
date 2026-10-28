from uuid import uuid4

import pytest
from django.core import mail
from django.core.exceptions import PermissionDenied

from estuairefleet.notifications.models import NotificationStatus
from estuairefleet.notifications.selectors import get_unread_notification_count
from estuairefleet.notifications.services import (
    create_in_app_notification,
    create_notification,
    dispatch_notification,
    mark_notification_read,
    publish_announcement,
)


@pytest.mark.django_db
def test_in_app_notification_event_key_is_idempotent_and_unread_counted(student_user):
    first = create_in_app_notification(
        recipient=student_user,
        title="Alerte",
        message="Une alerte est ouverte.",
        event_key="alert:test:student",
    )
    second = create_in_app_notification(
        recipient=student_user,
        title="Doublon",
        message="Ce message ne doit pas être dupliqué.",
        event_key="alert:test:student",
    )

    assert first.pk == second.pk
    assert student_user.notifications.count() == 1
    assert get_unread_notification_count(student_user) == 1


@pytest.mark.django_db
def test_only_recipient_can_mark_notification_read(notification, student_user, admin_user):
    with pytest.raises(PermissionDenied):
        mark_notification_read(notification=notification, user=admin_user)

    read = mark_notification_read(notification=notification, user=student_user)

    assert read.read
    assert get_unread_notification_count(student_user) == 0


@pytest.mark.django_db
def test_shared_read_group_marks_colleagues_notifications_as_read(user_factory):
    admin = user_factory(role="admin", email="admin-one@example.test")
    colleague = user_factory(role="admin", email="admin-two@example.test")
    read_group_id = uuid4()
    first = create_in_app_notification(
        recipient=admin,
        title="Signal étudiant",
        message="Un signal attend une prise en charge.",
        event_key="alert:shared:admin-one",
        read_group_id=read_group_id,
    )
    second = create_in_app_notification(
        recipient=colleague,
        title="Signal étudiant",
        message="Un signal attend une prise en charge.",
        event_key="alert:shared:admin-two",
        read_group_id=read_group_id,
    )

    mark_notification_read(notification=first, user=admin)

    first.refresh_from_db()
    second.refresh_from_db()
    assert first.read and second.read
    assert get_unread_notification_count(colleague) == 0


@pytest.mark.django_db
def test_email_notification_is_dispatched_and_announcement_published(student_user, admin_user):
    pending = create_notification(
        recipient=student_user,
        title="Message e-mail",
        message="Contenu du message",
        channel="email",
    )
    sent = dispatch_notification(notification=pending)
    announcement = publish_announcement(title="Annonce", message="Information", by=admin_user, audience="student")

    assert sent.status == NotificationStatus.SENT
    assert sent.provider_reference == "email"
    assert mail.outbox[-1].to == [student_user.email]
    assert announcement.published_at is not None
    assert student_user.notifications.filter(notification_type="announcement").exists()
