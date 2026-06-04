from django.urls import path
from . import views

urlpatterns = [
    path('prequalification/create/', views.CreatePrequalification.as_view(), name='create_prequalification'),
    path('prequalification/send-registration-email/', views.SendRegistrationEmail.as_view(), name='send_registration_email'),
    path('prequalification/<uuid:uuid>/', views.GetPrequalification.as_view(), name='get_prequalification'),
    path('prequalification/', views.RetrieveUserPrequalification.as_view(), name='retrieve_user_prequalification'),
    path('prequalification/<uuid:uuid>/update/', views.UpdatePrequalification.as_view(), name='update_prequalification'),
    path('register/', views.ApplicantUserRegistration.as_view(), name='user_registration'),
    path('login/', views.UserLoginView.as_view(), name='user_login'),
]
