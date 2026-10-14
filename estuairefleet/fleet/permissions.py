from estuairefleet.core.permissions import IsTransportStaff


class CanManageFleet(IsTransportStaff):
    message = "La gestion de la flotte est réservée aux responsables autorisés."

    def has_permission(self, request, view):
        return bool(
            super().has_permission(request, view)
            and (request.user.is_superuser or request.user.role in {"admin", "administrator"})
        )
