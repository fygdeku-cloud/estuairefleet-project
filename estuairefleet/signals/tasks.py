from celery import shared_task
from django.utils import timezone

from .models import Signal, SignalStatus


@shared_task
def expire_signals():
    return Signal.objects.filter(
        status=SignalStatus.ACTIVE,
        expires_at__lte=timezone.now(),
    ).update(status=SignalStatus.EXPIRED)
