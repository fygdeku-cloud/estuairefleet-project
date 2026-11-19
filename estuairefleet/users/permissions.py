from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from rest_framework.permissions import BasePermission

from estuairefleet.users.models import OTPPurpose
from estuairefleet.users.services import OTPRateLimitError, issue_otp


class OTPRequiredMixin:
    """Exige une session authentifiée par OTP avant l'accès à une page protégée."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())
        verified_at = request.session.get("otp_verified_at")
        try:
            otp_is_fresh = (
                verified_at
                and timezone.now().timestamp() - int(verified_at) <= settings.ESTUAIREFLEET_OTP_SESSION_AGE_SECONDS
            )
        except (TypeError, ValueError):
            otp_is_fresh = False
        if not otp_is_fresh:
            if not request.user.email:
                return redirect_to_login(request.get_full_path(), login_url=reverse("users:login"))
            try:
                challenge = issue_otp(email=request.user.email, purpose=OTPPurpose.LOGIN, user=request.user)
            except OTPRateLimitError:
                return HttpResponse("Trop de demandes de code. Réessayez dans quelques minutes.", status=429)
            request.session["login_user_id"] = str(request.user.pk)
            request.session["pending_otp"] = {
                "challenge_id": str(challenge.pk),
                "purpose": OTPPurpose.LOGIN,
                "next": request.get_full_path(),
            }
            request.session.modified = True
            messages.info(request, "Votre vérification a expiré. Un nouveau code vous a été envoyé par e-mail.")
            return redirect("users:otp_verify")
        return super().dispatch(request, *args, **kwargs)


class LoginAndOTPRequiredMixin(LoginRequiredMixin, OTPRequiredMixin):
    """Exige une session Django authentifiée et une vérification OTP récente."""


class RoleRequiredMixin(OTPRequiredMixin):
    allowed_roles = frozenset()

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path(), login_url=reverse("users:login"))
        if request.user.role not in self.allowed_roles and not request.user.is_superuser:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class StudentRequiredMixin(RoleRequiredMixin):
    allowed_roles = frozenset({"student"})


class DriverRequiredMixin(RoleRequiredMixin):
    allowed_roles = frozenset({"driver"})


class AdminRequiredMixin(RoleRequiredMixin):
    allowed_roles = frozenset({"admin", "administrator"})


class StaffOrAdminRequiredMixin(RoleRequiredMixin):
    allowed_roles = frozenset({"staff", "admin", "administrator"})


class NonStudentRequiredMixin(RoleRequiredMixin):
    allowed_roles = frozenset({"driver", "staff", "admin", "administrator"})


class _RolePermission(BasePermission):
    roles = frozenset()

    def has_permission(self, request, view):
        return bool(request.user.is_authenticated and (request.user.is_superuser or request.user.role in self.roles))


class IsStudent(_RolePermission):
    roles = frozenset({"student"})


class IsDriver(_RolePermission):
    roles = frozenset({"driver"})


class IsTransportAdmin(_RolePermission):
    roles = frozenset({"admin", "administrator"})


class IsStaffOrAdmin(_RolePermission):
    roles = frozenset({"staff", "admin", "administrator"})


class IsNotStudent(_RolePermission):
    roles = frozenset({"driver", "staff", "admin", "administrator"})
