from rest_framework import decorators, status, viewsets
from rest_framework.response import Response

from estuairefleet.users.models import User
from estuairefleet.users.permissions import IsTransportAdmin
from estuairefleet.users.services import record_location_consent, set_user_active, update_user_and_profile

from .serializers import AccountAdminSerializer, UserProfileSerializer, UserSerializer


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = UserSerializer
    queryset = User.objects.all()

    def get_queryset(self):
        role = getattr(self.request.user, "role", None)
        if self.request.user.is_superuser or role in {"admin", "administrator"}:
            return self.queryset
        return self.queryset.filter(pk=self.request.user.pk)

    def get_serializer_class(self):
        if self.action == "profile":
            return UserProfileSerializer
        role = getattr(self.request.user, "role", None)
        return AccountAdminSerializer if role in {"admin", "administrator"} else UserSerializer

    def get_permissions(self):
        if self.action in {"activate", "suspend"}:
            return [IsTransportAdmin()]
        return super().get_permissions()

    @decorators.action(detail=True, methods=["post"], permission_classes=[IsTransportAdmin])
    def activate(self, request, pk=None):
        return Response(
            AccountAdminSerializer(set_user_active(user=self.get_object(), active=True, by=request.user)).data
        )

    @decorators.action(detail=True, methods=["post"], permission_classes=[IsTransportAdmin])
    def suspend(self, request, pk=None):
        return Response(
            AccountAdminSerializer(set_user_active(user=self.get_object(), active=False, by=request.user)).data
        )

    @decorators.action(detail=False, methods=["patch"])
    def profile(self, request):
        serializer = UserProfileSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        user = update_user_and_profile(user=request.user, by=None, **serializer.validated_data)
        return Response(UserProfileSerializer(user).data)

    @decorators.action(detail=False, methods=["post"])
    def consent(self, request):
        if request.user.role != "student" or not hasattr(request.user, "student"):
            return Response({"detail": "Cette action est réservée aux étudiants."}, status=status.HTTP_403_FORBIDDEN)
        record_location_consent(student=request.user.student)
        return Response({"consent_location": True, "consent_location_at": request.user.student.location_consent_at})
