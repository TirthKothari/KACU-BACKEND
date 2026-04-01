from django.urls import path

from .views import UserProfileView


urlpatterns = [
    path("me/", UserProfileView.as_view(), name="get_update_user_profile"),
]
