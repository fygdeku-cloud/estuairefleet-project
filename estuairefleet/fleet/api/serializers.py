from rest_framework import serializers

from estuairefleet.fleet.models import Bus, Campus, Incident, Trajet


class CampusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Campus
        fields = ("id", "code", "name", "address", "latitude", "longitude", "radius_m", "is_active")


class TrajetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trajet
        fields = (
            "id",
            "code",
            "name",
            "direction",
            "itinerary",
            "horaires",
            "service_start",
            "service_end",
            "days_of_week",
            "seuil_alerte",
            "signal_ttl_minutes",
            "geofence_radius_m",
            "campuses",
            "is_active",
        )


class BusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bus
        fields = (
            "id",
            "plate_number",
            "label",
            "capacity",
            "status",
            "position_lat",
            "position_lng",
            "position_updated_at",
            "places_occupees",
            "trajet",
            "eta",
        )


class IncidentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Incident
        fields = ("id", "bus", "trajet", "type", "description", "status", "reported_at", "resolved_at")
        read_only_fields = ("id", "reported_at", "resolved_at")
