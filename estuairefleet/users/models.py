from typing import ClassVar

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from estuairefleet.core.models import BaseModel

from .managers import UserManager


class UserRole(models.TextChoices):
    STUDENT = "student", _("Étudiant")
    DRIVER = "driver", _("Chauffeur")
    ADMINISTRATOR = "administrator", _("Administrateur")
    STAFF = "staff", _("Personnel académique / scolarité")


class User(BaseModel, AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(_("adresse e-mail"), unique=True, blank=True, null=True)
    matricule = models.CharField(_("matricule"), max_length=32, unique=True, blank=True, null=True)
    first_name = models.CharField(_("prénom"), max_length=150, blank=True)
    last_name = models.CharField(_("nom"), max_length=150, blank=True)
    phone = models.CharField(_("téléphone"), max_length=32, blank=True)
    role = models.CharField(_("rôle"), max_length=20, choices=UserRole.choices, default=UserRole.STUDENT)
    is_staff = models.BooleanField(_("accès administration"), default=False)
    is_active = models.BooleanField(_("actif"), default=True)
    is_suspended = models.BooleanField(_("suspendu"), default=False)
    suspension_ends_at = models.DateTimeField(_("fin de suspension"), blank=True, null=True)

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

    def get_full_name(self):
        return " ".join(part for part in (self.first_name, self.last_name) if part).strip()

    def get_absolute_url(self):
        return reverse("users:detail", kwargs={"pk": self.pk})

    @property
    def is_transport_staff(self):
        return self.role in {UserRole.DRIVER, UserRole.ADMINISTRATOR, UserRole.STAFF}


class Student(BaseModel):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="student_profile", verbose_name=_("utilisateur")
    )
    consent_location = models.BooleanField(_("consentement de localisation"), default=False)
    home_address = models.CharField(_("adresse de domicile"), max_length=255, blank=True)
    campus = models.ForeignKey(
        "fleet.Campus",
        on_delete=models.SET_NULL,
        related_name="students",
        null=True,
        blank=True,
        verbose_name=_("campus"),
    )
    usual_route = models.ForeignKey(
        "fleet.Trajet",
        on_delete=models.SET_NULL,
        related_name="usual_students",
        null=True,
        blank=True,
        verbose_name=_("trajet habituel"),
    )

    class Meta:
        verbose_name = _("profil étudiant")
        verbose_name_plural = _("profils étudiants")

    def __str__(self):
        return str(self.user)


class Driver(BaseModel):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="driver_profile", verbose_name=_("utilisateur")
    )
    license_number = models.CharField(_("numéro de permis"), max_length=64, blank=True)
    is_available = models.BooleanField(_("disponible"), default=True)

    class Meta:
        verbose_name = _("profil chauffeur")
        verbose_name_plural = _("profils chauffeurs")

    def __str__(self):
        return str(self.user)


class AdministratorProfile(BaseModel):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="administrator_profile", verbose_name=_("utilisateur")
    )
    can_manage_fleet = models.BooleanField(_("gestion de la flotte"), default=True)

    class Meta:
        verbose_name = _("profil administrateur")
        verbose_name_plural = _("profils administrateurs")


class StaffProfile(BaseModel):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="staff_profile", verbose_name=_("utilisateur")
    )
    department = models.CharField(_("service"), max_length=120, blank=True)

    class Meta:
        verbose_name = _("profil personnel")
        verbose_name_plural = _("profils personnels")
