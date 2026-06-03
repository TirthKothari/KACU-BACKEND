from django.urls import path

from .views import AdminUserDetailView, AdminUserListView, AdminDashboardView


urlpatterns = [
    path("users/", AdminUserListView.as_view(), name="adminuser_user_list"),
    path("users/<int:id>/", AdminUserDetailView.as_view(), name="adminuser_user_detail"),
    path("dashboard/", AdminDashboardView.as_view(), name="admin_dashboard"),
]
