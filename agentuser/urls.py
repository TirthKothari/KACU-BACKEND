from django.urls import path

from .views import AgentUserDetailView, AgentUserListView


urlpatterns = [
    path("users/", AgentUserListView.as_view(), name="agentuser_user_list"),
    path("users/<int:id>/", AgentUserDetailView.as_view(), name="agentuser_user_detail"),
]
