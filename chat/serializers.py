import os

from rest_framework import serializers
from .models import ChatRoom, ChatMessage


# ─── File validation constants ────────────────────────────────────────────────
ALLOWED_FILE_EXTENSIONS = ['.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png', '.gif', '.webp', '.csv', '.xlsx', '.xls', '.txt']
MAX_FILE_SIZE_MB = 50
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024


# ─── Chat Room Serializers ────────────────────────────────────────────────────


class ChatRoomSerializer(serializers.ModelSerializer):
    """Serializer for listing and retrieving chat rooms."""

    created_by_name = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    message_count = serializers.SerializerMethodField()

    class Meta:
        model = ChatRoom
        fields = [
            'id',
            'chat_room_uuid',
            'room_type',
            'name',
            'loan_application',
            'created_by',
            'created_by_name',
            'last_message',
            'message_count',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'chat_room_uuid',
            'room_type',
            'loan_application',
            'created_by',
            'created_by_name',
            'last_message',
            'message_count',
            'created_at',
            'updated_at',
        ]

    def get_created_by_name(self, obj):
        if obj.created_by:
            return obj.created_by.get_full_name() or obj.created_by.username
        return None

    def get_last_message(self, obj):
        last_msg = obj.messages.order_by('-created_at').first()
        if last_msg:
            return {
                'message_uuid': str(last_msg.message_uuid),
                'sender_name': last_msg.sender.get_full_name() or last_msg.sender.username,
                'content': last_msg.content[:100] if last_msg.content else '[file]',
                'created_at': last_msg.created_at.isoformat(),
            }
        return None

    def get_message_count(self, obj):
        return obj.messages.count()


class AnnouncementRoomCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating an announcement chat room (admin only)."""

    class Meta:
        model = ChatRoom
        fields = [
            'id',
            'chat_room_uuid',
            'room_type',
            'name',
            'created_by',
            'created_at',
        ]
        read_only_fields = ['id', 'chat_room_uuid', 'room_type', 'created_by', 'created_at']

    def validate_name(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Room name cannot be empty.")
        if len(value.strip()) > 255:
            raise serializers.ValidationError("Room name cannot exceed 255 characters.")
        return value.strip()


# ─── Chat Message Serializers ─────────────────────────────────────────────────


class ChatMessageSerializer(serializers.ModelSerializer):
    """Serializer for listing and retrieving chat messages."""

    sender_name = serializers.SerializerMethodField()
    sender_role = serializers.SerializerMethodField()

    class Meta:
        model = ChatMessage
        fields = [
            'id',
            'message_uuid',
            'chat_room',
            'sender',
            'sender_name',
            'sender_role',
            'content',
            'message_file',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'message_uuid',
            'chat_room',
            'sender',
            'sender_name',
            'sender_role',
            'created_at',
            'updated_at',
        ]

    def get_sender_name(self, obj):
        return obj.sender.get_full_name() or obj.sender.username

    def get_sender_role(self, obj):
        return getattr(obj.sender, 'role', None)


class ChatMessageCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a new chat message.
    At least one of content or message_file must be provided.
    File validation mirrors the LoanApplicationDocument pattern and files
    are stored in S3 via the default storage backend.
    """

    class Meta:
        model = ChatMessage
        fields = [
            'message_uuid',
            'content',
            'message_file',
            'created_at',
        ]
        read_only_fields = ['message_uuid', 'created_at']

    def validate_message_file(self, value):
        """Validate file size and extension (same pattern as LoanApplicationDocumentSerializer)."""
        if value is None:
            return value

        # Limit file size
        if value.size > MAX_FILE_SIZE_BYTES:
            raise serializers.ValidationError(f"File size must not exceed {MAX_FILE_SIZE_MB}MB.")

        # Validate file extension
        ext = os.path.splitext(value.name)[1].lower()
        if ext not in ALLOWED_FILE_EXTENSIONS:
            raise serializers.ValidationError(f"File type not supported. Allowed types: {', '.join(ALLOWED_FILE_EXTENSIONS)}")

        return value

    def validate(self, data):
        """Ensure at least one of content or message_file is provided."""
        content = data.get('content', '').strip()
        message_file = data.get('message_file')

        if not content and not message_file:
            raise serializers.ValidationError("A message must contain either text content or a file attachment (or both).")

        return data
