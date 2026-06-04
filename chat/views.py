from rest_framework import generics
from rest_framework.pagination import CursorPagination
from django.db import transaction

from .models import ChatRoom, ChatMessage
from .utils import ChatRoomType
from .serializers import (
    ChatRoomSerializer,
    AnnouncementRoomCreateSerializer,
    ChatMessageSerializer,
    ChatMessageCreateSerializer,
)
from .helpers import (
    is_application_chat_participant,
    get_or_create_application_chat_room,
    get_loan_application_for_chat,
)
import api.permissions as permissions
from rest_framework.exceptions import PermissionDenied

import logging

logger = logging.getLogger(__name__)


# ─── Cursor Pagination for Chat Messages ──────────────────────────────────────


class ChatMessageCursorPagination(CursorPagination):
    """
    Cursor-based pagination for chat messages.
    Orders by created_at descending (newest first).
    """

    page_size = 50
    ordering = '-created_at'
    cursor_query_param = 'cursor'


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  ANNOUNCEMENT CHAT VIEWS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class AnnouncementRoomListView(generics.ListAPIView):
    """
    GET /announcements/    → list all announcement rooms

    Accessible by admins and agents.
    """

    permission_classes = [permissions.IsAdminOrAgent]
    serializer_class = ChatRoomSerializer

    def get_queryset(self):
        return ChatRoom.objects.filter(room_type=ChatRoomType.ANNOUNCEMENT.value).order_by('-created_at')


class AnnouncementRoomCreateView(generics.CreateAPIView):
    """
    POST /announcements/create/    → create an announcement room

    Only admins can create announcement rooms.
    """

    permission_classes = [permissions.IsAdmin]
    serializer_class = AnnouncementRoomCreateSerializer

    @transaction.atomic
    def perform_create(self, serializer):
        serializer.save(
            room_type=ChatRoomType.ANNOUNCEMENT.value,
            created_by=self.request.user,
        )


class AnnouncementRoomRetrieveView(generics.RetrieveAPIView):
    """
    GET /announcements/<uuid:chat_room_uuid>/    → retrieve an announcement room

    Accessible by admins and agents.
    """

    permission_classes = [permissions.IsAdminOrAgent]
    serializer_class = ChatRoomSerializer
    lookup_field = 'chat_room_uuid'

    def get_queryset(self):
        return ChatRoom.objects.filter(room_type=ChatRoomType.ANNOUNCEMENT.value)


class AnnouncementMessageListView(generics.ListAPIView):
    """
    GET /announcements/<uuid:chat_room_uuid>/messages/    → list messages in an announcement room

    Accessible by admins and agents. Uses cursor-based pagination.
    """

    permission_classes = [permissions.IsAdminOrAgent]
    serializer_class = ChatMessageSerializer
    pagination_class = ChatMessageCursorPagination

    def get_queryset(self):
        chat_room_uuid = self.kwargs.get('chat_room_uuid')
        return ChatMessage.objects.filter(
            chat_room__chat_room_uuid=chat_room_uuid,
            chat_room__room_type=ChatRoomType.ANNOUNCEMENT.value,
        )


class AnnouncementMessageCreateView(generics.CreateAPIView):
    """
    POST /announcements/<uuid:chat_room_uuid>/messages/create/    → send a message

    Only admins can send messages in announcement rooms.
    """

    permission_classes = [permissions.IsAdmin]
    serializer_class = ChatMessageCreateSerializer

    @transaction.atomic
    def perform_create(self, serializer):
        from django.shortcuts import get_object_or_404

        chat_room_uuid = self.kwargs.get('chat_room_uuid')
        chat_room = get_object_or_404(
            ChatRoom,
            chat_room_uuid=chat_room_uuid,
            room_type=ChatRoomType.ANNOUNCEMENT.value,
        )
        serializer.save(
            chat_room=chat_room,
            sender=self.request.user,
        )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  APPLICATION CHAT VIEWS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class ApplicationChatRoomRetrieveOrCreateView(generics.RetrieveAPIView):
    """
    GET /application/<uuid:loan_application_uuid>/    → get or create the chat room for an application

    Accessible by the applicant, partner, assigned agent, and admins.
    If the chat room doesn't exist yet, it is auto-created.
    """

    permission_classes = [permissions.IsAuthenticatedWithRole]
    serializer_class = ChatRoomSerializer

    def get_object(self):
        loan_application_uuid = self.kwargs.get('loan_application_uuid')
        user = self.request.user

        loan_application = get_loan_application_for_chat(loan_application_uuid, user)
        chat_room = get_or_create_application_chat_room(loan_application, user)
        return chat_room


class ApplicationChatMessageListView(generics.ListAPIView):
    """
    GET /application/<uuid:loan_application_uuid>/messages/    → list messages

    Uses cursor-based pagination. Only participants can view messages.
    """

    permission_classes = [permissions.IsAuthenticatedWithRole]
    serializer_class = ChatMessageSerializer
    pagination_class = ChatMessageCursorPagination

    def get_queryset(self):
        loan_application_uuid = self.kwargs.get('loan_application_uuid')
        user = self.request.user

        loan_application = get_loan_application_for_chat(loan_application_uuid, user)

        return ChatMessage.objects.filter(
            chat_room__loan_application=loan_application,
            chat_room__room_type=ChatRoomType.APPLICATION.value,
        )


class ApplicationChatMessageCreateView(generics.CreateAPIView):
    """
    POST /application/<uuid:loan_application_uuid>/messages/create/    → send a message

    Any participant (applicant, partner, assigned agent, admin) can send messages.
    """

    permission_classes = [permissions.IsAuthenticatedWithRole]
    serializer_class = ChatMessageCreateSerializer

    @transaction.atomic
    def perform_create(self, serializer):
        loan_application_uuid = self.kwargs.get('loan_application_uuid')
        user = self.request.user

        loan_application = get_loan_application_for_chat(loan_application_uuid, user)

        # Ensure participant check (already done inside get_loan_application_for_chat)
        if not is_application_chat_participant(user, loan_application):
            raise PermissionDenied("You are not a participant of this application chat.")

        chat_room = get_or_create_application_chat_room(loan_application, user)

        serializer.save(
            chat_room=chat_room,
            sender=user,
        )
