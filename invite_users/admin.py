from django.contrib import admin
from .models import InvitedUsers


@admin.register(InvitedUsers)
class InvitedUsersAdmin(admin.ModelAdmin):
    list_display = ('email', 'role', 'invited_by', 'expires_at', 'accepted_at', 'revoked_at', 'created_at')
    list_filter = ('role', 'accepted_at', 'revoked_at', 'created_at')
    search_fields = ('email', 'invited_by__email')
    readonly_fields = ('uuid', 'token_hash', 'created_at', 'updated_at')
