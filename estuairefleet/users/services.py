import secrets
import string
from datetime import timedelta
from math import ceil

from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.core.exceptions import PermissionDenied
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone

from estuairefleet.core import conf

from .models import Administrateur, Chauffeur, OTPChallenge, OTPPurpose, Personnel, Student, User, UserRole
from .selectors import get_otp_challenges_since


class OTPRateLimitError(Exception):
    """Indique qu'un nouvel OTP ne peut pas encore être envoyé."""

    def __init__(self, *, retry_after, reason):
        self.retry_after = max(1, int(retry_after))
        self.reason = reason
        super().__init__(reason)


def _temporary_password(length=12):
    return "".join(secrets.choice(string.ascii_letters + string.digits) for _ in range(length))


def _is_account_admin(user):
    return bool(user and (user.is_superuser or user.role in {UserRole.ADMIN, "administrator"}))


def _ensure_account_admin(by):
    if by is not None and not _is_account_admin(by):
        raise PermissionDenied("Seul un administrateur peut gérer les comptes.")


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
    if role == UserRole.STUDENT:
        profile_data["matricule"] = matricule or profile_data["matricule"]
    else:
        profile_data.pop("matricule", None)
    profile_model.objects.create(user=user, **profile_data)
    return user, temporary_password


@transaction.atomic
def update_user_and_profile(*, user, by=None, **data):
    _ensure_account_admin(by)
    user = User.objects.select_for_update().get(pk=user.pk)
    profile_data = data.pop("profile", {})
    for field in ("first_name", "last_name", "phone_number", "email", "matricule", "is_active"):
        if field in data:
            setattr(user, field, data[field])
    user.full_clean()
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
    _ensure_account_admin(by)
    user = User.objects.select_for_update().get(pk=user.pk)
    user.is_active = active
    user.save(update_fields=["is_active", "updated_at"])
    return user


@transaction.atomic
def reset_user_password(*, user, by=None):
    """Génère un secret temporaire affichable une seule fois."""
    _ensure_account_admin(by)
    user = User.objects.select_for_update().get(pk=user.pk)
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
    student = Student.objects.select_for_update().get(pk=student.pk)
    student.location_consent_at = timezone.now()
    student.consent_location = True
    student.save(update_fields=["location_consent_at", "consent_location", "updated_at"])
    return student


@transaction.atomic
def revoke_location_consent(*, student):
    student = Student.objects.select_for_update().get(pk=student.pk)
    student.location_consent_at = None
    student.consent_location = False
    student.save(update_fields=["location_consent_at", "consent_location", "updated_at"])
    return student


@transaction.atomic
def update_student_profile(*, student, campus=None, trajets_habituels=None, consent_location=False):
    """Met à jour le profil étudiant et trace explicitement le choix de localisation."""
    locked = Student.objects.select_for_update().get(pk=student.pk)
    locked.campus = campus
    locked.consent_location = consent_location
    locked.location_consent_at = timezone.now() if consent_location else None
    locked.save(update_fields=["campus", "consent_location", "location_consent_at", "updated_at"])
    if trajets_habituels is not None:
        locked.trajets_habituels.set(trajets_habituels)
    return locked


@transaction.atomic
def register_abuse_warning(*, student):
    student.abuse_warnings += 1
    if student.abuse_warnings >= conf.ABUSE_WARNINGS_BEFORE_SUSPENSION:
        student.signals_suspended_until = timezone.now() + timedelta(hours=conf.SUSPENSION_HOURS)
    student.save(update_fields=["abuse_warnings", "signals_suspended_until", "updated_at"])
    return student


@transaction.atomic
def lift_suspension(*, student, by=None):
    _ensure_account_admin(by)
    student = Student.objects.select_for_update().get(pk=student.pk)
    student.signals_suspended_until = None
    student.save(update_fields=["signals_suspended_until", "updated_at"])
    return student


