from allauth.account.forms import SignupForm
from django import forms
from django.contrib.auth import forms as admin_forms
from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext_lazy as _

from .models import Chauffeur, Student, User, UserRole
from .services import update_student_profile


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


class PublicSignupForm(forms.Form):
    role = forms.ChoiceField(
        label=_("Je m'inscris comme"),
        choices=((UserRole.STUDENT, _("Étudiant")), (UserRole.DRIVER, _("Chauffeur"))),
        widget=forms.Select(attrs={"data-role-selector": "true"}),
        initial=UserRole.STUDENT,
        required=False,
    )
    email = forms.EmailField(label=_("Adresse e-mail"))
    matricule = forms.CharField(label=_("Matricule étudiant"), max_length=32, required=False)
    licence_number = forms.CharField(label=_("Numéro de licence"), max_length=64, required=False)
    first_name = forms.CharField(label=_("Prénom"), max_length=150)
    last_name = forms.CharField(label=_("Nom"), max_length=150)
    password1 = forms.CharField(label=_("Mot de passe"), widget=forms.PasswordInput, strip=False)
    password2 = forms.CharField(label=_("Confirmation du mot de passe"), widget=forms.PasswordInput, strip=False)

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(_("Cette adresse e-mail est déjà utilisée."))
        return email

    def clean_matricule(self):
        matricule = self.cleaned_data["matricule"].strip().upper()
        if User.objects.filter(matricule__iexact=matricule).exists():
            raise forms.ValidationError(_("Ce matricule est déjà utilisé."))
        return matricule

    def clean_licence_number(self):
        licence_number = self.cleaned_data["licence_number"].strip().upper()
        if licence_number and Chauffeur.objects.filter(licence_number__iexact=licence_number).exists():
            raise forms.ValidationError(_("Ce numéro de licence est déjà utilisé."))
        return licence_number

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get("role") or UserRole.STUDENT
        cleaned_data["role"] = role
        if role == UserRole.STUDENT and not cleaned_data.get("matricule"):
            self.add_error("matricule", _("Le matricule est obligatoire pour un étudiant."))
        if role == UserRole.DRIVER and not cleaned_data.get("licence_number"):
            self.add_error("licence_number", _("Le numéro de licence est obligatoire pour un chauffeur."))
        if cleaned_data.get("password1") != cleaned_data.get("password2"):
            self.add_error("password2", _("Les deux mots de passe doivent être identiques."))
        elif cleaned_data.get("password1"):
            try:
                validate_password(cleaned_data["password1"])
            except forms.ValidationError as error:
                self.add_error("password1", error)
        return cleaned_data


StudentSignupForm = PublicSignupForm


class OTPVerificationForm(forms.Form):
    code = forms.CharField(
        label=_("Code de vérification"),
        min_length=6,
        max_length=6,
        strip=True,
        widget=forms.TextInput(attrs={"inputmode": "numeric", "autocomplete": "one-time-code"}),
    )


class LocationConsentForm(forms.Form):
    consent_location = forms.BooleanField(
        label=_("J'autorise EstuaireFleet à utiliser ma position pendant la durée de mon signal."),
        required=True,
    )


class StudentProfileForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ("campus", "trajets_habituels", "consent_location")
        labels = {
            "campus": _("Campus de référence"),
            "trajets_habituels": _("Trajets habituels"),
            "consent_location": _("Autoriser la géolocalisation"),
        }

    def save(self, commit=True):
        if not commit:
            return super().save(commit=False)
        return update_student_profile(
            student=self.instance,
            campus=self.cleaned_data.get("campus"),
            trajets_habituels=self.cleaned_data.get("trajets_habituels"),
            consent_location=self.cleaned_data.get("consent_location", False),
        )
