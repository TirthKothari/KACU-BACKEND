from django.shortcuts import get_object_or_404
from django.db.models import Q
from .models import LoanApplication
from applicant.utils import UserRoleChoices


def get_loan_application(uuid, actor):
    """Fetch a LoanApplication by UUID scoped to the authenticated user."""
    return get_object_or_404(LoanApplication, Q(user=actor) | Q(user__partner=actor) | Q(user__assigned_agent=actor), loan_application_uuid=uuid)


def get_role_based_queryset(user, model, role):
    """Return a queryset of models filtered based on the user's role."""
    if role == UserRoleChoices.ADMIN.value:
        return model.objects.all().order_by('-created_at')
    elif role == UserRoleChoices.PARTNER.value:
        return model.objects.filter(user__partner=user).order_by('-created_at')
    elif role == UserRoleChoices.AGENT.value:
        return model.objects.filter(user__assigned_agent=user).order_by('-created_at')
    elif role == UserRoleChoices.APPLICANT.value:
        return model.objects.filter(user=user).order_by('-created_at')
    else:
        return model.objects.none()


def is_loan_application_submitted(loan_application):
    """Check if loan application is submitted (status is SUBMITTED or beyond)."""
    from .utils import LoanApplicationStatus

    return loan_application.status == LoanApplicationStatus.SUBMITTED.value or loan_application.submitted_at is not None


def check_loan_application_submitted(loan_application):
    """Raise error if loan application is submitted."""
    from rest_framework.exceptions import ValidationError

    if is_loan_application_submitted(loan_application):
        raise ValidationError("Cannot update this information after the loan application has been submitted. " "Please contact support if you need to make changes.")


def check_loan_application_terminal(loan_application):
    """Raise error if loan application is in a terminal state (APPROVED or REJECTED)."""
    from rest_framework.exceptions import ValidationError
    from .utils import LoanApplicationStatus

    if loan_application.status in [LoanApplicationStatus.APPROVED.value, LoanApplicationStatus.REJECTED.value]:
        raise ValidationError("Cannot update this information after the loan application has been approved or rejected. " "Please contact support if you need to make changes.")
