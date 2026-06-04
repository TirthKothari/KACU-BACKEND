from django.urls import path
from .views import (
    AnnouncementRoomListView,
    AnnouncementRoomCreateView,
    AnnouncementRoomRetrieveView,
    AnnouncementMessageListView,
    AnnouncementMessageCreateView,
    ApplicationChatRoomRetrieveOrCreateView,
    ApplicationChatMessageListView,
    ApplicationChatMessageCreateView,
)

urlpatterns = [
    # ── Announcement Chat ────────────────────────────────────────────────────
    path('announcements/', AnnouncementRoomListView.as_view(), name='announcement-room-list'),
    path('announcements/create/', AnnouncementRoomCreateView.as_view(), name='announcement-room-create'),
    path('announcements/<uuid:chat_room_uuid>/', AnnouncementRoomRetrieveView.as_view(), name='announcement-room-retrieve'),
    path('announcements/<uuid:chat_room_uuid>/messages/', AnnouncementMessageListView.as_view(), name='announcement-message-list'),
    path('announcements/<uuid:chat_room_uuid>/messages/create/', AnnouncementMessageCreateView.as_view(), name='announcement-message-create'),
    # ── Application Chat ─────────────────────────────────────────────────────
    path('application/<uuid:loan_application_uuid>/', ApplicationChatRoomRetrieveOrCreateView.as_view(), name='application-chat-room'),
    path('application/<uuid:loan_application_uuid>/messages/', ApplicationChatMessageListView.as_view(), name='application-chat-message-list'),
    path('application/<uuid:loan_application_uuid>/messages/create/', ApplicationChatMessageCreateView.as_view(), name='application-chat-message-create'),
]
