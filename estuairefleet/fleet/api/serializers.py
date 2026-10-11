from rest_framework import serializers

from estuairefleet.fleet.models import Bus, Campus, Trajet


class CampusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Campus
        fields = ("id", "code", "name", "address", "latitude", "longitude", "radius_m", "is_active")


class TrajetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trajet
        fields = ("id", "code", "name", "direction", "itinerary", "horaires", "seuil_alerte", "is_active")


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
        )
