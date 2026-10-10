from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q


class EmailOrMatriculeBackend(ModelBackend):
    """Authenticate a person with either their email or student identifier."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        identifier = username or kwargs.get("email") or kwargs.get("matricule")
        if not identifier or not password:
            return None
        user_model = get_user_model()
        user = user_model.objects.filter(
            Q(email__iexact=identifier) | Q(matricule__iexact=identifier),
        ).first()
        if user and user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
