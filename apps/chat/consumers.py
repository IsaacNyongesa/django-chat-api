import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from .models import Room, Message
from apps.notifications.tasks import notify_room_members


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'chat_{self.room_id}'

        # Reject unauthenticated or non-member connections
        if not self.user.is_authenticated:
            await self.close()
            return

        is_member = await self.check_membership()
        if not is_member:
            await self.close()
            return

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.mark_online(True)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        if hasattr(self, 'user') and self.user.is_authenticated:
            await self.mark_online(False)

    async def receive(self, text_data):
        data = json.loads(text_data)
        msg_type = data.get('type')

        if msg_type == 'send_message':
            content = data.get('content', '').strip()
            if content:
                message = await self.save_message(content)
                msg_data = await self.serialize_message(message)
                # Broadcast to room
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {'type': 'chat_message', 'message': msg_data}
                )
                # .delay() (and especially its eager-mode execution in tests/dev)
                # does synchronous ORM work, which Django forbids calling
                # directly from an async context — route it through a thread.
                await self.dispatch_notifications(message.id)

        elif msg_type == 'typing':
            is_typing = data.get('is_typing', False)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_typing',
                    'user_id': self.user.id,
                    'username': self.user.username,
                    'is_typing': is_typing,
                }
            )

    # --- Handlers for group_send events ---

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'new_message',
            'message': event['message'],
        }))

    async def user_typing(self, event):
        if event['user_id'] != self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'user_typing',
                'user_id': event['user_id'],
                'username': event['username'],
                'is_typing': event['is_typing'],
            }))

    async def push_notification(self, event):
        """Receive a notification pushed by the server and forward to client."""
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'notification': event['notification'],
        }))

    # --- DB helpers ---

    @database_sync_to_async
    def dispatch_notifications(self, message_id):
        notify_room_members.delay(self.room_id, message_id, self.user.id)

    @database_sync_to_async
    def check_membership(self):
        return Room.objects.filter(id=self.room_id, members=self.user).exists()

    @database_sync_to_async
    def save_message(self, content):
        room = Room.objects.get(id=self.room_id)
        room.updated_at = timezone.now()
        room.save(update_fields=['updated_at'])
        return Message.objects.create(room=room, sender=self.user, content=content)

    @database_sync_to_async
    def serialize_message(self, message):
        return {
            'id': message.id,
            'content': message.content,
            'created_at': message.created_at.isoformat(),
            'sender': {
                'id': self.user.id,
                'username': self.user.username,
                'avatar': self.user.avatar,
            }
        }

    @database_sync_to_async
    def mark_online(self, is_online):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        User.objects.filter(id=self.user.id).update(
            is_online=is_online,
            last_seen=timezone.now() if not is_online else None,
        )
