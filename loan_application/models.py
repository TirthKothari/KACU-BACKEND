import uuid
from django.db import models
from applicant.models import User
from .utils import LoanApplicationStatus, LoanApplicationStep, DocumentType, BusinessLegalEntityType
from loan_type.models import LoanType
from django.core.validators import RegexValidator
from applicant.utils import BusinessLocationChoices
from django.db.models import Q
from .utils import LoanApplicationStatus

# Create your models here.


class LoanApplication(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    loan_application_uuid = models.UUIDField(unique=True, default=uuid.uuid4)
    loan_type = models.ForeignKey(LoanType, on_delete=models.CASCADE, null=True, blank=True, related_name='loan_application_loan_type')
    status = models.CharField(max_length=50, choices=LoanApplicationStatus.choices(), default=LoanApplicationStatus.DRAFT.value)
    approved_funds = models.DecimalField(max_digits=40, decimal_places=10, blank=True, null=True)
    rejection_reason = models.TextField(blank=True, null=True)
    partner_commision = models.DecimalField(max_digits=40, decimal_places=10, blank=True, null=True)
    current_step = models.CharField(max_length=100, choices=LoanApplicationStep.choices(), default=LoanApplicationStep.BUSINESS_INFORMATION.value)
    submitted_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name} - {self.loan_application_uuid}"

    class Meta:
        constraints = [models.UniqueConstraint(fields=['user', 'loan_type'], condition=~Q(status__in=[LoanApplicationStatus.APPROVED.value, LoanApplicationStatus.REJECTED.value]), name='unique_active_loan_application_per_user_and_type')]


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
    business_phone_number = models.CharField(
        max_length=20,
        default="+9190041179290",
        validators=[
            RegexValidator(
                regex=r"^\+?1?\d{9,15}$",
                message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.",  # noqa
            )
        ],
    )
    # section 2 Address and contact information
    business_website = models.URLField(blank=True, null=True)
    business_country = models.CharField(max_length=100, choices=BusinessLocationChoices.choices())
    business_state = models.CharField(max_length=100)
    business_address = models.TextField()
    business_city = models.CharField(max_length=100)
    business_zip_code = models.CharField(max_length=20)
    # section 3 Additional Business Information
    business_industry_type = models.CharField(max_length=100)
    business_legal_entity_type = models.CharField(max_length=100, choices=BusinessLegalEntityType.choices())
    business_length_of_ownership = models.CharField(max_length=50)
    business_number = models.CharField(max_length=100)
    business_estimated_start_date = models.DateField()
    business_province_of_incorporation = models.CharField(max_length=100)
    business_average_gross_monthly_sales = models.DecimalField(max_digits=40, decimal_places=10)
    # other fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.business_legal_name


LENDER_INFORMATION_FORMAT = '''
[
    {
        "lender_name": "string",
        "balance": "decimal",
    }
]
'''


class BusinessFundingInformation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    loan_application = models.OneToOneField(LoanApplication, on_delete=models.CASCADE)
    loan_application_uuid = models.UUIDField(unique=True)
    # section 4 Business Funding Information
    loan_amount_requested = models.DecimalField(max_digits=40, decimal_places=10)
    loan_purpose = models.TextField()
    loan_term_requested = models.CharField(max_length=100)
    overdraft_protection = models.BooleanField(default=False)
    overdraft_protection_limit = models.DecimalField(max_digits=40, decimal_places=10, blank=True, null=True)
    business_existing_loan = models.BooleanField(default=False)
    business_lender_details = models.JSONField(blank=True, null=True, help_text=LENDER_INFORMATION_FORMAT)

    # other fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.loan_application.user.first_name} {self.loan_application.user.last_name} - {self.loan_amount_requested}"


class BusinessOwnerInformation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    loan_application = models.ForeignKey(LoanApplication, on_delete=models.CASCADE)
    loan_application_uuid = models.UUIDField()
    owner_uuid = models.UUIDField(unique=True, default=uuid.uuid4)
    # section 5 Business Owner Information
    owner_first_name = models.CharField(max_length=100)
    owner_last_name = models.CharField(max_length=100)
    owner_email = models.EmailField()
    owner_phone_number = models.CharField(
        max_length=20,
        default="+9190041179290",
        validators=[
            RegexValidator(
                regex=r"^\+?1?\d{9,15}$",
                message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.",  # noqa
            )
        ],
    )
    owner_date_of_birth = models.DateField()
    owner_ssn = models.CharField(max_length=11)
    owner_address = models.TextField()
    owner_city = models.CharField(max_length=100)
    owner_state = models.CharField(max_length=100)
    owner_zip_code = models.CharField(max_length=20)
    owner_country = models.CharField(max_length=100, choices=BusinessLocationChoices.choices())
    owner_percentage_of_ownership = models.DecimalField(max_digits=5, decimal_places=2)
    owner_credit_score = models.IntegerField()
    # other fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('loan_application', 'owner_email')

    def __str__(self):
        return f"{self.owner_first_name} {self.owner_last_name}"


class TermsAndConditions(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    loan_application = models.OneToOneField(LoanApplication, on_delete=models.CASCADE)
    loan_application_uuid = models.UUIDField(unique=True)
    # section 6 Terms and Conditions
    signature_name = models.CharField(max_length=255)
    signature_image = models.ImageField(upload_to='signatures/')
    terms_accepted = models.BooleanField(default=False)
    accepted_at = models.DateTimeField(auto_now_add=True)
    # other fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.loan_application.user.first_name} {self.loan_application.user.last_name} - Terms Accepted"


class LoanApplicationDocument(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    loan_application = models.ForeignKey(LoanApplication, on_delete=models.CASCADE)
    loan_application_uuid = models.UUIDField(unique=True)
    document_uuid = models.UUIDField(unique=True, default=uuid.uuid4)
    document_name = models.CharField(max_length=255, choices=DocumentType.choices())
    document_file = models.FileField(upload_to='loan_documents/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('loan_application', 'document_name')

    def __str__(self):
        return f"{self.document_name} - {self.loan_application.user.first_name} {self.loan_application.user.last_name}"
