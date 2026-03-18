from datetime import datetime
from rest_framework import generics
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import (
    LoanApplication,
    BusinessInformation,
    BusinessFundingInformation,
    BusinessOwnerInformation,
    TermsAndConditions,
    LoanApplicationDocument,
)
from django.db import transaction
from loan_application.utils import LoanApplicationStep, LoanApplicationStatus
from .serializers import (
    LoanApplicationSerializer,
    LoanApplicationNestedSerializer,
    BusinessInformationSerializer,
    BusinessFundingInformationSerializer,
    BusinessOwnerInformationSerializer,
    TermsAndConditionsSerializer,
    LoanApplicationDocumentSerializer,
)
import api.permissions as permissions
from .helpers import check_loan_application_submitted, check_loan_application_terminal, get_loan_application
from applicant.utils import UserRoleChoices
from .helpers import get_role_based_queryset
from rest_framework.exceptions import ValidationError


# ─── Loan Application ─────────────────────────────────────────────────────────


class LoanApplicationListView(generics.ListAPIView):
    """
    GET  /loan-applications/       → list all loan applications for the user
    """

    permission_classes = [permissions.IsAuthenticatedWithRole]
    serializer_class = LoanApplicationSerializer

    def get_queryset(self):
        user = self.request.user
        role = getattr(user, 'role', None)

        return get_role_based_queryset(user, LoanApplication, role)

        # if role == UserRoleChoices.APPLICANT.value:
        #     return LoanApplication.objects.filter(user=self.request.user).order_by('-created_at')

        # elif role == UserRoleChoices.AGENT.value:
        #     return LoanApplication.objects.filter(user__assigned_agent=self.request.user).order_by('-created_at')

        # elif role == UserRoleChoices.PARTNER.value:
        #     return LoanApplication.objects.filter(user__partner=self.request.user).order_by('-created_at')

        # elif role == UserRoleChoices.ADMIN.value:
        #     return LoanApplication.objects.all().order_by('-created_at')
        # else:
        #     return LoanApplication.objects.none()


class LoanApplicationCreateView(generics.CreateAPIView):
    """
    POST /loan-applications/create/       → create a new loan application
    """

    permission_classes = [permissions.IsApplicant]
    serializer_class = LoanApplicationSerializer

    @transaction.atomic
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class LoanApplicationRetrieveView(generics.RetrieveAPIView):
    """
    GET /<loan_application_uuid>/  → retrieve with full nested data
    """

    permission_classes = [permissions.IsAuthenticatedWithRole]
    serializer_class = LoanApplicationNestedSerializer
    lookup_field = 'loan_application_uuid'

    def get_queryset(self):
        user = self.request.user
        role = getattr(user, 'role', None)

        return get_role_based_queryset(user, LoanApplication, role)

        # if role == UserRoleChoices.APPLICANT.value:
        #     return LoanApplication.objects.filter(user=self.request.user).order_by('-created_at')

        # elif role == UserRoleChoices.AGENT.value:
        #     return LoanApplication.objects.filter(user__assigned_agent=self.request.user).order_by('-created_at')

        # elif role == UserRoleChoices.PARTNER.value:
        #     return LoanApplication.objects.filter(user__partner=self.request.user).order_by('-created_at')

        # elif role == UserRoleChoices.ADMIN.value:
        #     return LoanApplication.objects.all().order_by('-created_at')
        # else:
        #     return LoanApplication.objects.none()


class LoanApplicationCurrentStepView(APIView):
    """
    GET /loan-applications/<loan_application_uuid>/current-step/  → get current step of the application
    """

    permission_classes = [permissions.IsApplicant]

    def get(self, request, loan_application_uuid):
        loan_application = get_loan_application(loan_application_uuid, request.user)
        return Response({'current_step': loan_application.current_step})


# ─── Business Information ─────────────────────────────────────────────────────


