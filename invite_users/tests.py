from django.test import TestCase
from django.utils import timezone
from datetime import timedelta

from applicant.models import User
from applicant.utils import UserRoleChoices
from .models import InvitedUsers
from .serializers import InviteAcceptSerializer


class InviteUsersModelTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username='admin_user',
            email='admin@example.com',
            password='AdminPass123!',
            first_name='Admin',
            last_name='User',
            phone='+12345678901',
            role=UserRoleChoices.ADMIN.value,
        )

    def test_issue_unique_token_creates_unique_hash(self):
        _, token_hash_1 = InvitedUsers.issue_unique_token()
        _, token_hash_2 = InvitedUsers.issue_unique_token()
        self.assertNotEqual(token_hash_1, token_hash_2)

    def test_create_invitation_revokes_previous_active(self):
        first, _ = InvitedUsers.create_invitation(
            email='agent@example.com',
            role=UserRoleChoices.AGENT.value,
            invited_by=self.admin,
            expiry_hours=48,
        )

        second, _ = InvitedUsers.create_invitation(
            email='agent@example.com',
            role=UserRoleChoices.AGENT.value,
            invited_by=self.admin,
            expiry_hours=48,
        )

        first.refresh_from_db()
        self.assertIsNotNone(first.revoked_at)
        self.assertIsNone(second.revoked_at)


class InviteAcceptSerializerTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username='admin_accept',
            email='admin_accept@example.com',
            password='AdminPass123!',
            first_name='Admin',
            last_name='Accept',
            phone='+12345678901',
            role=UserRoleChoices.ADMIN.value,
        )

    def test_accept_invite_creates_user_with_invited_role(self):
        invitation, raw_token = InvitedUsers.create_invitation(
            email='partner@example.com',
            role=UserRoleChoices.PARTNER.value,
            invited_by=self.admin,
            expiry_hours=48,
        )

        serializer = InviteAcceptSerializer(
            data={
                'token': raw_token,
                'username': 'partner_user',
                'email': 'partner@example.com',
                'phone': '+14165551234',
                'password': 'SecurePass123!',
                'first_name': 'Partner',
                'last_name': 'User',
            }
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        result = serializer.save()

        invitation.refresh_from_db()
        self.assertIsNotNone(invitation.accepted_at)
        self.assertEqual(result['user'].role, UserRoleChoices.PARTNER.value)

    def test_accept_invite_fails_for_expired_token(self):
        invitation, raw_token = InvitedUsers.create_invitation(
            email='agent_expired@example.com',
            role=UserRoleChoices.AGENT.value,
            invited_by=self.admin,
            expiry_hours=1,
        )
        invitation.expires_at = timezone.now() - timedelta(minutes=1)
        invitation.save(update_fields=['expires_at'])

        serializer = InviteAcceptSerializer(
            data={
                'token': raw_token,
                'username': 'agent_expired',
                'email': 'agent_expired@example.com',
                'phone': '+14165556789',
                'password': 'SecurePass123!',
                'first_name': 'Expired',
                'last_name': 'Agent',
            }
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn('token', serializer.errors)
