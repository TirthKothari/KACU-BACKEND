from rest_framework import serializers

from applicant.models import User
from applicant.utils import UserRoleChoices
from loan_application.models import LoanApplication


class AdminUserRelatedSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "first_name", "last_name", "email", "role", "is_active"]


class AdminUserListSerializer(serializers.ModelSerializer):
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
            "is_active",
            "is_qualified",
            "assigned_agent",
            "partner",
            "reference_code",
        ]


class AdminUserDetailSerializer(serializers.ModelSerializer):
    assigned_agent_details = AdminUserRelatedSerializer(source="assigned_agent", read_only=True)
    partner_details = AdminUserRelatedSerializer(source="partner", read_only=True)
    applications = serializers.SerializerMethodField()

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
            "is_active",
            "is_qualified",
            "assigned_agent",
            "assigned_agent_details",
            "partner",
            "partner_details",
            "reference_code",
            "applications",
        ]

    def get_applications(self, obj):
        from loan_application.serializers import LoanApplicationSerializer

        applications = LoanApplication.objects.filter(user=obj).order_by("-created_at")
        return LoanApplicationSerializer(applications, many=True).data


class AdminUserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "phone", "assigned_agent", "is_active"]

    def validate_assigned_agent(self, value):
        if value is None:
            return value

        if value.role != UserRoleChoices.AGENT.value:
            raise serializers.ValidationError("Assigned user must have AGENT role.")

        if not value.is_active:
            raise serializers.ValidationError("Assigned agent must be active.")

        return value

    def validate(self, attrs):
        user = self.instance
        if "assigned_agent" in attrs and user.role != UserRoleChoices.APPLICANT.value:
            raise serializers.ValidationError({"assigned_agent": "assigned_agent can only be updated for APPLICANT users."})
        return attrs
