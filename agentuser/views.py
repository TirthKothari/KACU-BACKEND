from rest_framework import generics, filters, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Count, Sum, Q
from applicant.models import User
from api.permissions import IsAgent
from applicant.utils import UserRoleChoices
from adminuser.serializers import AdminUserListSerializer, AdminUserDetailSerializer
from loan_application.models import LoanApplication
from loan_application.utils import LoanApplicationStatus
from loan_application.serializers import LoanApplicationSerializer


class AgentUserListView(generics.ListAPIView):
    """
    List all applicant users assigned to the currently logged-in agent.
    """

    serializer_class = AdminUserListSerializer
    permission_classes = [IsAgent]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['username', 'first_name', 'last_name', 'assigned_agent__username', 'partner__username', 'assigned_agent__first_name', 'assigned_agent__last_name', 'partner__first_name', 'partner__last_name']
    ordering_fields = ['date_joined', 'role']
    ordering = ['-date_joined']

    def get_queryset(self):
        return User.objects.filter(assigned_agent=self.request.user, role=UserRoleChoices.APPLICANT.value)


class AgentUserDetailView(generics.RetrieveAPIView):
    """
    Retrieve details of a specific applicant user assigned to the logged-in agent.
    """

    serializer_class = AdminUserDetailSerializer
    permission_classes = [IsAgent]
    lookup_field = 'id'

    def get_queryset(self):
        return User.objects.select_related("assigned_agent", "partner").filter(assigned_agent=self.request.user, role=UserRoleChoices.APPLICANT.value)


class AgentDashboardView(APIView):
    """
    Agent-only endpoint to retrieve dashboard statistics.
    """

    permission_classes = [IsAgent]

    def get(self, request, *args, **kwargs):
        try:
            # 1. Clients Assigned (assigned to current agent and applicant role)
            clients_assigned = User.objects.filter(assigned_agent=request.user, role=UserRoleChoices.APPLICANT.value).count()

            # 2. Applications Metrics (Total, Needs Review, Approved, Rejected, Referred, Approved Funds)
            # Scoped to applications of users assigned to the current agent.
            app_metrics = LoanApplication.objects.filter(user__assigned_agent=request.user).aggregate(total_count=Count('id'), needs_review_count=Count('id', filter=Q(status__in=[LoanApplicationStatus.SUBMITTED.value, LoanApplicationStatus.PENDING.value])), approved_count=Count('id', filter=Q(status=LoanApplicationStatus.APPROVED.value)), rejected_count=Count('id', filter=Q(status=LoanApplicationStatus.REJECTED.value)), referred_count=Count('id', filter=Q(user__partner__isnull=False)), approved_funds_sum=Sum('approved_funds', filter=Q(status=LoanApplicationStatus.APPROVED.value)))

            total_apps = app_metrics['total_count'] or 0
            needs_review_apps = app_metrics['needs_review_count'] or 0
            approved_apps = app_metrics['approved_count'] or 0
            rejected_apps = app_metrics['rejected_count'] or 0
            referred_apps = app_metrics['referred_count'] or 0
            total_funds_approved = float(app_metrics['approved_funds_sum'] or 0.0)

            # 3. Conversion Rate in Percent (Approved / Total * 100)
            conversion_rate = round((approved_apps / total_apps * 100), 2) if total_apps > 0 else 0.0

            # 4. Recent 5 Applications (In submitted or pending state)
            recent_apps = LoanApplication.objects.filter(user__assigned_agent=request.user, status__in=[LoanApplicationStatus.SUBMITTED.value, LoanApplicationStatus.PENDING.value]).select_related('user', 'loan_type').order_by('-created_at')[:5]
            recent_apps_serialized = LoanApplicationSerializer(recent_apps, many=True, context={'request': request}).data

            response_data = {"total_applications": total_apps, "clients_assigned": clients_assigned, "needs_review": needs_review_apps, "approved": approved_apps, "rejected": rejected_apps, "referred": referred_apps, "conversion_rate_percent": conversion_rate, "total_funds_approved": total_funds_approved, "recent_applications": recent_apps_serialized}

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.exception("Failed to retrieve agent dashboard statistics.")
            return Response({"error": "An unexpected error occurred while compiling dashboard metrics. Please check the logs."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
