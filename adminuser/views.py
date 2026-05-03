from rest_framework import generics
from rest_framework.exceptions import ValidationError

from api.permissions import IsAdmin
from applicant.models import User
from applicant.utils import UserRoleChoices
from .serializers import AdminUserListSerializer, AdminUserUpdateSerializer, AdminUserDetailSerializer
from rest_framework import filters


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
