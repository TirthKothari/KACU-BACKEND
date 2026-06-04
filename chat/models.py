import uuid
from django.db import models
from applicant.models import User
from loan_application.models import LoanApplication
from .utils import ChatRoomType


class ChatRoom(models.Model):
    """
    A chat room / channel.

    Two types:
      - ANNOUNCEMENT: Global broadcast room. Admins send, admins + agents read.
      - APPLICATION:  Scoped to a single LoanApplication. Applicant, partner,
                      assigned agent, and admins can send and read.
    """

    chat_room_uuid = models.UUIDField(unique=True, default=uuid.uuid4)
    room_type = models.CharField(
        max_length=50,
        choices=ChatRoomType.choices(),
        default=ChatRoomType.ANNOUNCEMENT.value,
    )
    name = models.CharField(max_length=255)
    loan_application = models.OneToOneField(
        LoanApplication,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='chat_room',
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='chat_rooms_created',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.room_type}] {self.name}"


class ChatMessage(models.Model):
    """
    A single message inside a ChatRoom.
    Supports text content and an optional file attachment stored in S3.
    """

    message_uuid = models.UUIDField(unique=True, default=uuid.uuid4)
    chat_room = models.ForeignKey(
        ChatRoom,
        on_delete=models.CASCADE,
        related_name='messages',
    )
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='chat_messages_sent',
    )
    content = models.TextField(blank=True, default='')
    message_file = models.FileField(
        upload_to='chat_files/',
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        preview = self.content[:50] if self.content else '[file]'
        return f"{self.sender.get_full_name()} – {preview}"
