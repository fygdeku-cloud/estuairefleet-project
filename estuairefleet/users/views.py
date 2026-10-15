from __future__ import annotations

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.hashers import make_password
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import (
    LoginView,
    LogoutView,
    PasswordChangeView,
    PasswordResetCompleteView,
    PasswordResetConfirmView,
    PasswordResetDoneView,
    PasswordResetView,
)
from django.contrib.messages.views import SuccessMessageMixin
from django.http import Http404
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.generic import DetailView, FormView, RedirectView, UpdateView

from estuairefleet.users.forms import OTPVerificationForm, PublicSignupForm, StudentProfileForm
from estuairefleet.users.models import OTPPurpose, User
from estuairefleet.users.permissions import OTPRequiredMixin
from estuairefleet.users.services import issue_otp, register_public_user, verify_otp

PENDING_OTP_SESSION_KEY = "pending_otp"
PENDING_SIGNUP_SESSION_KEY = "pending_signup"
OTP_VERIFIED_SESSION_KEY = "otp_verified_at"


def _safe_next_url(request, candidate):
    if candidate and url_has_allowed_host_and_scheme(
        candidate, {request.get_host()}, require_https=request.is_secure()
    ):
        return candidate
    return reverse("core:home")


def _set_otp_verified(request):
    request.session[OTP_VERIFIED_SESSION_KEY] = int(timezone.now().timestamp())
    request.session.modified = True


def _begin_otp(request, *, challenge, purpose, next_url=""):
    request.session[PENDING_OTP_SESSION_KEY] = {
        "challenge_id": str(challenge.pk),
        "purpose": purpose,
        "next": next_url,
    }
    request.session.modified = True


class IdentifierLoginView(LoginView):
    template_name = "account/login.html"

    def form_valid(self, form):
        user = form.get_user()
        if not user.email:
            form.add_error(None, "Ce compte doit avoir une adresse e-mail pour recevoir le code OTP.")
            return self.form_invalid(form)
        challenge = issue_otp(email=user.email, purpose=OTPPurpose.LOGIN, user=user)
        self.request.session["login_user_id"] = str(user.pk)
        self.request.session.modified = True
        _begin_otp(
            self.request, challenge=challenge, purpose=OTPPurpose.LOGIN, next_url=self.request.POST.get("next", "")
        )
        messages.info(self.request, "Un code de vérification vient d'être envoyé à votre adresse e-mail.")
        return redirect("users:otp_verify")


class LogoutConfirmView(LogoutView):
    """Affiche une confirmation avant de fermer la session."""

    http_method_names = ["get", "post", "options"]
    template_name = "account/logout.html"

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)


class StudentSignupView(FormView):
    form_class = PublicSignupForm
    template_name = "account/signup.html"

    def dispatch(self, request, *args, **kwargs):
        if not settings.ACCOUNT_ALLOW_REGISTRATION:
            raise Http404
        if request.user.is_authenticated:
            return redirect("core:home")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        cleaned = form.cleaned_data
        pending = {
            "role": cleaned["role"],
            "email": cleaned["email"],
            "matricule": cleaned.get("matricule", ""),
            "licence_number": cleaned.get("licence_number", ""),
            "first_name": cleaned["first_name"],
            "last_name": cleaned["last_name"],
            "password_hash": make_password(cleaned["password1"]),
        }
        self.request.session[PENDING_SIGNUP_SESSION_KEY] = pending
        challenge = issue_otp(email=cleaned["email"], purpose=OTPPurpose.SIGNUP)
        _begin_otp(self.request, challenge=challenge, purpose=OTPPurpose.SIGNUP)
        messages.info(self.request, "Vérifiez votre adresse e-mail avec le code reçu pour terminer l'inscription.")
        return redirect("users:otp_verify")


