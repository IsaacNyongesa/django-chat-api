from django.urls import path
from .views import (
    RoomListCreateView, RoomDetailView,
    JoinRoomView, LeaveRoomView, DMRoomView,
    MessageListCreateView, MessageDeleteView,
)

urlpatterns = [
    path('rooms/', RoomListCreateView.as_view(), name='room_list_create'),
    path('rooms/<int:pk>/', RoomDetailView.as_view(), name='room_detail'),
    path('rooms/<int:pk>/join/', JoinRoomView.as_view(), name='room_join'),
    path('rooms/<int:pk>/leave/', LeaveRoomView.as_view(), name='room_leave'),
    path('rooms/dm/', DMRoomView.as_view(), name='room_dm'),
    path('rooms/<int:room_id>/messages/', MessageListCreateView.as_view(), name='message_list_create'),
    path('messages/<int:pk>/', MessageDeleteView.as_view(), name='message_delete'),
]
