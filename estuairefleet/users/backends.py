from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q


class IdentifierBackend(ModelBackend):
    """Connexion par e-mail ou matricule, sans révéler l'existence d'un compte."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        identifier = (username or kwargs.get("email") or kwargs.get("matricule") or "").strip()
        if not identifier or not password:
            return None
        user = get_user_model().objects.filter(Q(email__iexact=identifier) | Q(matricule__iexact=identifier)).first()
        if user and user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None


EmailOrMatriculeBackend = IdentifierBackend
