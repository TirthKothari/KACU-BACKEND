from django.urls import path
from .views import (
    LoanApplicationCreateView,
    LoanApplicationListView,
    LoanApplicationRetrieveView,
    LoanApplicationCurrentStepView,
    LoanApplicationDecisionUpdateView,
    BusinessInformationCreateView,
    BusinessInformationRetrieveView,
    BusinessInformationUpdateView,
    BusinessFundingInformationCreateView,
    BusinessFundingInformationRetrieveView,
    BusinessFundingInformationUpdateView,
    BusinessOwnerInformationCreateView,
    BusinessOwnerInformationListView,
    BusinessOwnerInformationRetrieveView,
    BusinessOwnerInformationUpdateView,
    TermsAndConditionsCreateView,
    TermsAndConditionsRetrieveView,
    # TermsAndConditionsUpdateView,
    LoanApplicationDocumentCreateView,
    LoanApplicationDocumentListView,
    LoanApplicationDocumentRetrieveView,
    LoanApplicationDocumentUpdateView,
)

urlpatterns = [
    # ── Loan Application ──────────────────────────────────────────────────────
    path('', LoanApplicationListView.as_view(), name='loan-application-list'),
    path('create/', LoanApplicationCreateView.as_view(), name='loan-application-create'),
    path('<uuid:loan_application_uuid>/', LoanApplicationRetrieveView.as_view(), name='loan-application-retrieve'),
    path('<uuid:loan_application_uuid>/current-step/', LoanApplicationCurrentStepView.as_view(), name='loan-application-current-step'),
    path('<uuid:loan_application_uuid>/decision/', LoanApplicationDecisionUpdateView.as_view(), name='loan-application-decision-update'),
    # ── Nested routes (list sub-resources by loan application) ───────────────
    path('<uuid:loan_application_uuid>/owners/', BusinessOwnerInformationListView.as_view(), name='owner-information-list'),
    path('<uuid:loan_application_uuid>/documents/', LoanApplicationDocumentListView.as_view(), name='document-list'),
    # ── Business Information ──────────────────────────────────────────────────
    path('business-information/create/', BusinessInformationCreateView.as_view(), name='business-information-create'),
    path('business-information/<uuid:loan_application_uuid>/', BusinessInformationRetrieveView.as_view(), name='business-information-retrieve'),
    path('business-information/<uuid:loan_application_uuid>/update/', BusinessInformationUpdateView.as_view(), name='business-information-update'),
    # ── Business Funding Information ──────────────────────────────────────────
    path('funding-information/create/', BusinessFundingInformationCreateView.as_view(), name='funding-information-create'),
    path('funding-information/<uuid:loan_application_uuid>/', BusinessFundingInformationRetrieveView.as_view(), name='funding-information-retrieve'),
    path('funding-information/<uuid:loan_application_uuid>/update/', BusinessFundingInformationUpdateView.as_view(), name='funding-information-update'),
    # ── Business Owner Information ────────────────────────────────────────────
    path('owner-information/create/', BusinessOwnerInformationCreateView.as_view(), name='owner-information-create'),
    path('owner-information/<uuid:owner_uuid>/', BusinessOwnerInformationRetrieveView.as_view(), name='owner-information-retrieve'),
    path('owner-information/<uuid:owner_uuid>/update/', BusinessOwnerInformationUpdateView.as_view(), name='owner-information-update'),
    # ── Terms and Conditions ──────────────────────────────────────────────────
    path('terms-and-conditions/create/', TermsAndConditionsCreateView.as_view(), name='terms-and-conditions-create'),
    path('terms-and-conditions/<uuid:loan_application_uuid>/', TermsAndConditionsRetrieveView.as_view(), name='terms-and-conditions-retrieve'),
    # path('terms-and-conditions/<uuid:loan_application_uuid>/update/', TermsAndConditionsUpdateView.as_view(), name='terms-and-conditions-update'),
    # ── Documents ─────────────────────────────────────────────────────────────
    path('documents/create/', LoanApplicationDocumentCreateView.as_view(), name='document-create'),
    path('documents/<uuid:document_uuid>/', LoanApplicationDocumentRetrieveView.as_view(), name='document-retrieve'),
    path('documents/<uuid:document_uuid>/update/', LoanApplicationDocumentUpdateView.as_view(), name='document-update'),
]
