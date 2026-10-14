from rest_framework import decorators, status, viewsets
from rest_framework.response import Response

from estuairefleet.users.models import User
from estuairefleet.users.services import record_location_consent

from .serializers import UserSerializer


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = UserSerializer
    queryset = User.objects.all()

    def get_queryset(self):
        return self.queryset.filter(pk=self.request.user.pk)

    @decorators.action(detail=False, methods=["post"])
    def consent(self, request):
        if request.user.role != "student" or not hasattr(request.user, "student"):
            return Response({"detail": "Cette action est réservée aux étudiants."}, status=status.HTTP_403_FORBIDDEN)
        record_location_consent(student=request.user.student)
        return Response({"consent_location": True, "consent_location_at": request.user.student.location_consent_at})
