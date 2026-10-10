from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class IntercampusConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "estuairefleet.intercampus"
    verbose_name = _("Cours inter-campus")
