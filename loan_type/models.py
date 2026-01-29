from django.db import models


# Create your models here.


class LoanType(models.Model):
    name = models.CharField(max_length=255, unique=True)
    rates = models.DecimalField(max_digits=5, decimal_places=2)
    decision_time = models.CharField(max_length=255)
    amount = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey('applicant.User', on_delete=models.CASCADE, related_name='loantype_created_by')

    def __str__(self):
        return self.name
