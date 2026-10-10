from django.db import models


class BaseQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_active=True)


class BaseManager(models.Manager.from_queryset(BaseQuerySet)):
    """Manager shared by domain models."""

    def get_by_uuid(self, value):
        return self.get(pk=value)
