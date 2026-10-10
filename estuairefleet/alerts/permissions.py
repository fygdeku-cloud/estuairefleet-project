from rest_framework.permissions import BasePermission


class CanRespondToAlert(BasePermission):
    def has_object_permission(self, request, view, obj):
        return bool(
            request.user.is_authenticated and obj.route.buses.filter(driver=request.user).exists(),
        )
