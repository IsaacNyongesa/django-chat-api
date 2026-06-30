import pytest
from django.core import mail
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
from apps.users.factories import UserFactory
from apps.chat.models import Room, RoomMember, Message
from apps.notifications.models import Notification
from apps.notifications.tasks import notify_room_members

pytestmark = pytest.mark.django_db


class TestNotifyRoomMembersTask:
    def test_creates_in_app_notification_for_offline_members(self):
        sender = UserFactory()
        recipient = UserFactory(is_online=False, email_notifications=True)
        room = Room.objects.create(room_type='group', name='Team')
        RoomMember.objects.create(room=room, user=sender)
        RoomMember.objects.create(room=room, user=recipient)
        message = Message.objects.create(room=room, sender=sender, content='Hello team')

        notify_room_members(room.id, message.id, sender.id)

        notif = Notification.objects.get(recipient=recipient)
        assert notif.notif_type == 'new_message'
        assert 'Hello team' in notif.body

    def test_sends_email_to_offline_member_with_notifications_enabled(self):
        sender = UserFactory()
        recipient = UserFactory(is_online=False, email_notifications=True)
        room = Room.objects.create(room_type='group', name='Team')
        RoomMember.objects.create(room=room, user=sender)
        RoomMember.objects.create(room=room, user=recipient)
        message = Message.objects.create(room=room, sender=sender, content='Ping')

        notify_room_members(room.id, message.id, sender.id)

        assert len(mail.outbox) == 1
        assert recipient.email in mail.outbox[0].to

    def test_does_not_email_online_members(self):
        sender = UserFactory()
        recipient = UserFactory(is_online=True, email_notifications=True)
        room = Room.objects.create(room_type='group', name='Team')
        RoomMember.objects.create(room=room, user=sender)
        RoomMember.objects.create(room=room, user=recipient)
        message = Message.objects.create(room=room, sender=sender, content='Ping')

        notify_room_members(room.id, message.id, sender.id)

        assert len(mail.outbox) == 0
        assert Notification.objects.filter(recipient=recipient).exists()  # in-app still created

    def test_respects_email_notification_preference(self):
        sender = UserFactory()
        recipient = UserFactory(is_online=False, email_notifications=False)
        room = Room.objects.create(room_type='group', name='Team')
        RoomMember.objects.create(room=room, user=sender)
        RoomMember.objects.create(room=room, user=recipient)
        message = Message.objects.create(room=room, sender=sender, content='Ping')

        notify_room_members(room.id, message.id, sender.id)

        assert len(mail.outbox) == 0

    def test_sender_does_not_notify_self(self):
        sender = UserFactory()
        room = Room.objects.create(room_type='group', name='Solo')
        RoomMember.objects.create(room=room, user=sender)
        message = Message.objects.create(room=room, sender=sender, content='Just me')

        notify_room_members(room.id, message.id, sender.id)

        assert Notification.objects.filter(recipient=sender).count() == 0


class TestNotificationEndpoints:
    def test_list_only_returns_own_notifications(self):
        user = UserFactory()
        other = UserFactory()
        Notification.objects.create(recipient=user, title='Mine', body='x')
        Notification.objects.create(recipient=other, title='Not mine', body='x')

        client = APIClient()
        client.force_authenticate(user=user)
        response = client.get(reverse('notification_list'))

        titles = [n['title'] for n in response.data['results']]
        assert 'Mine' in titles
        assert 'Not mine' not in titles

    def test_mark_read(self):
        user = UserFactory()
        notif = Notification.objects.create(recipient=user, title='Read me', body='x')
        client = APIClient()
        client.force_authenticate(user=user)

        response = client.post(reverse('notification_mark_read', args=[notif.id]))
        notif.refresh_from_db()

        assert response.status_code == status.HTTP_200_OK
        assert notif.is_read is True

    def test_unread_count(self):
        user = UserFactory()
        Notification.objects.create(recipient=user, title='A', body='x', is_read=False)
        Notification.objects.create(recipient=user, title='B', body='x', is_read=True)
        client = APIClient()
        client.force_authenticate(user=user)

        response = client.get(reverse('notification_unread_count'))
        assert response.data['unread_count'] == 1
