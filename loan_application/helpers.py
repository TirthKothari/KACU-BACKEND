from django.shortcuts import get_object_or_404
from .models import LoanApplication


def get_loan_application(uuid, user):
    """Fetch a LoanApplication by UUID scoped to the authenticated user."""
    return get_object_or_404(LoanApplication, loan_application_uuid=uuid, user=user)
