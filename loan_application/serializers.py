from rest_framework import serializers
from .models import (
    LoanApplication,
    BusinessInformation,
    BusinessFundingInformation,
    BusinessOwnerInformation,
    TermsAndConditions,
    LoanApplicationDocument,
)
from applicant.serializers import UserSerializer
from loan_type.serializers import LoanTypeListSerializer
from .utils import LoanApplicationStatus
from decimal import Decimal, InvalidOperation
from django.utils import timezone


class LoanApplicationSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing Loan Applications"""

    user = UserSerializer(read_only=True)
    loan_type_info = LoanTypeListSerializer(source='loan_type', read_only=True)
    completion_percentage = serializers.SerializerMethodField()
    is_complete = serializers.SerializerMethodField()

    class Meta:
        model = LoanApplication
        fields = [
            'id',
            'user',
            'loan_application_uuid',
            'loan_type',
            'loan_type_info',
            'status',
            'approved_funds',
            'rejection_reason',
            'partner_commision',
            'approved_at',
            'rejected_at',
            'current_step',
            'submitted_at',
            'is_complete',
            'completion_percentage',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'user', 'loan_application_uuid', 'approved_at', 'rejected_at', 'approved_funds', 'rejection_reason', 'partner_commision', 'created_at', 'updated_at', 'is_complete', 'completion_percentage', 'current_step', 'submitted_at', 'status']

    def validate(self, data):
        """Prevent multiple pending applications for the same loan type per user."""
        request = self.context.get('request')
        loan_type = data.get('loan_type')

        if loan_type is None:
            raise serializers.ValidationError({'loan_type': 'This field is required.'})

        existing_pending = LoanApplication.objects.filter(
            user=request.user,
            loan_type=loan_type,
        ).exclude(status__in=[LoanApplicationStatus.APPROVED.value, LoanApplicationStatus.REJECTED.value])

        if self.instance:
            existing_pending = existing_pending.exclude(pk=self.instance.pk)

        if existing_pending.exists():
            raise serializers.ValidationError({'loan_type': 'A pending application already exists for this loan type. ' 'You can create another one after it is approved or rejected.'})

        return data

    def get_completion_percentage(self, obj):
        """Calculate completion percentage based on completed sections"""
        total_sections = 5  # business, funding, owner, terms, documents
        completed_sections = 0

        if hasattr(obj, 'businessinformation'):
            completed_sections += 1
        if hasattr(obj, 'businessfundinginformation'):
            completed_sections += 1
        if hasattr(obj, 'businessownerinformation_set') and obj.businessownerinformation_set.exists():
            completed_sections += 1
        if hasattr(obj, 'termsandconditions'):
            completed_sections += 1
        if hasattr(obj, 'loanapplicationdocument_set') and obj.loanapplicationdocument_set.exists():
            completed_sections += 1

        return int((completed_sections / total_sections) * 100)

    def get_is_complete(self, obj):
        """Check if all required sections are completed"""
        has_business_info = hasattr(obj, 'businessinformation')
        has_funding_info = hasattr(obj, 'businessfundinginformation')
        has_owner_info = hasattr(obj, 'businessownerinformation_set') and obj.businessownerinformation_set.exists()
        has_terms = hasattr(obj, 'termsandconditions')
        has_documents = hasattr(obj, 'loanapplicationdocument_set') and obj.loanapplicationdocument_set.exists()

        return all([has_business_info, has_funding_info, has_owner_info, has_terms, has_documents])


# Business Information Serializer
class BusinessInformationSerializer(serializers.ModelSerializer):
    """Serializer for Business Information"""

    user = UserSerializer(read_only=True)

    class Meta:
        model = BusinessInformation
        fields = [
            'id',
            'user',
            'loan_application',
            'loan_application_uuid',
            'business_uuid',
            # Section 1: Business Information
            'is_dba',
            'business_legal_name',
            'business_dba_name',
            'business_email',
            'business_phone_number',
            # Section 2: Address and Contact Information
            'business_website',
            'business_country',
            'business_state',
            'business_address',
            'business_city',
            'business_zip_code',
            # Section 3: Additional Business Information
            'business_industry_type',
            'business_legal_entity_type',
            'business_length_of_ownership',
            'business_number',
            'business_estimated_start_date',
            'business_province_of_incorporation',
            'business_average_gross_monthly_sales',
            # Other fields
            'created_at',
            'updated_at',
            'created_by',
        ]
        read_only_fields = ['id', 'user', 'loan_application', 'loan_application_uuid', 'business_uuid', 'created_at', 'updated_at', 'created_by']

    def validate_business_average_gross_monthly_sales(self, value):
        """Validate that business average gross monthly sales is positive"""
        if value < 0:
            raise serializers.ValidationError("Average gross monthly sales must be a positive value.")
        return value

    def validate_business_number(self, value):
        """Validate that business number is not empty"""
        if not value or len(value.strip()) < 9:
            raise serializers.ValidationError("Business number cannot be empty and must be at least 9 characters long.")
        return value.strip()

    def validate_business_estimated_start_date(self, value):
        """Validate that estimated start date is not in the future"""
        from django.utils import timezone

        if value > timezone.now().date():
            raise serializers.ValidationError("Estimated start date cannot be in the future.")
        return value


# Business Funding Information Serializer
class BusinessFundingInformationSerializer(serializers.ModelSerializer):
    """Serializer for Business Funding Information"""

    user = UserSerializer(read_only=True)

    class Meta:
        model = BusinessFundingInformation
        fields = [
            'id',
            'user',
            'loan_application',
            'loan_application_uuid',
            # Section 4: Business Funding Information
            'loan_amount_requested',
            'loan_purpose',
            'loan_term_requested',
            'overdraft_protection',
            'overdraft_protection_limit',
            'business_existing_loan',
            'business_lender_details',
            # Other fields
            'created_at',
            'updated_at',
            'created_by',
        ]
        read_only_fields = ['id', 'user', 'loan_application', 'loan_application_uuid', 'created_at', 'updated_at', 'created_by']

    def validate_loan_amount_requested(self, value):
        """Validate that loan amount requested is positive"""
        if value <= 0:
            raise serializers.ValidationError("Loan amount requested must be greater than zero.")
        return value

    def validate_overdraft_protection_limit(self, value):
        """Validate overdraft protection limit"""
        if value and value < 0:
            raise serializers.ValidationError("Overdraft protection limit must be a positive value.")
        return value

    def validate_business_lender_details(self, value):
        """Validate business lender details format against LENDER_INFORMATION_FORMAT"""
        if value:
            if not isinstance(value, list):
                raise serializers.ValidationError("Business lender details must be a list of lender information.")

            required_fields = {"lender_name", "balance"}

            for index, lender in enumerate(value):
                if not isinstance(lender, dict):
                    raise serializers.ValidationError(f"Lender at index {index} must be a dictionary.")

                # Validate required fields
                missing_fields = required_fields - lender.keys()
                if missing_fields:
                    raise serializers.ValidationError(f"Lender at index {index} is missing required fields: {list(missing_fields)}. " f"Required fields are: {list(required_fields)}")

                # Validate no extra fields
                extra_fields = lender.keys() - required_fields
                if extra_fields:
                    raise serializers.ValidationError(f"Lender at index {index} contains invalid fields: {list(extra_fields)}. " f"Allowed fields are: {list(required_fields)}")

                # Validate lender_name is a non-empty string
                if not isinstance(lender.get("lender_name"), str) or not lender["lender_name"].strip():
                    raise serializers.ValidationError(f"Lender at index {index}: 'lender_name' must be a non-empty string.")

                # Validate balance is a valid decimal
                try:
                    balance = Decimal(str(lender.get("balance", "")))
                    if balance < 0:
                        raise serializers.ValidationError(f"Lender at index {index}: 'balance' must be a positive decimal value.")
                except (InvalidOperation, ValueError):
                    raise serializers.ValidationError(f"Lender at index {index}: 'balance' must be a valid decimal number.")

        return value

    def validate(self, data):
        """Custom validation for related fields"""
        if data.get('overdraft_protection') and not data.get('overdraft_protection_limit'):
            raise serializers.ValidationError({'overdraft_protection_limit': 'Overdraft protection limit is required when overdraft protection is enabled.'})

        if data.get('business_existing_loan') and not data.get('business_lender_details'):
            raise serializers.ValidationError({'business_lender_details': 'Lender details are required when business has existing loans.'})

        return data


# Business Owner Information Serializer
class BusinessOwnerInformationSerializer(serializers.ModelSerializer):
    """Serializer for Business Owner Information"""

    user = UserSerializer(read_only=True)

    class Meta:
        model = BusinessOwnerInformation
        fields = [
            'id',
            'user',
            'loan_application',
            'loan_application_uuid',
            'owner_uuid',
            # Section 5: Business Owner Information
            'owner_first_name',
            'owner_last_name',
            'owner_email',
            'owner_phone_number',
            'owner_date_of_birth',
            'owner_ssn',
            'owner_address',
            'owner_city',
            'owner_state',
            'owner_zip_code',
            'owner_country',
            'owner_percentage_of_ownership',
            'owner_credit_score',
            # Other fields
            'created_at',
            'updated_at',
            'created_by',
        ]
        read_only_fields = ['id', 'user', 'loan_application', 'loan_application_uuid', 'owner_uuid', 'created_at', 'updated_at', 'created_by']

    def validate_owner_percentage_of_ownership(self, value):
        """Validate that ownership percentage is between 0 and 100"""
        if value < 0 or value > 100:
            raise serializers.ValidationError("Ownership percentage must be between 0 and 100.")
        return value

    def validate_owner_credit_score(self, value):
        """Validate credit score range"""
        if value < 0:
            raise serializers.ValidationError("Credit score must be a positive integer.")
        return value


# Terms and Conditions Serializer
class TermsAndConditionsSerializer(serializers.ModelSerializer):
    """Serializer for Terms and Conditions"""

    user = UserSerializer(read_only=True)

    class Meta:
        model = TermsAndConditions
        fields = [
            'id',
            'user',
            'loan_application',
            'loan_application_uuid',
            # Section 6: Terms and Conditions
            'signature_name',
            'signature_image',
            'terms_accepted',
            'accepted_at',
            # Other fields
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'user', 'loan_application', 'loan_application_uuid', 'accepted_at', 'created_at', 'updated_at']

    def validate(self, data):
        """Validate that terms are accepted"""
        if not data.get('terms_accepted'):
            raise serializers.ValidationError({'terms_accepted': 'You must accept the terms and conditions to proceed.'})
        return data


# Loan Application Document Serializer
class LoanApplicationDocumentSerializer(serializers.ModelSerializer):
    """Serializer for Loan Application Documents"""

    user = UserSerializer(read_only=True)

    class Meta:
        model = LoanApplicationDocument
        fields = [
            'id',
            'user',
            'loan_application',
            'loan_application_uuid',
            'document_uuid',
            'document_name',
            'document_file',
            'uploaded_at',
            'updated_at',
            'created_by',
        ]
        read_only_fields = ['id', 'user', 'loan_application', 'loan_application_uuid', 'document_uuid', 'uploaded_at', 'updated_at', 'created_by']

    def validate_document_file(self, value):
        """Validate document file size and type"""
        # Limit file size to 50MB
        if value.size > 50 * 1024 * 1024:
            raise serializers.ValidationError("File size must not exceed 50MB.")

        # Validate file extension
        allowed_extensions = ['.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png']
        import os

        ext = os.path.splitext(value.name)[1].lower()
        if ext not in allowed_extensions:
            raise serializers.ValidationError(f"File type not supported. Allowed types: {', '.join(allowed_extensions)}")

        return value


# Loan Application Serializer
class LoanApplicationNestedSerializer(serializers.ModelSerializer):
    """Main Loan Application Serializer with nested data"""

    user = UserSerializer(read_only=True)
    loan_type = LoanTypeListSerializer(read_only=True)

    # Nested related data (read-only)
    business_information = BusinessInformationSerializer(source='businessinformation', read_only=True)

    funding_information = BusinessFundingInformationSerializer(source='businessfundinginformation', read_only=True)
    owner_information = BusinessOwnerInformationSerializer(source='businessownerinformation_set', many=True, read_only=True)
    terms_and_conditions = TermsAndConditionsSerializer(source='termsandconditions', read_only=True)
    documents = LoanApplicationDocumentSerializer(source='loanapplicationdocument_set', many=True, read_only=True)

    # Computed fields
    is_complete = serializers.SerializerMethodField()
    completion_percentage = serializers.SerializerMethodField()

    class Meta:
        model = LoanApplication
        fields = [
            'id',
            'user',
            'loan_application_uuid',
            'loan_type',
            'status',
            'approved_funds',
            'current_step',
            'submitted_at',
            'created_at',
            'updated_at',
            # Nested data
            'business_information',
            'funding_information',
            'owner_information',
            'terms_and_conditions',
            'documents',
            # Computed fields
            'is_complete',
            'completion_percentage',
        ]
        read_only_fields = [
            'id',
            'user',
            'loan_application_uuid',
            'submitted_at',
            'created_at',
            'updated_at',
            'is_complete',
            'completion_percentage',
        ]

    def get_completion_percentage(self, obj):
        """Calculate completion percentage based on completed sections"""
        total_sections = 5  # business, funding, owner, terms, documents
        completed_sections = 0

        if hasattr(obj, 'businessinformation'):
            completed_sections += 1
        if hasattr(obj, 'businessfundinginformation'):
            completed_sections += 1
        if hasattr(obj, 'businessownerinformation_set') and obj.businessownerinformation_set.exists():
            completed_sections += 1
        if hasattr(obj, 'termsandconditions'):
            completed_sections += 1
        if hasattr(obj, 'loanapplicationdocument_set') and obj.loanapplicationdocument_set.exists():
            completed_sections += 1

        return int((completed_sections / total_sections) * 100)

    def get_is_complete(self, obj):
        """Check if all required sections are completed"""
        has_business_info = hasattr(obj, 'businessinformation')
        has_funding_info = hasattr(obj, 'businessfundinginformation')
        has_owner_info = hasattr(obj, 'businessownerinformation_set') and obj.businessownerinformation_set.exists()
        has_terms = hasattr(obj, 'termsandconditions')
        has_documents = hasattr(obj, 'loanapplicationdocument_set') and obj.loanapplicationdocument_set.exists()

        return all([has_business_info, has_funding_info, has_owner_info, has_terms, has_documents])


class LoanApplicationDecisionSerializer(serializers.ModelSerializer):
    """Serializer for admin/agent loan application approval or rejection decisions."""

    class Meta:
        model = LoanApplication
        fields = [
            'loan_application_uuid',
            'status',
            'approved_funds',
            'rejection_reason',
            'partner_commision',
            'approved_at',
            'rejected_at',
            'updated_at',
        ]
        read_only_fields = ['loan_application_uuid', 'updated_at', 'approved_at', 'rejected_at']

    def validate(self, data):
        instance = self.instance
        decision_status = data.get('status', instance.status if instance else None)

        if decision_status not in [LoanApplicationStatus.APPROVED.value, LoanApplicationStatus.REJECTED.value]:
            raise serializers.ValidationError({'status': 'Status must be either approved or rejected.'})

        if instance and instance.status in [LoanApplicationStatus.DRAFT.value, LoanApplicationStatus.APPROVED.value, LoanApplicationStatus.REJECTED.value]:
            raise serializers.ValidationError({'status': 'Only submitted or pending loan applications can be approved or rejected.'})

        approved_funds = data.get('approved_funds', instance.approved_funds if instance else None)
        rejection_reason = data.get('rejection_reason', instance.rejection_reason if instance else None)
        partner_commision = data.get('partner_commision', instance.partner_commision if instance else None)

        if decision_status == LoanApplicationStatus.APPROVED.value:
            if approved_funds is None:
                raise serializers.ValidationError({'approved_funds': 'approved_funds is required when approving a loan application.'})

            if approved_funds <= 0:
                raise serializers.ValidationError({'approved_funds': 'approved_funds must be greater than zero.'})

            if instance and instance.user and instance.user.partner:
                if partner_commision is None:
                    raise serializers.ValidationError({'partner_commision': 'partner_commision is required when approving an application with a partner.'})

                if partner_commision < 0:
                    raise serializers.ValidationError({'partner_commision': 'partner_commision cannot be negative.'})
            elif partner_commision is not None:
                raise serializers.ValidationError({'partner_commision': 'partner_commision is only allowed when the applicant has a partner.'})

            data['rejection_reason'] = None

        if decision_status == LoanApplicationStatus.REJECTED.value:
            if not rejection_reason or not str(rejection_reason).strip():
                raise serializers.ValidationError({'rejection_reason': 'rejection_reason is required when rejecting a loan application.'})

            data['approved_funds'] = None
            data['partner_commision'] = None

        return data

    def update(self, instance, validated_data):
        decision_status = validated_data.get('status', instance.status)
        instance.status = decision_status
        instance.approved_funds = validated_data.get('approved_funds', instance.approved_funds)
        instance.rejection_reason = validated_data.get('rejection_reason', instance.rejection_reason)
        instance.partner_commision = validated_data.get('partner_commision', instance.partner_commision)

        if decision_status == LoanApplicationStatus.APPROVED.value:
            instance.approved_at = timezone.now()
            instance.rejected_at = None
        elif decision_status == LoanApplicationStatus.REJECTED.value:
            instance.rejected_at = timezone.now()
            instance.approved_at = None

        instance.save(update_fields=['status', 'approved_funds', 'rejection_reason', 'partner_commision', 'updated_at', 'approved_at', 'rejected_at'])
        return instance
