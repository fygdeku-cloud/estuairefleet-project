from rest_framework import serializers

from estuairefleet.alerts.models import Alert, AlertResponse


class AlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alert
        fields = (
            "id",
            "route",
            "status",
            "threshold",
            "signal_count",
            "priority",
            "response_deadline",
            "triggered_at",
            "motif",
            "relay_bus",
            "escalated_at",
            "resolved_at",
            "created_at",
        )
        read_only_fields = fields


class AlertResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = AlertResponse
        fields = ("id", "response_type", "eta_minutes", "reason", "relay_bus", "responded_at")
        read_only_fields = ("id", "responded_at")
