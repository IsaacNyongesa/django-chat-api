from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Room(models.Model):
    ROOM_TYPES = (
        ('dm', 'Direct Message'),
        ('group', 'Group'),
    )

    name = models.CharField(max_length=150, blank=True)  # blank for DMs
    room_type = models.CharField(max_length=10, choices=ROOM_TYPES, default='group')
    members = models.ManyToManyField(User, through='RoomMember', related_name='rooms')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_rooms')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return self.name or f'DM Room {self.id}'

    @property
    def last_message(self):
        return self.messages.order_by('-created_at').first()


class RoomMember(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='memberships')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='memberships')
    joined_at = models.DateTimeField(auto_now_add=True)
    is_admin = models.BooleanField(default=False)

    class Meta:
        unique_together = ('room', 'user')


class Message(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'{self.sender.username}: {self.content[:50]}'
