from rest_framework import serializers
from .models import pre_qualification, User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'phone', 'role', 'is_qualified', 'partner', 'reference_code', 'assigned_agent']


class PreQualificationSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = pre_qualification
        fields = ['id', 'uuid', 'user', 'business_name', 'loan_amount', 'loan_type', 'loan_term', 'business_location', 'years_in_business', 'annual_revenue', 'is_qualified', 'name', 'email', 'phone', 'partner', 'refernce_code', 'created_at', 'updated_at']
        read_only_fields = ['id', 'uuid', 'created_at', 'updated_at']


class UserRegistrationSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=150, required=True)
    last_name = serializers.CharField(max_length=150, required=True)
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True, min_length=8)
    phone = serializers.CharField(max_length=20, required=True)
    role = serializers.CharField(max_length=50, required=False)
    is_qualified = serializers.BooleanField(required=False)
    prequalification_form_uuid = serializers.UUIDField(required=True)

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate_phone(self, value):
        import re

        if not re.match(r"^\+?1?\d{9,15}$", value):
            raise serializers.ValidationError("Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")
        return value

    def validate_password(self, value):
        try:
            validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        return value

    def validate_prequalification_form_uuid(self, value):
        if not pre_qualification.objects.filter(uuid=value).exists():
            raise serializers.ValidationError("Prequalification form with this UUID does not exist.")
        return value
