from rest_framework import viewsets

from estuairefleet.signals.models import Signal
from estuairefleet.signals.permissions import CanViewSignalMap

from .serializers import SignalSerializer


class SignalViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = SignalSerializer
    permission_classes = (CanViewSignalMap,)
    queryset = Signal.objects.select_related("route", "student")

    def get_queryset(self):
        return self.queryset.filter(status="active")