class OTPVerifyView(FormView):
    form_class = OTPVerificationForm
    template_name = "account/otp_verify.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.session.get(PENDING_OTP_SESSION_KEY):
            messages.info(request, "Votre demande de vérification a expiré. Recommencez.")
            return redirect("users:login")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pending = self.request.session.get(PENDING_OTP_SESSION_KEY, {})
        context["purpose"] = pending.get("purpose")
        return context

    def post(self, request, *args, **kwargs):
        pending = request.session.get(PENDING_OTP_SESSION_KEY, {})
        if "resend" in request.POST:
            challenge = self._resend(pending)
            if challenge:
                _begin_otp(request, challenge=challenge, purpose=pending["purpose"], next_url=pending.get("next", ""))
                messages.success(request, "Un nouveau code vient d'être envoyé.")
            else:
                messages.error(request, "Impossible de renvoyer le code. Recommencez le parcours.")
            return redirect("users:otp_verify")
        return super().post(request, *args, **kwargs)

    def _resend(self, pending):
        if pending.get("purpose") == OTPPurpose.LOGIN:
            user = User.objects.filter(pk=self.request.session.get("login_user_id"), is_active=True).first()
            return issue_otp(email=user.email, purpose=OTPPurpose.LOGIN, user=user) if user and user.email else None
        signup = self.request.session.get(PENDING_SIGNUP_SESSION_KEY)
        return issue_otp(email=signup["email"], purpose=OTPPurpose.SIGNUP) if signup else None

    def form_valid(self, form):
        pending = self.request.session.get(PENDING_OTP_SESSION_KEY, {})
        challenge = verify_otp(challenge_id=pending.get("challenge_id"), code=form.cleaned_data["code"])
        if challenge is None:
            form.add_error("code", "Code invalide, expiré ou trop de tentatives.")
            return self.form_invalid(form)
        purpose = pending.get("purpose")
        if purpose == OTPPurpose.LOGIN:
            user = User.objects.filter(pk=self.request.session.pop("login_user_id", None), is_active=True).first()
            if user is None:
                return redirect("users:login")
            login(self.request, user, backend="estuairefleet.users.backends.IdentifierBackend")
            _set_otp_verified(self.request)
            self.request.session.pop(PENDING_OTP_SESSION_KEY, None)
            return redirect(_safe_next_url(self.request, pending.get("next", "")))
        if purpose == OTPPurpose.SIGNUP:
            signup = self.request.session.pop(PENDING_SIGNUP_SESSION_KEY, None)
            self.request.session.pop(PENDING_OTP_SESSION_KEY, None)
            if not signup:
                return redirect("users:signup")
            user = register_public_user(
                role=signup["role"],
                email=signup["email"],
                matricule=signup["matricule"],
                first_name=signup["first_name"],
                last_name=signup["last_name"],
                password_hash=signup["password_hash"],
                licence_number=signup["licence_number"],
            )
            login(self.request, user, backend="estuairefleet.users.backends.IdentifierBackend")
            _set_otp_verified(self.request)
            messages.success(self.request, "Votre compte a été créé. Votre espace est prêt.")
            return redirect("core:home")
        return redirect("users:login")


class ProtectedPasswordChangeView(LoginRequiredMixin, OTPRequiredMixin, PasswordChangeView):
    template_name = "users/password_change.html"


class UserDetailView(LoginRequiredMixin, OTPRequiredMixin, DetailView):
    model = User
    template_name = "users/user_detail.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("users:login")
        if str(request.user.pk) != str(kwargs.get("pk")) and not request.user.is_superuser:
            from django.core.exceptions import PermissionDenied

            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class UserUpdateView(LoginRequiredMixin, OTPRequiredMixin, SuccessMessageMixin, UpdateView):
    model = User
    fields = ("first_name", "last_name", "phone_number")
    template_name = "users/user_form.html"
    success_message = "Votre profil a été mis à jour."

    def get_object(self, queryset=None):
        return self.request.user

    def get_profile_form(self):
        if self.request.user.role == "student" and hasattr(self.request.user, "student"):
            return StudentProfileForm(instance=self.request.user.student, prefix="profile")
        return None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["profile_form"] = kwargs.get("profile_form") or self.get_profile_form()
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        profile_form = self.get_profile_form()
        if profile_form is not None:
            profile_form = StudentProfileForm(request.POST, instance=self.object.student, prefix="profile")
        if form.is_valid() and (profile_form is None or profile_form.is_valid()):
            self.object = form.save()
            if profile_form is not None:
                profile_form.save()
            return self.form_valid(form)
        return self.render_to_response(self.get_context_data(form=form, profile_form=profile_form))

    def get_success_url(self):
        return self.request.user.get_absolute_url()


class UserRedirectView(RedirectView):
    permanent = False

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("users:login")
        return super().dispatch(request, *args, **kwargs)

    def get_redirect_url(self):
        return reverse("users:detail", kwargs={"pk": self.request.user.pk})


login_view = IdentifierLoginView.as_view()
logout_view = LogoutConfirmView.as_view(next_page="core:home")
user_detail_view = UserDetailView.as_view()
signup_view = StudentSignupView.as_view()
otp_verify_view = OTPVerifyView.as_view()
user_update_view = UserUpdateView.as_view()
user_redirect_view = UserRedirectView.as_view()
password_change_view = ProtectedPasswordChangeView.as_view(success_url="/users/~redirect/")
password_reset_view = PasswordResetView.as_view(template_name="users/password_reset.html")
password_reset_done_view = PasswordResetDoneView.as_view(template_name="users/password_reset_done.html")
password_reset_confirm_view = PasswordResetConfirmView.as_view(template_name="users/password_reset_confirm.html")
password_reset_complete_view = PasswordResetCompleteView.as_view(template_name="users/password_reset_complete.html")
