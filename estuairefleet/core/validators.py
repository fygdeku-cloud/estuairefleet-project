from decimal import Decimal

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_latitude(value: Decimal) -> None:
    if not Decimal("-90") <= value <= Decimal("90"):
        raise ValidationError(_("La latitude doit être comprise entre -90 et 90."))


def validate_longitude(value: Decimal) -> None:
    if not Decimal("-180") <= value <= Decimal("180"):
        raise ValidationError(_("La longitude doit être comprise entre -180 et 180."))


def validate_positive_integer(value: int) -> None:
    if value < 0:
        raise ValidationError(_("La valeur doit être positive ou nulle."))
