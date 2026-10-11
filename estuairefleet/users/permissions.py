from django.core.exceptions import PermissionDenied
from rest_framework.permissions import BasePermission


class RoleRequiredMixin:
    allowed_roles = frozenset()

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            from django.contrib.auth.views import redirect_to_login

            return redirect_to_login(request.get_full_path())
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