class BusinessInformationCreateView(generics.CreateAPIView):
    """
    POST /business-information/create/    → create business information for a loan application
    """

    permission_classes = [permissions.IsApplicantOrPartner]
    serializer_class = BusinessInformationSerializer

    @transaction.atomic
    def perform_create(self, serializer):
        loan_application_uuid = self.request.data.get('loan_application_uuid')
        loan_application = get_loan_application(loan_application_uuid, self.request.user)
        check_loan_application_submitted(loan_application)
        check_loan_application_terminal(loan_application)
        serializer.save(
            user=loan_application.user,
            loan_application=loan_application,
            loan_application_uuid=loan_application.loan_application_uuid,
            created_by=self.request.user,
        )
        loan_application.current_step = LoanApplicationStep.BUSINESS_INFORMATION.value
        loan_application.save(update_fields=['current_step', 'updated_at'])


class BusinessInformationRetrieveView(generics.RetrieveAPIView):
    """
    GET /business-information/<loan_application_uuid>/  → retrieve business information
    """

    permission_classes = [permissions.IsAuthenticatedWithRole]
    serializer_class = BusinessInformationSerializer
    lookup_field = 'loan_application_uuid'

    def get_queryset(self):
        user = self.request.user
        role = getattr(user, 'role', None)

        return get_role_based_queryset(user, BusinessInformation, role)


class BusinessInformationUpdateView(generics.UpdateAPIView):
    """
    PUT   /business-information/<loan_application_uuid>/update/  → full update
    PATCH /business-information/<loan_application_uuid>/update/  → partial update
    """

    permission_classes = [permissions.IsApplicantOrPartner]
    serializer_class = BusinessInformationSerializer
    lookup_field = 'loan_application_uuid'

    def get_queryset(self):
        user = self.request.user
        role = getattr(user, 'role', None)

        return get_role_based_queryset(user, BusinessInformation, role)

    def perform_update(self, serializer):
        loan_application = serializer.instance.loan_application
        check_loan_application_submitted(loan_application)
        check_loan_application_terminal(loan_application)
        serializer.save()


# ─── Business Funding Information ─────────────────────────────────────────────


class BusinessFundingInformationCreateView(generics.CreateAPIView):
    """
    POST /funding-information/create/     → create funding information for a loan application
    """

    permission_classes = [permissions.IsApplicantOrPartner]
    serializer_class = BusinessFundingInformationSerializer

    @transaction.atomic
    def perform_create(self, serializer):
        loan_application_uuid = self.request.data.get('loan_application_uuid')
        loan_application = get_loan_application(loan_application_uuid, self.request.user)
        check_loan_application_submitted(loan_application)
        check_loan_application_terminal(loan_application)
        serializer.save(
            user=loan_application.user,
            loan_application=loan_application,
            loan_application_uuid=loan_application.loan_application_uuid,
            created_by=self.request.user,
        )
        loan_application.current_step = LoanApplicationStep.FUNDING_INFORMATION.value
        loan_application.save(update_fields=['current_step', 'updated_at'])


class BusinessFundingInformationRetrieveView(generics.RetrieveAPIView):
    """
    GET /funding-information/<loan_application_uuid>/  → retrieve funding information
    """

    permission_classes = [permissions.IsAuthenticatedWithRole]
    serializer_class = BusinessFundingInformationSerializer
    lookup_field = 'loan_application_uuid'

    def get_queryset(self):
        user = self.request.user
        role = getattr(user, 'role', None)

        return get_role_based_queryset(user, BusinessFundingInformation, role)


class BusinessFundingInformationUpdateView(generics.UpdateAPIView):
    """
    PUT   /funding-information/<loan_application_uuid>/update/  → full update
    PATCH /funding-information/<loan_application_uuid>/update/  → partial update
    """

    permission_classes = [permissions.IsApplicantOrPartner]
    serializer_class = BusinessFundingInformationSerializer
    lookup_field = 'loan_application_uuid'

    def get_queryset(self):
        user = self.request.user
        role = getattr(user, 'role', None)

        return get_role_based_queryset(user, BusinessFundingInformation, role)

    def perform_update(self, serializer):
        loan_application = serializer.instance.loan_application
        check_loan_application_submitted(loan_application)
        check_loan_application_terminal(loan_application)
        serializer.save()


# ─── Business Owner Information ───────────────────────────────────────────────


