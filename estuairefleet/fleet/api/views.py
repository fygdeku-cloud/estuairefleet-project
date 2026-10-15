from rest_framework import decorators, response, viewsets
from rest_framework.permissions import IsAuthenticated

from estuairefleet.fleet.models import Bus, Campus, Incident, Trajet
from estuairefleet.fleet.permissions import CanManageFleet
from estuairefleet.fleet.services import (
    change_bus_status,
    create_bus,
    create_campus,
    create_trajet,
    report_incident,
    resolve_incident,
    set_bus_occupancy,
    update_bus,
    update_bus_position,
    update_campus,
    update_trajet,
)
from estuairefleet.users.permissions import IsDriver, IsTransportAdmin

from .serializers import BusSerializer, CampusSerializer, IncidentSerializer, TrajetSerializer


class CampusViewSet(viewsets.ModelViewSet):
    queryset = Campus.objects.filter(is_active=True)
    serializer_class = CampusSerializer

    def get_permissions(self):
        return [CanManageFleet()] if self.request.method not in ("GET", "HEAD", "OPTIONS") else [IsAuthenticated()]

    def perform_create(self, serializer):
        serializer.instance = create_campus(**serializer.validated_data)

    def perform_update(self, serializer):
        serializer.instance = update_campus(campus=self.get_object(), **serializer.validated_data)


class TrajetViewSet(viewsets.ModelViewSet):
    queryset = Trajet.objects.filter(is_active=True).prefetch_related("campuses", "stops")
    serializer_class = TrajetSerializer

    def get_permissions(self):
        return [CanManageFleet()] if self.request.method not in ("GET", "HEAD", "OPTIONS") else [IsAuthenticated()]

    def perform_create(self, serializer):
        serializer.instance = create_trajet(**serializer.validated_data)

    def perform_update(self, serializer):
        serializer.instance = update_trajet(trajet=self.get_object(), **serializer.validated_data)


class BusViewSet(viewsets.ModelViewSet):
    queryset = Bus.objects.select_related("trajet", "chauffeur__user")
    serializer_class = BusSerializer

    def get_permissions(self):
        if self.action in {"list", "retrieve", "positions"}:
            return [IsAuthenticated()]
        if self.action in {"my_position", "my_status", "my_occupancy"}:
            return [IsDriver()]
        return [CanManageFleet()]

    def perform_create(self, serializer):
        serializer.instance = create_bus(**serializer.validated_data)

    def perform_update(self, serializer):
        serializer.instance = update_bus(bus=self.get_object(), **serializer.validated_data)

    def get_serializer_context(self):
        return {**super().get_serializer_context(), "request": self.request}

    @decorators.action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
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


class IncidentViewSet(viewsets.ModelViewSet):
    queryset = Incident.objects.select_related("bus", "trajet")
    serializer_class = IncidentSerializer
    permission_classes = (IsTransportAdmin,)

    def perform_create(self, serializer):
        serializer.instance = report_incident(by=self.request.user, **serializer.validated_data)

    def perform_update(self, serializer):
        serializer.instance = report_incident(
            incident=self.get_object(), by=self.request.user, **serializer.validated_data
        )

    @decorators.action(detail=True, methods=["post"])
    def resolve(self, request, pk=None):
        incident = resolve_incident(incident=self.get_object(), by=request.user)
        return response.Response(IncidentSerializer(incident).data)
