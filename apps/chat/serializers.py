from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Room, Message, RoomMember
from apps.users.serializers import UserMiniSerializer

User = get_user_model()


class MessageSerializer(serializers.ModelSerializer):
    sender = UserMiniSerializer(read_only=True)

    class Meta:
        model = Message
        fields = ('id', 'room', 'sender', 'content', 'created_at', 'updated_at', 'is_deleted')
        read_only_fields = ('id', 'room', 'sender', 'created_at', 'updated_at', 'is_deleted')


class RoomSerializer(serializers.ModelSerializer):
    members = UserMiniSerializer(many=True, read_only=True)
    last_message = MessageSerializer(read_only=True)
    member_count = serializers.SerializerMethodField()

    class Meta:
        model = Room
        fields = ('id', 'name', 'room_type', 'members', 'last_message', 'member_count', 'created_at', 'updated_at')
        read_only_fields = ('id', 'room_type', 'created_at', 'updated_at')

    def get_member_count(self, obj):
        return obj.members.count()


class CreateGroupRoomSerializer(serializers.ModelSerializer):
    member_ids = serializers.ListField(child=serializers.IntegerField(), write_only=True, required=False)

    class Meta:
        model = Room
        fields = ('name', 'member_ids')

    def create(self, validated_data):
        member_ids = validated_data.pop('member_ids', [])
        user = self.context['request'].user
        room = Room.objects.create(room_type='group', created_by=user, **validated_data)
        # Add creator as admin
        RoomMember.objects.create(room=room, user=user, is_admin=True)
        # Add other members
        for uid in member_ids:
            try:
                member = User.objects.get(id=uid)
                RoomMember.objects.get_or_create(room=room, user=member)
            except User.DoesNotExist:
                pass
        return room


class DMRoomSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()

    def validate_user_id(self, value):
        try:
            return User.objects.get(id=value)
        except User.DoesNotExist:
            raise serializers.ValidationError('User not found.')
