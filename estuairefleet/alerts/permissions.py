from rest_framework.permissions import BasePermission


class CanRespondToAlert(BasePermission):
    message = "Cette alerte ne concerne pas votre bus."

    def has_object_permission(self, request, view, obj):
        return bool(request.user.is_authenticated and obj.route.buses.filter(chauffeur__user=request.user).exists())
