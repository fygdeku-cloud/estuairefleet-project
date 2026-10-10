from rest_framework.permissions import BasePermission


class CanViewSignalMap(BasePermission):
    message = "La carte des signaux est réservée aux acteurs transport autorisés."

    def has_permission(self, request, view):
        return bool(request.user.is_authenticated and request.user.is_transport_staff)
