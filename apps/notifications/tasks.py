from celery import shared_task
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

User = get_user_model()


@shared_task
def notify_room_members(room_id, message_id, sender_id):
    """
    Create in-app notifications for all room members (except sender)
    and send email to offline members who have email notifications enabled.
    """
    from apps.chat.models import Room, Message
    from apps.notifications.models import Notification

    try:
        message = Message.objects.select_related('sender', 'room').get(id=message_id)
    except Message.DoesNotExist:
        return

    room = message.room
    sender = message.sender
    members = room.members.exclude(id=sender_id)

    channel_layer = get_channel_layer()

    for member in members:
        # Create in-app notification
        notif = Notification.objects.create(
            recipient=member,
            notif_type='new_message',
            title=f'New message from {sender.username}',
            body=message.content[:200],
            room_id=room_id,
            message_id=message_id,
        )

        # Push real-time notification over WebSocket if member is connected
        unread_count = Notification.objects.filter(recipient=member, is_read=False).count()
        async_to_sync(channel_layer.group_send)(
            f'chat_{room_id}',
            {
                'type': 'push_notification',
                'notification': {
                    'id': notif.id,
                    'title': notif.title,
                    'body': notif.body,
                    'room_id': room_id,
                    'unread_count': unread_count,
                    'created_at': notif.created_at.isoformat(),
                }
            }
        )

        # Send email if member is offline and has email notifications on
        if not member.is_online and member.email_notifications and member.email:
            room_label = room.name or f'your conversation with {sender.username}'
            send_mail(
                subject=f'New message in {room_label}',
                message=(
                    f'Hi {member.username},\n\n'
                    f'{sender.username} sent a message:\n\n'
                    f'"{message.content[:300]}"\n\n'
                    f'Reply here: {settings.FRONTEND_URL}/rooms/{room_id}\n\n'
                    f'— The Chat Team'
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[member.email],
                fail_silently=True,
            )
