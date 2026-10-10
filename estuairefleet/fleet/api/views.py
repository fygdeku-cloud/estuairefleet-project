from rest_framework import viewsets

from estuairefleet.core.permissions import IsTransportStaff
from estuairefleet.fleet.models import Bus, Campus, Trajet

from .serializers import BusSerializer, CampusSerializer, TrajetSerializer


class CampusViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Campus.objects.active()
    serializer_class = CampusSerializer


class TrajetViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Trajet.objects.active().prefetch_related("campuses")
    serializer_class = TrajetSerializer


class BusViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Bus.objects.select_related("driver")
    serializer_class = BusSerializer
    permission_classes = (IsTransportStaff,)
