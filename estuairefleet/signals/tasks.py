from celery import shared_task

from .services import expire_stale_signals, purge_old_positions


@shared_task
def expire_signals():
    return expire_stale_signals()


@shared_task
def purge_old_signal_positions():
    return purge_old_positions()
