from django.contrib.auth.password_validation import validate_password
from django.conf import settings
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers
from rest_framework.authtoken.models import Token
import re

from applicant.models import User
from .models import InvitedUsers, INVITABLE_ROLES


class InviteCreateSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    role = serializers.ChoiceField(choices=INVITABLE_ROLES, required=True)

    def validate(self, attrs):
        email = attrs['email'].lower().strip()
        role = attrs['role']

        if User.objects.filter(email__iexact=email, role=role).exists():
            raise serializers.ValidationError({'email': 'A user with this email and role already exists.'})

        attrs['email'] = email
        return attrs

    def create(self, validated_data):
        invited_by = self.context['request'].user
        expiry_hours = getattr(settings, 'INVITE_LINK_EXPIRY_HOURS', 48)
        invitation, raw_token = InvitedUsers.create_invitation(
            email=validated_data['email'],
            role=validated_data['role'],
            invited_by=invited_by,
            expiry_hours=expiry_hours,
        )
        invitation.raw_token = raw_token
        return invitation


class InvitationListSerializer(serializers.ModelSerializer):
    invited_by_email = serializers.CharField(source='invited_by.email', read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)

    class Meta:
        model = InvitedUsers
        fields = [
            'uuid',
            'email',
            'role',
            'invited_by_email',
            'expires_at',
            'accepted_at',
            'revoked_at',
            'created_at',
            'is_expired',
            'is_active',
        ]


class InviteValidateSerializer(serializers.Serializer):
    token = serializers.CharField(required=True)


class InviteAcceptSerializer(serializers.Serializer):
    token = serializers.CharField(required=True)
    username = serializers.CharField(required=True, max_length=150)
    email = serializers.EmailField(required=True)
    phone = serializers.CharField(required=True, max_length=20)
    password = serializers.CharField(required=True, write_only=True, min_length=8)
    first_name = serializers.CharField(required=True, max_length=150)
    last_name = serializers.CharField(required=True, max_length=150)

    def validate_password(self, value):
        try:
            validate_password(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages))
        return value

    def validate_username(self, value):
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError('A user with this username already exists.')
        return value

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError('A user with this email already exists.')
        return value.lower().strip()

    def validate_phone(self, value):
        if not re.match(r"^\+?1?\d{9,15}$", value):
            raise serializers.ValidationError("Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")
        return value

    def validate(self, attrs):
        token_hash = InvitedUsers.hash_token(attrs['token'])
        invitation = InvitedUsers.objects.filter(token_hash=token_hash).select_related('invited_by').first()

        if invitation is None:
            raise serializers.ValidationError({'token': 'Invalid invitation token.'})

        if invitation.accepted_at is not None:
            raise serializers.ValidationError({'token': 'This invitation has already been used.'})

        if invitation.revoked_at is not None:
            raise serializers.ValidationError({'token': 'This invitation has been revoked.'})

        if invitation.expires_at <= timezone.now():
            raise serializers.ValidationError({'token': 'This invitation has expired.'})

        if invitation.email.lower() != attrs['email'].lower().strip():
            raise serializers.ValidationError({'email': 'This email does not match the invitation.'})

        attrs['invitation'] = invitation
        return attrs

    def create(self, validated_data):
        invitation = validated_data['invitation']

        with transaction.atomic():
            user = User.objects.create_user(
                username=validated_data['username'],
                email=validated_data['email'],
                password=validated_data['password'],
                first_name=validated_data['first_name'],
                last_name=validated_data['last_name'],
                role=invitation.role,
                is_qualified=False,
                phone=validated_data['phone'],
            )

            invitation.accepted_at = timezone.now()
            invitation.save(update_fields=['accepted_at', 'updated_at'])

            Token.objects.filter(user=user).delete()
            token = Token.objects.create(user=user)

        return {
            'user': user,
            'token': token.key,
            'invitation': invitation,
        }


class InvitationValidationResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvitedUsers
        fields = ['email', 'role', 'expires_at', 'accepted_at', 'revoked_at']
