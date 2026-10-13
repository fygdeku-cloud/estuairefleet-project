from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .models import IntercampusCourseStatus


def validate_course_status_transition(*, current, target):
    allowed = {
        IntercampusCourseStatus.PLANNED: {IntercampusCourseStatus.CONFIRMED, IntercampusCourseStatus.CANCELLED},
        IntercampusCourseStatus.CONFIRMED: {IntercampusCourseStatus.COMPLETED, IntercampusCourseStatus.CANCELLED},
        IntercampusCourseStatus.COMPLETED: set(),
        IntercampusCourseStatus.CANCELLED: set(),
    }
    if target not in allowed.get(current, set()):
        raise ValidationError(_("Cette transition de cours n'est pas autorisée."))
