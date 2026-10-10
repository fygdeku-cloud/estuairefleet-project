import uuid

import estuairefleet.users.managers
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = [("auth", "0012_alter_user_first_name_max_length")]
    operations = [
        migrations.CreateModel(
            name="User",
            fields=[
                ("password", models.CharField(max_length=128, verbose_name="password")),
                ("last_login", models.DateTimeField(blank=True, null=True, verbose_name="last login")),
                (
                    "is_superuser",
                    models.BooleanField(
                        default=False,
                        help_text="Designates that this user has all permissions without explicitly assigning them.",
                        verbose_name="superuser status",
                    ),
                ),
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="créé le")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="modifié le")),
                ("email", models.EmailField(blank=True, max_length=254, null=True, unique=True, verbose_name="adresse e-mail")),
                ("matricule", models.CharField(blank=True, max_length=32, null=True, unique=True, verbose_name="matricule")),
                ("first_name", models.CharField(blank=True, max_length=150, verbose_name="prénom")),
                ("last_name", models.CharField(blank=True, max_length=150, verbose_name="nom")),
                ("phone", models.CharField(blank=True, max_length=32, verbose_name="téléphone")),
                (
                    "role",
                    models.CharField(
                        choices=[
                            ("student", "Étudiant"),
                            ("driver", "Chauffeur"),
                            ("administrator", "Administrateur"),
                            ("staff", "Personnel académique / scolarité"),
                        ],
                        default="student",
                        max_length=20,
                        verbose_name="rôle",
                    ),
                ),
                ("is_staff", models.BooleanField(default=False, verbose_name="accès administration")),
                ("is_active", models.BooleanField(default=True, verbose_name="actif")),
                ("is_suspended", models.BooleanField(default=False, verbose_name="suspendu")),
                ("suspension_ends_at", models.DateTimeField(blank=True, null=True, verbose_name="fin de suspension")),
                (
                    "groups",
                    models.ManyToManyField(
                        blank=True,
                        help_text="The groups this user belongs to. A user will get all permissions granted to each group.",
                        related_name="user_set",
                        related_query_name="user",
                        to="auth.group",
                        verbose_name="groups",
                    ),
                ),
                (
                    "user_permissions",
                    models.ManyToManyField(
                        blank=True,
                        help_text="Specific permissions for this user.",
                        related_name="user_set",
                        related_query_name="user",
                        to="auth.permission",
                        verbose_name="user permissions",
                    ),
                ),
            ],
            options={"verbose_name": "utilisateur", "verbose_name_plural": "utilisateurs"},
            managers=[("objects", estuairefleet.users.managers.UserManager())],
        ),
        migrations.AddConstraint(
            model_name="user",
            constraint=models.CheckConstraint(
                condition=models.Q(email__isnull=False) | models.Q(matricule__isnull=False),
                name="user_has_email_or_matricule",
            ),
        ),
    ]
