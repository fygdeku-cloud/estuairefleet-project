from rest_framework import serializers

from estuairefleet.notifications.models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ("id", "title", "message", "channel", "status", "read_at", "sent_at", "created_at", "metadata")
        read_only_fields = fields
