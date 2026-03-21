from django.contrib import admin

from .models import (
    LoanApplication,
    BusinessInformation,
    BusinessFundingInformation,
    BusinessOwnerInformation,
    TermsAndConditions,
    LoanApplicationDocument,
)


@admin.register(LoanApplication)
class LoanApplicationAdmin(admin.ModelAdmin):
    list_display = (
        'loan_application_uuid',
        'user',
        'loan_type',
        'status',
        'approved_funds',
        'partner_commision',
        'submitted_at',
        'approved_at',
        'rejected_at',
        'created_at',
    )
    list_filter = (
        'status',
        'current_step',
        'loan_type',
        'created_at',
        'updated_at',
        'submitted_at',
        'approved_at',
        'rejected_at',
    )
    search_fields = (
        'loan_application_uuid',
        'user__username',
        'user__email',
        'user__first_name',
        'user__last_name',
        'rejection_reason',
    )
    readonly_fields = (
        'loan_application_uuid',
        'created_at',
        'updated_at',
        'submitted_at',
        'approved_at',
        'rejected_at',
    )
    list_select_related = ('user', 'loan_type')
    ordering = ('-created_at',)
    autocomplete_fields = ('user', 'loan_type')
    date_hierarchy = 'created_at'


@admin.register(BusinessInformation)
class BusinessInformationAdmin(admin.ModelAdmin):
    list_display = (
        'business_uuid',
        'loan_application_uuid',
        'business_legal_name',
        'business_email',
        'business_country',
        'business_state',
        'business_city',
        'user',
        'created_by',
        'created_at',
    )
    list_filter = (
        'business_country',
        'business_legal_entity_type',
        'is_dba',
        'created_at',
        'updated_at',
    )
    search_fields = (
        'business_uuid',
        'loan_application_uuid',
        'business_legal_name',
        'business_dba_name',
        'business_email',
        'business_phone_number',
        'business_number',
        'user__username',
        'user__email',
        'user__first_name',
        'user__last_name',
    )
    readonly_fields = (
        'business_uuid',
        'loan_application_uuid',
        'created_at',
        'updated_at',
    )
    list_select_related = ('user', 'loan_application', 'created_by')
    ordering = ('-created_at',)
    autocomplete_fields = ('user', 'loan_application', 'created_by')
    date_hierarchy = 'created_at'


@admin.register(BusinessFundingInformation)
class BusinessFundingInformationAdmin(admin.ModelAdmin):
    list_display = (
        'loan_application_uuid',
        'user',
        'loan_amount_requested',
        'loan_term_requested',
        'overdraft_protection',
        'business_existing_loan',
        'created_by',
        'created_at',
    )
    list_filter = (
        'overdraft_protection',
        'business_existing_loan',
        'created_at',
        'updated_at',
    )
    search_fields = (
        'loan_application_uuid',
        'loan_purpose',
        'loan_term_requested',
        'user__username',
        'user__email',
        'user__first_name',
        'user__last_name',
    )
    readonly_fields = (
        'loan_application_uuid',
        'created_at',
        'updated_at',
    )
    list_select_related = ('user', 'loan_application', 'created_by')
    ordering = ('-created_at',)
    autocomplete_fields = ('user', 'loan_application', 'created_by')
    date_hierarchy = 'created_at'


@admin.register(BusinessOwnerInformation)
class BusinessOwnerInformationAdmin(admin.ModelAdmin):
    list_display = (
        'owner_uuid',
        'loan_application_uuid',
        'owner_first_name',
        'owner_last_name',
        'owner_email',
        'owner_country',
        'owner_percentage_of_ownership',
        'owner_credit_score',
        'user',
        'created_at',
    )
    list_filter = (
        'owner_country',
        'created_at',
        'updated_at',
    )
    search_fields = (
        'owner_uuid',
        'loan_application_uuid',
        'owner_first_name',
        'owner_last_name',
        'owner_email',
        'owner_phone_number',
        'owner_ssn',
        'user__username',
        'user__email',
        'user__first_name',
        'user__last_name',
    )
    readonly_fields = (
        'owner_uuid',
        'loan_application_uuid',
        'created_at',
        'updated_at',
    )
    list_select_related = ('user', 'loan_application', 'created_by')
    ordering = ('-created_at',)
    autocomplete_fields = ('user', 'loan_application', 'created_by')
    date_hierarchy = 'created_at'


@admin.register(TermsAndConditions)
class TermsAndConditionsAdmin(admin.ModelAdmin):
    list_display = (
        'loan_application_uuid',
        'user',
        'signature_name',
        'terms_accepted',
        'accepted_at',
        'created_at',
    )
    list_filter = (
        'terms_accepted',
        'accepted_at',
        'created_at',
        'updated_at',
    )
    search_fields = (
        'loan_application_uuid',
        'signature_name',
        'user__username',
        'user__email',
        'user__first_name',
        'user__last_name',
    )
    readonly_fields = (
        'loan_application_uuid',
        'accepted_at',
        'created_at',
        'updated_at',
    )
    list_select_related = ('user', 'loan_application')
    ordering = ('-created_at',)
    autocomplete_fields = ('user', 'loan_application')
    date_hierarchy = 'created_at'


@admin.register(LoanApplicationDocument)
class LoanApplicationDocumentAdmin(admin.ModelAdmin):
    list_display = (
        'document_uuid',
        'loan_application_uuid',
        'document_name',
        'user',
        'created_by',
        'uploaded_at',
        'updated_at',
    )
    list_filter = (
        'document_name',
        'uploaded_at',
        'updated_at',
    )
    search_fields = (
        'document_uuid',
        'loan_application_uuid',
        'document_name',
        'user__username',
        'user__email',
        'user__first_name',
        'user__last_name',
    )
    readonly_fields = (
        'document_uuid',
        'loan_application_uuid',
        'uploaded_at',
        'updated_at',
    )
    list_select_related = ('user', 'loan_application', 'created_by')
    ordering = ('-uploaded_at',)
    autocomplete_fields = ('user', 'loan_application', 'created_by')
    date_hierarchy = 'uploaded_at'
