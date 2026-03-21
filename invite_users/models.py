from django.db import models
from applicant.models import User
import uuid
from applicant.utils import UserRoleChoices
from django.utils import timezone
from datetime import timedelta
import secrets
import hashlib


INVITABLE_ROLES = [
    UserRoleChoices.ADMIN.value,
    UserRoleChoices.AGENT.value,
    UserRoleChoices.PARTNER.value,
]


class InvitedUsers(models.Model):
    uuid = models.UUIDField(unique=True, default=uuid.uuid4)
    email = models.EmailField(db_index=True)
    role = models.CharField(max_length=50, choices=UserRoleChoices.invitable_roles())
    token_hash = models.CharField(max_length=64, unique=True)
    expires_at = models.DateTimeField()
    accepted_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    invited_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='sent_invitations')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email', 'role']),
            models.Index(fields=['expires_at']),
        ]

    @staticmethod
    def hash_token(raw_token):
        return hashlib.sha256(raw_token.encode('utf-8')).hexdigest()

    @property
    def is_expired(self):
        return timezone.now() >= self.expires_at

    @property
    def is_active(self):
        return self.accepted_at is None and self.revoked_at is None and not self.is_expired

    @classmethod
    def issue_unique_token(cls):
        # Regenerate if a collision ever happens with the unique token hash.
        while True:
            raw_token = secrets.token_urlsafe(48)
            token_hash = cls.hash_token(raw_token)
            if not cls.objects.filter(token_hash=token_hash).exists():
                return raw_token, token_hash

    @classmethod
    def create_invitation(cls, email, role, invited_by, expiry_hours=48):
        now = timezone.now()

        cls.objects.filter(
            email__iexact=email,
            role=role,
            accepted_at__isnull=True,
            revoked_at__isnull=True,
            expires_at__gt=now,
        ).update(revoked_at=now)

        raw_token, token_hash = cls.issue_unique_token()
        invitation = cls.objects.create(
            email=email,
            role=role,
            token_hash=token_hash,
            expires_at=now + timedelta(hours=expiry_hours),
            invited_by=invited_by,
        )
        return invitation, raw_token

    def __str__(self):
        return f"{self.email} ({self.role})"
