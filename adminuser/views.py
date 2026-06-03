import logging
from rest_framework import generics, status, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from django.db.models import Sum, Count, Q

from api.permissions import IsAdmin
from applicant.models import User
from applicant.utils import UserRoleChoices
from loan_application.models import LoanApplication
from loan_application.utils import LoanApplicationStatus
from loan_type.models import LoanType
from .serializers import AdminUserListSerializer, AdminUserUpdateSerializer, AdminUserDetailSerializer

logger = logging.getLogger(__name__)


class AdminUserListView(generics.ListAPIView):
    """
    Admin-only endpoint to list users.
    Supports ?role=AGENT or ?role=APPLICANT.
    """

    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['username', 'first_name', 'last_name', 'assigned_agent__username', 'partner__username', 'assigned_agent__first_name', 'assigned_agent__last_name', 'partner__first_name', 'partner__last_name']
    ordering_fields = ['date_joined', 'role']
    ordering = ['-date_joined']
    serializer_class = AdminUserListSerializer
    permission_classes = [IsAdmin]

    def get_queryset(self):
        queryset = User.objects.all().order_by("-date_joined")
        role = self.request.query_params.get("role")

        if not role:
            return queryset

        normalized_role = role.strip().upper()
        allowed_roles = {UserRoleChoices.AGENT.value, UserRoleChoices.APPLICANT.value, UserRoleChoices.ADMIN.value, UserRoleChoices.PARTNER.value}
        if normalized_role not in allowed_roles:
            raise ValidationError({"role": "Invalid role filter. Allowed values: AGENT, APPLICANT, ADMIN, PARTNER."})

        return queryset.filter(role=normalized_role)


class AdminUserDetailView(generics.RetrieveUpdateAPIView):
    """
    Admin-only endpoint to retrieve and update a single user.
    """

    queryset = User.objects.select_related("assigned_agent", "partner").all()
    permission_classes = [IsAdmin]
    lookup_field = "id"

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return AdminUserUpdateSerializer
        return AdminUserDetailSerializer


class AdminDashboardView(APIView):
    """
    Admin-only endpoint to retrieve dashboard statistics.
    """

    permission_classes = [IsAdmin]

    def get(self, request, *args, **kwargs):
        try:
            # 1. Team Counts (Optimized: 1 query to fetch counts grouped by role)
            role_counts = User.objects.values('role').annotate(count=Count('id'))
            role_map = {item['role']: item['count'] for item in role_counts}

            clients_count = role_map.get(UserRoleChoices.APPLICANT.value, 0)
            agents_count = role_map.get(UserRoleChoices.AGENT.value, 0)
            partners_count = role_map.get(UserRoleChoices.PARTNER.value, 0)
            admins_count = role_map.get(UserRoleChoices.ADMIN.value, 0)

            # 2. Applications Status & Funds Counts (Optimized: 1 query using conditional aggregation)
            app_metrics = LoanApplication.objects.aggregate(total_count=Count('id'), needs_review_count=Count('id', filter=Q(status__in=[LoanApplicationStatus.SUBMITTED.value, LoanApplicationStatus.PENDING.value])), approved_count=Count('id', filter=Q(status=LoanApplicationStatus.APPROVED.value)), rejected_count=Count('id', filter=Q(status=LoanApplicationStatus.REJECTED.value)), referred_count=Count('id', filter=Q(user__partner__isnull=False)), approved_funds_sum=Sum('approved_funds', filter=Q(status=LoanApplicationStatus.APPROVED.value)))

            total_apps = app_metrics['total_count'] or 0
            needs_review_apps = app_metrics['needs_review_count'] or 0
            approved_apps = app_metrics['approved_count'] or 0
            rejected_apps = app_metrics['rejected_count'] or 0
            referred_apps = app_metrics['referred_count'] or 0
            total_funds_approved = float(app_metrics['approved_funds_sum'] or 0.0)

            # 3. Conversion Rate in Percent (Approved / Total * 100)
            conversion_rate = round((approved_apps / total_apps * 100), 2) if total_apps > 0 else 0.0

            # 5. Referral Rate in Percent (Referred Applications / Total Applications * 100)
            referral_rate = round((referred_apps / total_apps * 100), 2) if total_apps > 0 else 0.0

            # 6. Applications by Loan-Types Counts and Percentages (Optimized: 1 query fetching all types with count)
            loan_type_data = []
            loan_types = LoanType.objects.annotate(app_count=Count('loan_application_loan_type'))
            for lt in loan_types:
                lt_count = lt.app_count
                lt_percentage = round((lt_count / total_apps * 100), 2) if total_apps > 0 else 0.0
                loan_type_data.append({"id": lt.id, "name": lt.name, "count": lt_count, "percentage": lt_percentage})

            # Handle applications with unspecified/null loan type (Optimized: 1 query)
            unspecified_count = LoanApplication.objects.filter(loan_type__isnull=True).count()
            if unspecified_count > 0:
                unspecified_percentage = round((unspecified_count / total_apps * 100), 2) if total_apps > 0 else 0.0
                loan_type_data.append({"id": None, "name": "Unspecified", "count": unspecified_count, "percentage": unspecified_percentage})

            response_data = {"team": {"clients": clients_count, "agents": agents_count, "partners": partners_count, "admin": admins_count}, "applications": {"total": total_apps, "needs_review": needs_review_apps, "approved": approved_apps, "rejected": rejected_apps, "referred": referred_apps}, "conversion_rate_percent": conversion_rate, "total_funds_approved": total_funds_approved, "referral_rate_percent": referral_rate, "applications_by_loan_type": loan_type_data}

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.exception("Failed to retrieve admin dashboard statistics.")
            return Response({"error": "An unexpected error occurred while compiling dashboard metrics. Please check the logs."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
