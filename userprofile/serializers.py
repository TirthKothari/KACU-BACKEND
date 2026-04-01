from rest_framework import serializers
from applicant.models import User


class RelatedUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "first_name", "last_name", "email", "role", "reference_code"]


class UserProfileSerializer(serializers.ModelSerializer):
    partner_details = RelatedUserSerializer(source="partner", read_only=True)
    assigned_agent_details = RelatedUserSerializer(source="assigned_agent", read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "phone",
            "role",
            "is_qualified",
            "partner",
            "reference_code",
            "assigned_agent",
            "partner_details",
            "assigned_agent_details",
        ]
        read_only_fields = [
            "id",
            "role",
            "email",
            "username",
            "is_qualified",
            "partner",
            "reference_code",
            "assigned_agent",
            "partner_details",
            "assigned_agent_details",
        ]

    def update(self, instance, validated_data):
        email = validated_data.get("email")

        # Keep username aligned with email because authentication uses username.
        if email:
            validated_data["username"] = email

        return super().update(instance, validated_data)
