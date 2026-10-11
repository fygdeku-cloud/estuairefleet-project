import secrets
import string
from datetime import timedelta

from django.contrib.auth.hashers import make_password
from django.db import transaction
from django.utils import timezone

from estuairefleet.core import conf

from .models import Administrateur, Chauffeur, Personnel, Student, User, UserRole


def _temporary_password(length=12):
    return "".join(secrets.choice(string.ascii_letters + string.digits) for _ in range(length))


@transaction.atomic
def create_user_with_profile(
    *, role, email=None, matricule=None, first_name="", last_name="", phone_number="", **profile_data
):
    """Crée un compte et le profil correspondant dans une seule opération."""
    temporary_password = _temporary_password()
    user = User.objects.create(
        email=email,
        matricule=matricule,
        first_name=first_name,
        last_name=last_name,
        phone_number=phone_number,
        role=role,
        password=make_password(temporary_password),
        must_change_password=True,
    )
    profile_model = {
        UserRole.STUDENT: Student,
        UserRole.DRIVER: Chauffeur,
        UserRole.ADMIN: Administrateur,
        UserRole.STAFF: Personnel,
    }.get(role)
    if profile_model is None:
        raise ValueError("Rôle inconnu.")
    if role == UserRole.STUDENT and not (matricule or profile_data.get("matricule")):
        raise ValueError("Le matricule est obligatoire pour un étudiant.")
    profile_model.objects.create(user=user, **profile_data)
    return user, temporary_password


@transaction.atomic
def update_user_and_profile(*, user, by=None, **data):
    profile_data = data.pop("profile", {})
    for field in ("first_name", "last_name", "phone_number", "email", "matricule", "is_active"):
        if field in data:
            setattr(user, field, data[field])
    user.save()
    relation = {"student": "student", "driver": "chauffeur", "admin": "administrateur", "staff": "personnel"}[
        user.role
    ]
    profile = getattr(user, relation)
    for field, value in profile_data.items():
        setattr(profile, field, value)
    if profile_data:
        profile.save()
    return user


@transaction.atomic
def set_user_active(*, user, active, by=None):
    user.is_active = active
    user.save(update_fields=["is_active", "updated_at"])
    return user


@transaction.atomic
def reset_user_password(*, user, by=None):
    """Génère un secret temporaire affichable une seule fois."""
    temporary_password = _temporary_password()
    user.password = make_password(temporary_password)
    user.must_change_password = True
    user.save(update_fields=["password", "must_change_password", "updated_at"])
    return temporary_password


@transaction.atomic
def change_password(*, user, new_password):
    user.set_password(new_password)
    user.must_change_password = False
    user.save(update_fields=["password", "must_change_password", "updated_at"])
    return user


@transaction.atomic
def record_location_consent(*, student):
    student.location_consent_at = timezone.now()
    student.consent_location = True
    student.save(update_fields=["location_consent_at", "consent_location", "updated_at"])
    return student


@transaction.atomic
def register_abuse_warning(*, student):
    student.abuse_warnings += 1
    if student.abuse_warnings >= conf.ABUSE_WARNINGS_BEFORE_SUSPENSION:
        student.signals_suspended_until = timezone.now() + timedelta(hours=conf.SUSPENSION_HOURS)
    student.save(update_fields=["abuse_warnings", "signals_suspended_until", "updated_at"])
    return student


@transaction.atomic
def lift_suspension(*, student, by=None):
    student.signals_suspended_until = None
    student.save(update_fields=["signals_suspended_until", "updated_at"])
    return student
