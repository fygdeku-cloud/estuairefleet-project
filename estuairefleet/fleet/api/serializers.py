from rest_framework import serializers

from estuairefleet.fleet.models import Bus, Campus, Trajet


class CampusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Campus
        fields = ("id", "code", "name", "address", "latitude", "longitude")


class TrajetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trajet
        fields = ("id", "name", "route_type", "description", "stops", "departure_time", "arrival_time")


class BusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bus
        fields = (
            "id",
            "registration_number",
            "name",
            "capacity",
            "status",
            "position_lat",
            "position_lng",
            "eta_minutes",
        )
