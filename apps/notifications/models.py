from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Notification(models.Model):
    NOTIF_TYPES = (
        ('new_message', 'New Message'),
        ('room_invite', 'Room Invite'),
        ('mention', 'Mention'),
    )

    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notif_type = models.CharField(max_length=20, choices=NOTIF_TYPES, default='new_message')
    title = models.CharField(max_length=255)
    body = models.TextField()
    is_read = models.BooleanField(default=False)
    # Optional reference fields
    room_id = models.IntegerField(null=True, blank=True)
    message_id = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Notif for {self.recipient.username}: {self.title}'
