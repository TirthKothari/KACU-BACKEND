from rest_framework import serializers
from .models import LoanType


class LoanTypeSerializer(serializers.ModelSerializer):
    """
    Serializer for LoanType model.
    Handles all CRUD operations for loan types.
    """

    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    created_by_email = serializers.EmailField(source='created_by.email', read_only=True)

    class Meta:
        model = LoanType
        fields = [
            'id',
            'name',
            'rates',
            'decision_time',
            'amount',
            'description',
            'created_by',
            'created_by_username',
            'created_by_email',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by_username', 'created_by_email', 'created_by']

    def validate_rates(self, value):
        """
        Validate that rates are within acceptable range (0-100).
        """
        if value < 0 or value > 100:
            raise serializers.ValidationError("Rates must be between 0 and 100.")
        return value

    def validate_name(self, value):
        """
        Validate that the loan type name is not empty and is unique.
        """
        if not value or value.strip() == '':
            raise serializers.ValidationError("Loan type name cannot be empty.")

        # Check uniqueness on update
        if self.instance:
            if LoanType.objects.exclude(pk=self.instance.pk).filter(name=value).exists():
                raise serializers.ValidationError("A loan type with this name already exists.")

        return value.strip()

    def create(self, validated_data):
        """
        Create a new loan type.
        The created_by field should be set in the view.
        """
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """
        Update an existing loan type.
        """
        return super().update(instance, validated_data)


class LoanTypeListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for listing loan types.
    Includes only essential fields for better performance.
    """

    created_by_username = serializers.CharField(source='created_by.username', read_only=True)

    class Meta:
        model = LoanType
        fields = [
            'id',
            'name',
            'rates',
            'decision_time',
            'amount',
            'description',
            'created_by_username',
            'created_at',
        ]
        read_only_fields = fields
