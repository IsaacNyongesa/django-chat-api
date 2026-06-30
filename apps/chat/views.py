from rest_framework import generics, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q
from django.contrib.auth import get_user_model
from .models import Room, Message, RoomMember
from .serializers import (
    RoomSerializer, CreateGroupRoomSerializer,
    MessageSerializer, DMRoomSerializer
)

User = get_user_model()


class RoomListCreateView(generics.ListCreateAPIView):
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreateGroupRoomSerializer
        return RoomSerializer

    def get_queryset(self):
        return Room.objects.filter(members=self.request.user).prefetch_related('members', 'messages')

    def perform_create(self, serializer):
        serializer.save()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        room = serializer.save()
        return Response(RoomSerializer(room).data, status=status.HTTP_201_CREATED)


class RoomDetailView(generics.RetrieveAPIView):
    serializer_class = RoomSerializer

    def get_queryset(self):
        return Room.objects.filter(members=self.request.user)


class JoinRoomView(APIView):
    def post(self, request, pk):
        try:
            room = Room.objects.get(pk=pk, room_type='group')
        except Room.DoesNotExist:
            return Response({'detail': 'Room not found.'}, status=404)
        RoomMember.objects.get_or_create(room=room, user=request.user)
        return Response({'detail': 'Joined room.'})


class LeaveRoomView(APIView):
    def post(self, request, pk):
        deleted, _ = RoomMember.objects.filter(room_id=pk, user=request.user).delete()
        if deleted:
            return Response({'detail': 'Left room.'})
        return Response({'detail': 'You are not a member.'}, status=400)


class DMRoomView(APIView):
    """Get or create a DM room between the current user and another user."""
    def post(self, request):
        serializer = DMRoomSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        other_user = serializer.validated_data['user_id']

        # Find existing DM room with exactly these two members
        user_rooms = Room.objects.filter(room_type='dm', members=request.user)
        dm_room = user_rooms.filter(members=other_user).first()

        if not dm_room:
            dm_room = Room.objects.create(room_type='dm', created_by=request.user)
            RoomMember.objects.create(room=dm_room, user=request.user)
            RoomMember.objects.create(room=dm_room, user=other_user)

        return Response(RoomSerializer(dm_room).data)


class MessageListCreateView(generics.ListCreateAPIView):
    serializer_class = MessageSerializer
    throttle_scope = 'messages'

    def get_queryset(self):
        room_id = self.kwargs['room_id']
        # Ensure user is a member
        if not Room.objects.filter(id=room_id, members=self.request.user).exists():
            return Message.objects.none()
        return Message.objects.filter(room_id=room_id, is_deleted=False).select_related('sender')

    def perform_create(self, serializer):
        room_id = self.kwargs['room_id']
        try:
            room = Room.objects.get(id=room_id, members=self.request.user)
        except Room.DoesNotExist:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('You are not a member of this room.')
        serializer.save(sender=self.request.user, room=room)


class MessageDeleteView(APIView):
    def delete(self, request, pk):
        try:
            message = Message.objects.get(pk=pk, sender=request.user)
        except Message.DoesNotExist:
            return Response({'detail': 'Message not found.'}, status=404)
        message.is_deleted = True
        message.content = '[deleted]'
        message.save()
        return Response(status=204)
