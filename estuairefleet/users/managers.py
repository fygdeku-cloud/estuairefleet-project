from django.contrib.auth.base_user import BaseUserManager


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email=None, password=None, **extra_fields):
        email = self.normalize_email(email).lower() if email else None
        matricule = extra_fields.get("matricule")
        if not email and not matricule:
            raise ValueError("Un e-mail ou un matricule est obligatoire.")
        if matricule:
            extra_fields["matricule"] = matricule.strip().upper()
        user = self.model(email=email, **extra_fields)
        user.set_password(password or self.make_random_password())
        user.save(using=self._db)
        return user

    def create_user(self, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("must_change_password", False)
        if not extra_fields["is_staff"] or not extra_fields["is_superuser"]:
            raise ValueError("Un superutilisateur doit avoir les droits d'administration.")
        return self._create_user(email, password, **extra_fields)