class BusinessOwnerInformationCreateView(generics.CreateAPIView):
    """
    POST /owner-information/create      → add an owner to a loan application
    """

    permission_classes = [permissions.IsApplicantOrPartner]
    serializer_class = BusinessOwnerInformationSerializer

    @transaction.atomic
    def perform_create(self, serializer):
        loan_application_uuid = self.request.data.get('loan_application_uuid')
        loan_application = get_loan_application(loan_application_uuid, self.request.user)
        check_loan_application_submitted(loan_application)
        check_loan_application_terminal(loan_application)
        serializer.save(
            user=loan_application.user,
            loan_application=loan_application,
            loan_application_uuid=loan_application.loan_application_uuid,
            created_by=self.request.user,
        )
        loan_application.current_step = LoanApplicationStep.BUSINESS_OWNERSHIP_INFORMATION.value
        loan_application.save(update_fields=['current_step', 'updated_at'])


class BusinessOwnerInformationListView(generics.ListAPIView):
    """
    GET /<loan_application_uuid>/owners/  → list all owners
    """

    permission_classes = [permissions.IsAuthenticatedWithRole]
    serializer_class = BusinessOwnerInformationSerializer

    def get_queryset(self):
        user = self.request.user
        role = getattr(user, 'role', None)
        loan_application_uuid = self.kwargs.get('loan_application_uuid')
        loan_application = get_loan_application(loan_application_uuid, self.request.user) if role != UserRoleChoices.ADMIN.value else get_object_or_404(LoanApplication, loan_application_uuid=loan_application_uuid)
        qs = get_role_based_queryset(user, BusinessOwnerInformation, role)
        return qs.filter(loan_application=loan_application)


class BusinessOwnerInformationRetrieveView(generics.RetrieveAPIView):
    """
    GET /owner-information/<owner_uuid>/   → retrieve a single owner record
    """

    permission_classes = [permissions.IsAuthenticatedWithRole]
    serializer_class = BusinessOwnerInformationSerializer
    lookup_field = 'owner_uuid'

    def get_queryset(self):
        user = self.request.user
        role = getattr(user, 'role', None)

        return get_role_based_queryset(user, BusinessOwnerInformation, role)


class BusinessOwnerInformationUpdateView(generics.UpdateAPIView):
    """
    PUT   /owner-information/<owner_uuid>/update/  → full update
    PATCH /owner-information/<owner_uuid>/update/  → partial update
    """

    permission_classes = [permissions.IsAuthenticatedWithRole]
    serializer_class = BusinessOwnerInformationSerializer
    lookup_field = 'owner_uuid'

    def get_queryset(self):
        user = self.request.user
        role = getattr(user, 'role', None)

        return get_role_based_queryset(user, BusinessOwnerInformation, role)

    def perform_update(self, serializer):
        loan_application = serializer.instance.loan_application
        check_loan_application_submitted(loan_application)
        check_loan_application_terminal(loan_application)
        serializer.save()


# ─── Terms and Conditions ─────────────────────────────────────────────────────


class TermsAndConditionsCreateView(generics.CreateAPIView):
    """
    POST /terms-and-conditions/    → submit terms and conditions for a loan application
    """

    permission_classes = [permissions.IsApplicant]
    serializer_class = TermsAndConditionsSerializer

    @transaction.atomic
    def perform_create(self, serializer):
        loan_application_uuid = self.request.data.get('loan_application_uuid')
        loan_application = get_loan_application(loan_application_uuid, self.request.user)
        check_loan_application_submitted(loan_application)
        check_loan_application_terminal(loan_application)
        serializer.save(
            user=self.request.user,
            loan_application=loan_application,
            loan_application_uuid=loan_application.loan_application_uuid,
            accepted_at=datetime.now(),
        )
        loan_application.current_step = LoanApplicationStep.TERMS_AND_CONDITIONS.value
        loan_application.submitted_at = datetime.now()
        loan_application.status = LoanApplicationStatus.SUBMITTED.value
        loan_application.save(update_fields=['current_step', 'submitted_at', 'status', 'updated_at'])


