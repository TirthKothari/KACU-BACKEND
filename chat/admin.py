from django.contrib import admin
from .models import ChatRoom, ChatMessage


@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ('name', 'room_type', 'loan_application', 'created_by', 'created_at')
    list_filter = ('room_type', 'created_at')
    search_fields = ('name', 'chat_room_uuid', 'created_by__username', 'created_by__email')
    readonly_fields = ('chat_room_uuid', 'created_at', 'updated_at')
    ordering = ('-created_at',)


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'chat_room', 'content_preview', 'has_file', 'created_at')
    list_filter = ('chat_room__room_type', 'created_at')
    search_fields = ('content', 'sender__username', 'sender__email', 'message_uuid')
    readonly_fields = ('message_uuid', 'created_at', 'updated_at')
    ordering = ('-created_at',)

    def content_preview(self, obj):
        return obj.content[:80] if obj.content else '[file only]'

    content_preview.short_description = 'Content'

    def has_file(self, obj):
        return bool(obj.message_file)

    has_file.boolean = True
    has_file.short_description = 'File?'
