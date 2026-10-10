import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _

from estuairefleet.core.managers import BaseManager


class BaseModel(models.Model):
    """UUID primary key and audit timestamps shared by domain entities."""

    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("créé le"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("modifié le"))

    objects = BaseManager()

    class Meta:
        abstract = True
        ordering = ("-created_at",)
