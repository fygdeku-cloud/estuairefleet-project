from rest_framework import decorators, response, viewsets

from estuairefleet.notifications.models import Notification
from estuairefleet.notifications.services import mark_notification_read

from .serializers import NotificationSerializer


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user).order_by("-created_at")

    @decorators.action(detail=True, methods=["post"])
    def read(self, request, pk=None):
        notification = mark_notification_read(notification=self.get_object(), user=request.user)
        return response.Response(NotificationSerializer(notification).data)

    @decorators.action(detail=False, methods=["get"])
    def unread_count(self, request):
        return response.Response({"count": self.get_queryset().filter(read_at__isnull=True).count()})
