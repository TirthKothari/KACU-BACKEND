from django.urls import path
from . import views

urlpatterns = [
    path('prequalification/', views.CreatePrequalification.as_view(), name='create_prequalification'),
    path('register/', views.ApplicantUserRegistration.as_view(), name='user_registration'),
    path('login/', views.UserLoginView.as_view(), name='user_login'),
]
