from allauth.account.forms import SignupForm
from django import forms
from django.contrib.auth import forms as admin_forms
from django.utils.translation import gettext_lazy as _

from .models import User


class UserAdminChangeForm(admin_forms.UserChangeForm):
    class Meta(admin_forms.UserChangeForm.Meta):
        model = User
        fields = (
            "email",
            "matricule",
            "first_name",
            "last_name",
            "phone_number",
            "role",
            "is_active",
            "is_staff",
            "must_change_password",
        )


class UserAdminCreationForm(admin_forms.UserCreationForm):
    class Meta:
        model = User
        fields = ("email", "matricule", "first_name", "last_name", "role")
        error_messages = {"email": {"unique": _("Cette adresse e-mail est déjà utilisée.")}}


class UserSignupForm(SignupForm):
    matricule = forms.CharField(label=_("Matricule"), required=False)

    def save(self, request):
        user = super().save(request)
        user.matricule = self.cleaned_data.get("matricule")
        user.save(update_fields=["matricule", "updated_at"])
        return user
