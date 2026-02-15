import uuid
from django.db import models
from applicant.models import User
from .utils import LoanApplicationStatus, LoanApplicationStep
from loan_type.models import LoanType

# Create your models here.


class LoanApplication(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    loan_application_uuid = models.UUIDField(unique=True, default=uuid.uuid4)
    loan_type = models.ForeignKey(LoanType, on_delete=models.CASCADE, null=True, blank=True, related_name='loan_application_loan_type')
    status = models.CharField(max_length=50, choices=LoanApplicationStatus.choices(), default=LoanApplicationStatus.DRAFT.value)
    current_step = models.CharField(max_length=100, choices=LoanApplicationStep.choices(), default=LoanApplicationStep.BUSINESS_INFORMATION.value)
    submitted_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class BusinessInformation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    loan_application = models.OneToOneField(LoanApplication, on_delete=models.CASCADE)
    loan_application_uuid = models.UUIDField(unique=True)
    business_uuid = models.UUIDField(unique=True, default=uuid.uuid4)
    # section 1 Business information
    is_dba = models.BooleanField(default=False)
    business_legal_name = models.CharField(max_length=255)
    business_dba_name = models.CharField(max_length=255)
    business_email = models.EmailField()
    business_phone_number = models.CharField(max_length=20)
    # section 2 Address and contact information
    business_website = models.URLField(blank=True, null=True)
    business_country = models.CharField(max_length=100)
    business_state = models.CharField(max_length=100)
    business_address = models.TextField()
    business_city = models.CharField(max_length=100)
    business_zip_code = models.CharField(max_length=20)
    # section 3 Additional Business Information
    business_industry_type = models.CharField(max_length=100)
    business_legal_entity_name = models.CharField(max_length=100)
    business_length_of_ownership = models.CharField(max_length=50)
    business_number = models.CharField(max_length=100)
    business_estimated_start_date = models.DateField()
    business_province_of_incorporation = models.CharField(max_length=100)
    business_average_gross_monthly_sales = models.DecimalField(max_digits=15, decimal_places=2)
    # other fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.business_legal_name


class BusinessFundingInformation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    loan_application = models.OneToOneField(LoanApplication, on_delete=models.CASCADE)
    loan_application_uuid = models.UUIDField(unique=True)
    # section 4 Business Funding Information
    loan_amount_requested = models.DecimalField(max_digits=10, decimal_places=2)
    loan_purpose = models.TextField()
    loan_term_requested = models.CharField(max_length=100)
    overdraft_protection = models.BooleanField(default=False)
    overdraft_protection_limit = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    business_existing_loan = models.BooleanField(default=False)
    business_lender_details = models.JSONField(blank=True, null=True)
