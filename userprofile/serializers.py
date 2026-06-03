from rest_framework import serializers
from applicant.models import User
from loan_application.models import LoanApplication
from applicant.models import pre_qualification
from applicant.serializers import LoanTypeSerializer
from loan_application.serializers import LoanApplicationSerializer


class RelatedUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "first_name", "last_name", "email", "role", "reference_code"]


class UserProfileSerializer(serializers.ModelSerializer):
    partner_details = RelatedUserSerializer(source="partner", read_only=True)
    assigned_agent_details = RelatedUserSerializer(source="assigned_agent", read_only=True)
    is_new = serializers.SerializerMethodField(read_only=True)
    prequalification_loan_type_applied_for = serializers.SerializerMethodField(read_only=True)
    recent_active_loan_application = serializers.SerializerMethodField(read_only=True)

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
            "is_new",
            "prequalification_loan_type_applied_for",
            "recent_active_loan_application",
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
            "recent_active_loan_application",
        ]

    def get_is_new(self, obj):
        # Check if the user has any loan applications
        has_applications = LoanApplication.objects.filter(user=obj).exists()
        return not has_applications

    def get_prequalification_loan_type_applied_for(self, obj):
        # Get the most recent prequalification form for the user
        prequalification = pre_qualification.objects.filter(user=obj).order_by('-created_at').first()
        if prequalification and prequalification.loan_type:
            return LoanTypeSerializer(prequalification.loan_type).data
        return None

    def update(self, instance, validated_data):
        email = validated_data.get("email")

        # Keep username aligned with email because authentication uses username.
        if email:
            validated_data["username"] = email

        return super().update(instance, validated_data)

    def get_recent_active_loan_application(self, obj):
        recent_active_loan_application = LoanApplication.objects.filter(user=obj).order_by("-created_at").first()
        if recent_active_loan_application:
            return LoanApplicationSerializer(recent_active_loan_application).data
        return None
