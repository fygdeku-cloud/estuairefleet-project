from rest_framework import serializers

from estuairefleet.intercampus.models import CoursInterCampus


class CoursInterCampusSerializer(serializers.ModelSerializer):
    class Meta:
        model = CoursInterCampus
        fields = (
            "id",
            "group",
            "campus_depart",
            "campus_arrivee",
            "start_at",
            "horaire_fin",
            "effectif",
            "bus_affecte",
            "notify_before_minutes",
            "status",
            "driver_notified_at",
        )
        read_only_fields = ("id", "driver_notified_at")
