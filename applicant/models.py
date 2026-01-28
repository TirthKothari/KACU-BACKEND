from django.db import models
from django.contrib.auth.models import AbstractUser
from .utils import (
    LoanAmountChoices,
    LoanTermChoices,
    BusinessLocationChoices,
    YearsInBusinessChoices,
    UserRoleChoices,
)
from .helpers import generate_referral_code
from django.core.validators import RegexValidator
import uuid

# Create your models here.


class User(AbstractUser):
    phone = models.CharField(
        max_length=20,
        validators=[
            RegexValidator(
                regex=r"^\+?1?\d{9,15}$",
                message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.",
            )
        ],
    )
    is_qualified = models.BooleanField(default=False)
    role = models.CharField(max_length=50, choices=UserRoleChoices.choices(), default=UserRoleChoices.APPLICANT.value)
    partner = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='partner_user')
    reference_code = models.CharField(max_length=20, unique=True, null=True, blank=True)
    assigned_agent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='applicant_assigned_agent')

    def save(self, *args, **kwargs):
        if not self.reference_code and self.role == UserRoleChoices.PARTNER.value:
            code = generate_referral_code()
            while User.objects.filter(reference_code=code).exists():
                code = generate_referral_code()
            self.reference_code = code
        super().save(*args, **kwargs)


class pre_qualification(models.Model):
    uuid = models.UUIDField(unique=True, default=uuid.uuid4)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='prequalification_user')
    business_name = models.CharField(max_length=255)
    loan_amount = models.CharField(max_length=255, choices=LoanAmountChoices.choices())
    # loan_type = models.CharField(max_length=255, choices=LoanTypeChoices.choices())
    loan_type = models.ForeignKey('loan_type.LoanType', on_delete=models.SET_NULL, null=True, blank=True, related_name='prequalification_loan_type')
    loan_term = models.CharField(max_length=255, choices=LoanTermChoices.choices())
    business_location = models.CharField(max_length=255, choices=BusinessLocationChoices.choices())
    years_in_business = models.CharField(max_length=255, choices=YearsInBusinessChoices.choices())
    annual_revenue = models.FloatField()
    is_qualified = models.BooleanField(default=False)
    name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(
        max_length=20,
        default="+9190041179290",
        validators=[
            RegexValidator(
                regex=r"^\+?1?\d{9,15}$",
                message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.",  # noqa
            )
        ],
    )
    partner = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, blank=True, related_name='prequalification_partner_user')
    refernce_code = models.CharField(max_length=20, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.user:
            return f"{self.business_name} - {self.user.username}"
        return f"{self.business_name} - No User"
