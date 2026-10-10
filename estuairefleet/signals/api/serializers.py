from rest_framework import serializers

from estuairefleet.signals.models import Signal


class SignalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Signal
        fields = ("id", "route", "position_lat", "position_lng", "status", "expires_at", "created_at")
        read_only_fields = fields