@transaction.atomic
def register_public_user(
    *, role, email, matricule, first_name, last_name, password="", password_hash=None, licence_number=""
):
    """Crée un compte public et le profil correspondant en une opération."""
    user = User.objects.create(
        email=email,
        password=password_hash or make_password(password),
        matricule=matricule or None,
        first_name=first_name,
        last_name=last_name,
        role=role,
        must_change_password=False,
    )
    if role == UserRole.STUDENT:
        Student.objects.create(user=user, matricule=matricule)
    elif role == UserRole.DRIVER:
        Chauffeur.objects.create(user=user, licence_number=licence_number)
    else:
        raise ValueError("Ce rôle ne peut pas être créé par inscription publique.")
    return user


@transaction.atomic
def register_student(*, email, matricule, first_name, last_name, password):
    """Compatibilité pour créer un compte étudiant depuis un service interne."""
    return register_public_user(
        role=UserRole.STUDENT,
        email=email,
        matricule=matricule,
        first_name=first_name,
        last_name=last_name,
        password=password,
    )


@transaction.atomic
def issue_otp(*, email, purpose, user=None):
    """Invalide les anciens codes et envoie un nouveau code à six chiffres."""
    email = email.strip().lower()
    purpose = OTPPurpose(purpose)
    now = timezone.now()

    window_start = now - timedelta(minutes=settings.ESTUAIREFLEET_OTP_RATE_LIMIT_WINDOW_MINUTES)
    recent_challenges = list(
        get_otp_challenges_since(email=email, purpose=purpose.value, since=window_start)
        .select_for_update()
        .order_by("created_at")
    )
    if recent_challenges:
        latest = recent_challenges[-1]
        cooldown_ends_at = latest.created_at + timedelta(seconds=settings.ESTUAIREFLEET_OTP_RESEND_COOLDOWN_SECONDS)
        if cooldown_ends_at > now:
            raise OTPRateLimitError(
                retry_after=ceil((cooldown_ends_at - now).total_seconds()),
                reason="cooldown",
            )
        if len(recent_challenges) >= settings.ESTUAIREFLEET_OTP_MAX_SENDS_PER_WINDOW:
            window_ends_at = recent_challenges[0].created_at + timedelta(
                minutes=settings.ESTUAIREFLEET_OTP_RATE_LIMIT_WINDOW_MINUTES
            )
            raise OTPRateLimitError(
                retry_after=ceil((window_ends_at - now).total_seconds()),
                reason="window",
            )

    OTPChallenge.objects.filter(
        email__iexact=email,
        purpose=purpose.value,
        consumed_at__isnull=True,
    ).update(consumed_at=now)
    code = f"{secrets.randbelow(1_000_000):06d}"
    challenge = OTPChallenge.objects.create(
        email=email,
        purpose=purpose.value,
        code_hash=make_password(code),
        expires_at=now + timedelta(minutes=settings.ESTUAIREFLEET_OTP_EXPIRY_MINUTES),
    )
    send_otp_email(
        email=email,
        code=code,
        purpose=purpose.value,
    )
    return challenge


def send_otp_email(*, email, code, purpose):
    """Envoie un OTP via le backend e-mail configuré par l'environnement.

    En local, ``config.settings.local`` force le backend SMTP vers Mailpit
    (``mailpit:1025``). La production conserve son relais SMTP configuré par
    l'environnement sans modifier le parcours OTP.
    """
    send_mail(
        subject="Votre code EstuaireFleet",
        message=(
            f"Votre code de {OTPPurpose(purpose).label.lower()} EstuaireFleet est {code}. "
            f"Il expire dans {settings.ESTUAIREFLEET_OTP_EXPIRY_MINUTES} minutes."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=False,
    )


@transaction.atomic
def verify_otp(*, challenge_id, code):
    """Vérifie un code sans révéler si le challenge existe ou est expiré."""
    try:
        challenge = OTPChallenge.objects.select_for_update().get(pk=challenge_id)
    except OTPChallenge.DoesNotExist:
        return None
    if not challenge.is_usable or challenge.attempts >= settings.ESTUAIREFLEET_OTP_MAX_ATTEMPTS:
        return None
    challenge.attempts += 1
    if not check_password(str(code).strip(), challenge.code_hash):
        challenge.save(update_fields=["attempts", "updated_at"])
        return None
    challenge.consumed_at = timezone.now()
    challenge.save(update_fields=["attempts", "consumed_at", "updated_at"])
    return challenge
