from rest_framework import decorators, status, viewsets
from rest_framework.response import Response

from estuairefleet.alerts.models import Alert
from estuairefleet.alerts.services import resolve_alert, respond_to_alert, respond_to_relay
from estuairefleet.core.permissions import IsTransportStaff
from estuairefleet.users.permissions import IsDriver, IsTransportAdmin

from .serializers import AlertResponseSerializer, AlertSerializer


class AlertViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Alert.objects.all()
    serializer_class = AlertSerializer
    permission_classes = (IsTransportStaff,)

    def get_queryset(self):
        queryset = Alert.objects.filter(status__in=("pending", "triggered", "in_progress", "escalated"))
        if self.request.user.role == "driver":
            queryset = queryset.filter(route__buses__chauffeur__user=self.request.user)
        return queryset.select_related("route").distinct()

    @decorators.action(detail=True, methods=["post"], permission_classes=[IsDriver])
    def respond(self, request, pk=None):
        alert = self.get_object()
        serializer = AlertResponseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        response = respond_to_alert(alert=alert, driver=request.user, **serializer.validated_data)
        return Response(AlertResponseSerializer(response).data, status=status.HTTP_201_CREATED)

    @decorators.action(detail=True, methods=["post"], permission_classes=[IsTransportAdmin])
    def resolve(self, request, pk=None):
        alert = resolve_alert(alert=self.get_object(), by=request.user)
        return Response(AlertSerializer(alert).data)

    @decorators.action(detail=True, methods=["post"], permission_classes=[IsDriver], url_path="relay/respond")
    def relay_respond(self, request, pk=None):
        alert = respond_to_relay(
            alert=self.get_object(),
            driver=request.user,
            accepted=bool(request.data.get("accepted")),
            reason=request.data.get("reason", ""),
        )
        return Response(AlertSerializer(alert).data)
