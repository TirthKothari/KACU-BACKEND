from django.conf import settings
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
import logging

from api.permissions import IsAdmin
from .models import InvitedUsers
from .serializers import (
    InviteAcceptSerializer,
    InviteCreateSerializer,
    InvitationListSerializer,
    InvitationValidationResponseSerializer,
)
from .helpers import send_invitation_email


logger = logging.getLogger(getattr(settings, 'LOGGER', __name__))


class CreateInvitationView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request):
        serializer = InviteCreateSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return Response(
                {
                    'success': False,
                    'message': 'Validation failed',
                    'errors': serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        invitation = serializer.save()

        frontend_base = getattr(settings, 'FRONTEND_INVITE_ACCEPT_URL', 'http://localhost:5173/invite/accept')
        invite_link = f"{frontend_base}?token={invitation.raw_token}"

        recipient_name = invitation.email.split('@')[0]
        inviter_name = f"{request.user.first_name} {request.user.last_name}".strip() or request.user.email
        business_name = getattr(settings, 'INVITE_BUSINESS_NAME', 'KACU')

        email_success, email_message = send_invitation_email(
            email=invitation.email,
            recipient_name=recipient_name,
            inviter_name=inviter_name,
            business_name=business_name,
            invite_link=invite_link,
            expires_at=invitation.expires_at.isoformat(),
            role=invitation.role,
        )

        if not email_success:
            logger.warning("Invitation email failed for %s: %s", invitation.email, email_message)

        response_data = {
            'uuid': str(invitation.uuid),
            'email': invitation.email,
            'role': invitation.role,
            'expires_at': invitation.expires_at,
            'email_sent': email_success,
            'email_status': email_message,
        }
        if getattr(settings, 'DEBUG', False):
            response_data['invite_link'] = invite_link

        return Response(
            {
                'success': True,
                'message': 'Invitation created successfully',
                'data': response_data,
            },
            status=status.HTTP_201_CREATED,
        )


class ValidateInvitationView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        token = request.query_params.get('token')
        if not token:
            return Response(
                {'success': False, 'message': 'Token is required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        token_hash = InvitedUsers.hash_token(token)
        invitation = InvitedUsers.objects.filter(token_hash=token_hash).first()

        if invitation is None:
            return Response(
                {'success': False, 'message': 'Invalid invitation token.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if invitation.accepted_at is not None:
            return Response(
                {'success': False, 'message': 'This invitation has already been used.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if invitation.revoked_at is not None:
            return Response(
                {'success': False, 'message': 'This invitation has been revoked.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if invitation.expires_at <= timezone.now():
            return Response(
                {'success': False, 'message': 'This invitation has expired.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = InvitationValidationResponseSerializer(invitation).data
        return Response(
            {
                'success': True,
                'message': 'Invitation is valid.',
                'data': data,
            },
            status=status.HTTP_200_OK,
        )


class AcceptInvitationView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = InviteAcceptSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return Response(
                {
                    'success': False,
                    'message': 'Validation failed',
                    'errors': serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        result = serializer.save()
        user = result['user']

        return Response(
            {
                'success': True,
                'message': 'User registered successfully through invitation.',
                'token': result['token'],
                'user': {
                    'user_id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'role': user.role,
                },
            },
            status=status.HTTP_201_CREATED,
        )


class InvitationListView(generics.ListAPIView):
    permission_classes = [IsAdmin]
    serializer_class = InvitationListSerializer

    def get_queryset(self):
        queryset = InvitedUsers.objects.select_related('invited_by').all().order_by('-created_at')
        status_filter = self.request.query_params.get('status')
        now = timezone.now()

        if status_filter == 'active':
            queryset = queryset.filter(accepted_at__isnull=True, revoked_at__isnull=True, expires_at__gt=now)
        elif status_filter == 'expired':
            queryset = queryset.filter(expires_at__lte=now, accepted_at__isnull=True, revoked_at__isnull=True)
        elif status_filter == 'accepted':
            queryset = queryset.filter(accepted_at__isnull=False)
        elif status_filter == 'revoked':
            queryset = queryset.filter(revoked_at__isnull=False)

        return queryset


class RevokeInvitationView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request, uuid):
        invitation = InvitedUsers.objects.filter(uuid=uuid).first()
        if invitation is None:
            return Response(
                {'success': False, 'message': 'Invitation not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if invitation.accepted_at is not None:
            return Response(
                {'success': False, 'message': 'Accepted invitation cannot be revoked.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if invitation.revoked_at is not None:
            return Response(
                {'success': True, 'message': 'Invitation is already revoked.'},
                status=status.HTTP_200_OK,
            )

        invitation.revoked_at = timezone.now()
        invitation.save(update_fields=['revoked_at', 'updated_at'])

        return Response(
            {'success': True, 'message': 'Invitation revoked successfully.'},
            status=status.HTTP_200_OK,
        )
