from rest_framework import viewsets

from estuairefleet.users.models import User

from .serializers import UserSerializer


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = UserSerializer
    queryset = User.objects.all()

    def get_queryset(self):
        return self.queryset.filter(pk=self.request.user.pk)
