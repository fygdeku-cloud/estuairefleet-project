import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("users", "0001_initial"), ("fleet", "0001_initial")]
    operations = [
        migrations.CreateModel(
            name="AdministratorProfile",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="créé le")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="modifié le")),
                ("can_manage_fleet", models.BooleanField(default=True, verbose_name="gestion de la flotte")),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="administrator_profile",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="utilisateur",
                    ),
                ),
            ],
            options={"verbose_name": "profil administrateur", "verbose_name_plural": "profils administrateurs"},
        ),
        migrations.CreateModel(
            name="Driver",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="créé le")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="modifié le")),
                ("license_number", models.CharField(blank=True, max_length=64, verbose_name="numéro de permis")),
                ("is_available", models.BooleanField(default=True, verbose_name="disponible")),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="driver_profile",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="utilisateur",
                    ),
                ),
            ],
            options={"verbose_name": "profil chauffeur", "verbose_name_plural": "profils chauffeurs"},
        ),
        migrations.CreateModel(
            name="StaffProfile",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="créé le")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="modifié le")),
                ("department", models.CharField(blank=True, max_length=120, verbose_name="service")),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="staff_profile",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="utilisateur",
                    ),
                ),
            ],
            options={"verbose_name": "profil personnel", "verbose_name_plural": "profils personnels"},
        ),
        migrations.CreateModel(
            name="Student",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="créé le")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="modifié le")),
                ("consent_location", models.BooleanField(default=False, verbose_name="consentement de localisation")),
                ("home_address", models.CharField(blank=True, max_length=255, verbose_name="adresse de domicile")),
                (
                    "campus",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="students",
                        to="fleet.campus",
                        verbose_name="campus",
                    ),
                ),
                (
                    "usual_route",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="usual_students",
                        to="fleet.trajet",
                        verbose_name="trajet habituel",
                    ),
                ),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="student_profile",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="utilisateur",
                    ),
                ),
            ],
            options={"verbose_name": "profil étudiant", "verbose_name_plural": "profils étudiants"},
        ),
    ]
