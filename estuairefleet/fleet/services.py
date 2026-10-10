from django.db import transaction

from .models import Bus


@transaction.atomic
def assign_driver(*, bus: Bus, driver) -> Bus:
    bus.driver = driver
    bus.save(update_fields=["driver", "updated_at"])
    return bus
