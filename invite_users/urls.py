from django.urls import path

from .views import (
    AcceptInvitationView,
    CreateInvitationView,
    InvitationListView,
    RevokeInvitationView,
    ValidateInvitationView,
)


urlpatterns = [
    path('create/', CreateInvitationView.as_view(), name='create_invitation'),
    path('validate/', ValidateInvitationView.as_view(), name='validate_invitation'),
    path('accept/', AcceptInvitationView.as_view(), name='accept_invitation'),
    path('list/', InvitationListView.as_view(), name='list_invitations'),
    path('revoke/<uuid:uuid>/', RevokeInvitationView.as_view(), name='revoke_invitation'),
]
