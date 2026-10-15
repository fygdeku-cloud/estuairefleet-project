from rest_framework import serializers

from estuairefleet.users.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "email", "matricule", "first_name", "last_name", "role")
        read_only_fields = fields


class AccountAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "email", "matricule", "first_name", "last_name", "phone_number", "role", "is_active")
        read_only_fields = ("id",)
