from django.urls import path

from .views import AgentUserDetailView, AgentUserListView, AgentDashboardView


urlpatterns = [
    path("users/", AgentUserListView.as_view(), name="agentuser_user_list"),
    path("users/<int:id>/", AgentUserDetailView.as_view(), name="agentuser_user_detail"),
    path("dashboard/", AgentDashboardView.as_view(), name="agent_dashboard"),
]