class TermsAndConditionsRetrieveView(generics.RetrieveAPIView):
    """
    GET /terms-and-conditions/<loan_application_uuid>/  → retrieve terms and conditions
    """

    permission_classes = [permissions.IsAuthenticatedWithRole]
    serializer_class = TermsAndConditionsSerializer
    lookup_field = 'loan_application_uuid'

    def get_queryset(self):
        user = self.request.user
        role = getattr(user, 'role', None)

        return get_role_based_queryset(user, TermsAndConditions, role)


# class TermsAndConditionsUpdateView(generics.UpdateAPIView):
#     """
#     PUT   /terms-and-conditions/<loan_application_uuid>/update/  → full update
#     PATCH /terms-and-conditions/<loan_application_uuid>/update/  → partial update
#     """

#     permission_classes = [permissions.Is]
#     serializer_class = TermsAndConditionsSerializer
#     lookup_field = 'loan_application_uuid'

#     def get_queryset(self):
#         user = self.request.user
#         role = getattr(user, 'role', None)

#         return get_role_based_queryset(user, TermsAndConditions, role)


# ─── Loan Application Documents ───────────────────────────────────────────────


class LoanApplicationDocumentCreateView(generics.CreateAPIView):
    """
    POST /documents/               → upload a document for a loan application
    """

    permission_classes = [permissions.IsApplicantOrPartner]
    serializer_class = LoanApplicationDocumentSerializer

    @transaction.atomic
    def perform_create(self, serializer):
        loan_application_uuid = self.request.data.get('loan_application_uuid')
        loan_application = get_loan_application(loan_application_uuid, self.request.user)
        if loan_application.status != LoanApplicationStatus.SUBMITTED.value or loan_application.submitted_at is None:
            raise ValidationError("Cannot upload documents for a loan application that is not submitted.")
        check_loan_application_terminal(loan_application)
        serializer.save(
            user=loan_application.user,
            loan_application=loan_application,
            loan_application_uuid=loan_application.loan_application_uuid,
            created_by=self.request.user,
        )
        loan_application.current_step = LoanApplicationStep.DOCUMENT_UPLOAD.value
        loan_application.status = LoanApplicationStatus.PENDING.value if loan_application.status == LoanApplicationStatus.SUBMITTED.value else loan_application.status
        loan_application.save(update_fields=['current_step', 'status', 'updated_at'])


class LoanApplicationDocumentListView(generics.ListAPIView):
    """
    GET /loan-applications/<loan_application_uuid>/documents/  → list all documents
    """

    permission_classes = [permissions.IsAuthenticatedWithRole]
    serializer_class = LoanApplicationDocumentSerializer

    def get_queryset(self):
        loan_application_uuid = self.kwargs.get('loan_application_uuid')
        loan_application = get_loan_application(loan_application_uuid, self.request.user) if self.request.user.role != UserRoleChoices.ADMIN.value else get_object_or_404(LoanApplication, loan_application_uuid=loan_application_uuid)
        qs = get_role_based_queryset(self.request.user, LoanApplicationDocument, self.request.user.role)
        return qs.filter(loan_application=loan_application)


class LoanApplicationDocumentRetrieveView(generics.RetrieveAPIView):
    """
    GET /documents/<document_uuid>/           → retrieve a single document
    """

    permission_classes = [permissions.IsAuthenticatedWithRole]
    serializer_class = LoanApplicationDocumentSerializer
    lookup_field = 'document_uuid'

    def get_queryset(self):
        user = self.request.user
        role = getattr(user, 'role', None)

        return get_role_based_queryset(user, LoanApplicationDocument, role)


class LoanApplicationDocumentUpdateView(generics.UpdateAPIView):
    """
    PUT   /documents/<document_uuid>/update/  → full update
    PATCH /documents/<document_uuid>/update/  → partial update
    """

    permission_classes = [permissions.IsApplicantOrPartner]
    serializer_class = LoanApplicationDocumentSerializer
    lookup_field = 'document_uuid'

    def get_queryset(self):
        user = self.request.user
        role = getattr(user, 'role', None)

        return get_role_based_queryset(user, LoanApplicationDocument, role)

    def perform_update(self, serializer):
        loan_application = serializer.instance.loan_application
        check_loan_application_terminal(loan_application)
        serializer.save()
