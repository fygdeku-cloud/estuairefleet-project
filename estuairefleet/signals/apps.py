from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class SignalsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "estuairefleet.signals"
    verbose_name = _("Signaux de localisation")
