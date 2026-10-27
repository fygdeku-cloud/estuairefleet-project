from typing import ClassVar

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.core.validators import RegexValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from estuairefleet.core.models import BaseModel

from .managers import UserManager


class UserRole(models.TextChoices):
    STUDENT = "student", _("Étudiant")
    DRIVER = "driver", _("Chauffeur")
    ADMIN = "admin", _("Administrateur")
    STAFF = "staff", _("Personnel académique / scolarité")


class OTPPurpose(models.TextChoices):
    LOGIN = "login", _("Connexion")
    SIGNUP = "signup", _("Inscription")
    PASSWORD_RESET = "password_reset", _("Réinitialisation du mot de passe")


phone_validator = RegexValidator(r"^\+?[0-9 ()-]{7,32}$", _("Saisissez un numéro de téléphone valide."))


class User(BaseModel, AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(_("adresse e-mail"), unique=True, blank=True, null=True)
    matricule = models.CharField(_("matricule"), max_length=32, unique=True, blank=True, null=True)
    first_name = models.CharField(_("prénom"), max_length=150, blank=True)
    last_name = models.CharField(_("nom"), max_length=150, blank=True)
    phone_number = models.CharField(
        _("téléphone"), max_length=32, blank=True, default="", validators=[phone_validator]
    )
    role = models.CharField(_("rôle"), max_length=20, choices=UserRole.choices, default=UserRole.STUDENT)
    must_change_password = models.BooleanField(_("changement de mot de passe requis"), default=True)
    is_staff = models.BooleanField(_("accès administration"), default=False)
    is_active = models.BooleanField(_("actif"), default=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: ClassVar[list[str]] = []
    objects: ClassVar[UserManager] = UserManager()

    class Meta:
        verbose_name = _("utilisateur")
        verbose_name_plural = _("utilisateurs")
        constraints = [
            models.CheckConstraint(
                condition=models.Q(email__isnull=False) | models.Q(matricule__isnull=False),
                name="user_has_email_or_matricule",
            ),
        ]

    def __str__(self):
        return self.get_full_name() or self.email or self.matricule or str(self.pk)

    def save(self, *args, **kwargs):
        if self.email:
            self.email = self.email.strip().lower()
        if self.matricule:
            self.matricule = self.matricule.strip().upper()
        return super().save(*args, **kwargs)

    def get_full_name(self):
        return " ".join(part for part in (self.first_name, self.last_name) if part).strip()

    def get_absolute_url(self):
        return reverse("users:detail", kwargs={"pk": self.pk})

    @property
    def phone(self):
        return self.phone_number

    @phone.setter
    def phone(self, value):
        self.phone_number = value

    @property
    def is_transport_staff(self):
        return self.role in {UserRole.DRIVER, UserRole.ADMIN, UserRole.STAFF}


class OTPChallenge(BaseModel):
    """Code à usage unique envoyé par e-mail pour finaliser une action sensible."""

    email = models.EmailField(_("adresse e-mail"), db_index=True)
    purpose = models.CharField(_("usage"), max_length=20, choices=OTPPurpose.choices)
    code_hash = models.CharField(_("code"), max_length=128)
    expires_at = models.DateTimeField(_("expire le"))
    attempts = models.PositiveSmallIntegerField(_("tentatives"), default=0)
    consumed_at = models.DateTimeField(_("utilisé le"), null=True, blank=True)

    class Meta:
        verbose_name = _("code OTP")
        verbose_name_plural = _("codes OTP")
        indexes = [models.Index(fields=("email", "purpose", "created_at"))]

    @property
    def is_expired(self):
        return self.expires_at <= timezone.now()

    @property
    def is_usable(self):
        return self.consumed_at is None and not self.is_expired


class Student(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="student", verbose_name=_("utilisateur"))
    matricule = models.CharField(_("matricule étudiant"), max_length=32, blank=True)
    campus = models.ForeignKey(
        "fleet.Campus",
        on_delete=models.SET_NULL,
        related_name="students",
        null=True,
        blank=True,
        verbose_name=_("campus"),
    )
    trajets_habituels = models.ManyToManyField(
        "fleet.Trajet", related_name="students_habituels", blank=True, verbose_name=_("trajets habituels")
    )
    location_consent_at = models.DateTimeField(_("consentement géolocalisation"), null=True, blank=True)
    consent_location = models.BooleanField(_("consentement enregistré"), default=False)
    abuse_warnings = models.PositiveIntegerField(_("avertissements"), default=0)
    signals_suspended_until = models.DateTimeField(_("suspension des signaux"), null=True, blank=True)

    class Meta:
        verbose_name = _("profil étudiant")
        verbose_name_plural = _("profils étudiants")

    @property
    def has_location_consent(self):
        return bool(self.location_consent_at or self.consent_location)

    @property
    def is_signal_suspended(self):
        return bool(self.signals_suspended_until and self.signals_suspended_until > timezone.now())

    def __str__(self):
        return str(self.user)


class Chauffeur(BaseModel):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="chauffeur", verbose_name=_("utilisateur")
    )
    licence_number = models.CharField(_("numéro de licence"), max_length=64, unique=True, default="PENDING")

    class Meta:
        verbose_name = _("profil chauffeur")
        verbose_name_plural = _("profils chauffeurs")

    def __str__(self):
        return str(self.user)


class Administrateur(BaseModel):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="administrateur", verbose_name=_("utilisateur")
    )
    job_title = models.CharField(_("fonction"), max_length=120, blank=True)

    class Meta:
        verbose_name = _("profil administrateur")
        verbose_name_plural = _("profils administrateurs")


class Personnel(BaseModel):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="personnel", verbose_name=_("utilisateur")
    )
    service = models.CharField(_("service"), max_length=120, blank=True)
    campus = models.ForeignKey(
        "fleet.Campus",
        on_delete=models.SET_NULL,
        related_name="personnel",
        null=True,
        blank=True,
        verbose_name=_("campus"),
    )

    class Meta:
        verbose_name = _("profil personnel")
        verbose_name_plural = _("profils personnels")


Driver = Chauffeur
AdministratorProfile = Administrateur
StaffProfile = Personnel
