from rest_framework import decorators, response, viewsets

from estuairefleet.fleet.models import Bus, Campus, Trajet
from estuairefleet.fleet.services import change_bus_status, set_bus_occupancy, update_bus_position
from estuairefleet.users.permissions import IsDriver, IsStaffOrAdmin

from .serializers import BusSerializer, CampusSerializer, TrajetSerializer


class CampusViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Campus.objects.filter(is_active=True)
    serializer_class = CampusSerializer


class TrajetViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Trajet.objects.filter(is_active=True).prefetch_related("campuses", "stops")
    serializer_class = TrajetSerializer


class BusViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Bus.objects.select_related("trajet", "chauffeur__user")
    serializer_class = BusSerializer
    permission_classes = (IsStaffOrAdmin,)

    @decorators.action(detail=False, methods=["get"], permission_classes=[IsStaffOrAdmin])
    def positions(self, request):
        queryset = self.get_queryset().filter(position_lat__isnull=False, position_lng__isnull=False)
        return response.Response(BusSerializer(queryset, many=True).data)

    @decorators.action(detail=False, methods=["post"], url_path="my-bus/position", permission_classes=[IsDriver])
    def my_position(self, request):
        bus = request.user.chauffeur.bus
        updated = update_bus_position(
            bus=bus, lat=request.data.get("lat"), lng=request.data.get("lng"), by=request.user
        )
        return response.Response(BusSerializer(updated).data)

    @decorators.action(detail=False, methods=["post"], url_path="my-bus/status", permission_classes=[IsDriver])
    def my_status(self, request):
        bus = request.user.chauffeur.bus
        updated = change_bus_status(bus=bus, new_status=request.data.get("status"), by=request.user)
        return response.Response(BusSerializer(updated).data)

    @decorators.action(detail=False, methods=["post"], url_path="my-bus/occupancy", permission_classes=[IsDriver])
    def my_occupancy(self, request):
        bus = request.user.chauffeur.bus
        updated = set_bus_occupancy(bus=bus, places=int(request.data.get("places", 0)), by=request.user)
        return response.Response(BusSerializer(updated).data)
