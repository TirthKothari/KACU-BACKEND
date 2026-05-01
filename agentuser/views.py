from rest_framework import generics, filters
from applicant.models import User
from api.permissions import IsAgent
from applicant.utils import UserRoleChoices
from adminuser.serializers import AdminUserListSerializer


class AgentUserListView(generics.ListAPIView):
    """
    List all applicant users assigned to the currently logged-in agent.
    """

    serializer_class = AdminUserListSerializer
    permission_classes = [IsAgent]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['username', 'first_name', 'last_name', 'email']
    ordering_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']

    def get_queryset(self):
        return User.objects.select_related("assigned_agent", "partner").filter(assigned_agent=self.request.user, role=UserRoleChoices.APPLICANT.value)


class AgentUserDetailView(generics.RetrieveAPIView):
    """
    Retrieve details of a specific applicant user assigned to the logged-in agent.
    """

    serializer_class = AdminUserListSerializer
    permission_classes = [IsAgent]
    lookup_field = 'id'

    def get_queryset(self):
        return User.objects.select_related("assigned_agent", "partner").filter(assigned_agent=self.request.user, role=UserRoleChoices.APPLICANT.value)
