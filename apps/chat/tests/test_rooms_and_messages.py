import pytest
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
from apps.users.factories import UserFactory
from apps.chat.models import Room, RoomMember, Message

pytestmark = pytest.mark.django_db


@pytest.fixture
def auth_client():
    user = UserFactory()
    client = APIClient()
    client.force_authenticate(user=user)
    return client, user


class TestGroupRooms:
    def test_create_group_room(self, auth_client):
        client, user = auth_client
        other = UserFactory()
        response = client.post(reverse('room_list_create'), {
            'name': 'Engineering', 'member_ids': [other.id],
        }, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        room = Room.objects.get(id=response.data['id'])
        assert room.members.count() == 2
        assert RoomMember.objects.get(room=room, user=user).is_admin is True

    def test_list_only_returns_rooms_user_belongs_to(self, auth_client):
        client, user = auth_client
        my_room = Room.objects.create(room_type='group', name='Mine', created_by=user)
        RoomMember.objects.create(room=my_room, user=user)
        other_user = UserFactory()
        other_room = Room.objects.create(room_type='group', name='NotMine', created_by=other_user)
        RoomMember.objects.create(room=other_room, user=other_user)

        response = client.get(reverse('room_list_create'))
        ids = [r['id'] for r in response.data['results']]
        assert my_room.id in ids
        assert other_room.id not in ids

    def test_join_and_leave_room(self, auth_client):
        client, user = auth_client
        room = Room.objects.create(room_type='group', name='Open Room')
        join_resp = client.post(reverse('room_join', args=[room.id]))
        assert join_resp.status_code == status.HTTP_200_OK
        assert RoomMember.objects.filter(room=room, user=user).exists()

        leave_resp = client.post(reverse('room_leave', args=[room.id]))
        assert leave_resp.status_code == status.HTTP_200_OK
        assert not RoomMember.objects.filter(room=room, user=user).exists()


class TestDMRooms:
    def test_dm_room_is_reused_not_duplicated(self, auth_client):
        client, user = auth_client
        other = UserFactory()

        first = client.post(reverse('room_dm'), {'user_id': other.id}, format='json')
        second = client.post(reverse('room_dm'), {'user_id': other.id}, format='json')

        assert first.data['id'] == second.data['id']
        assert Room.objects.filter(room_type='dm').count() == 1

    def test_dm_with_nonexistent_user_fails(self, auth_client):
        client, user = auth_client
        response = client.post(reverse('room_dm'), {'user_id': 999999}, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestMessages:
    def test_member_can_send_message(self, auth_client):
        client, user = auth_client
        room = Room.objects.create(room_type='group', name='Chat')
        RoomMember.objects.create(room=room, user=user)

        response = client.post(reverse('message_list_create', args=[room.id]), {
            'content': 'Hello world',
        }, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert Message.objects.filter(room=room, sender=user, content='Hello world').exists()

    def test_non_member_cannot_send_message(self, auth_client):
        client, user = auth_client
        room = Room.objects.create(room_type='group', name='Private')
        response = client.post(reverse('message_list_create', args=[room.id]), {
            'content': 'Sneaky',
        }, format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_deleted_message_is_soft_deleted(self, auth_client):
        client, user = auth_client
        room = Room.objects.create(room_type='group', name='Chat')
        RoomMember.objects.create(room=room, user=user)
        message = Message.objects.create(room=room, sender=user, content='Oops')

        response = client.delete(reverse('message_delete', args=[message.id]))
        message.refresh_from_db()

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert message.is_deleted is True
        assert message.content == '[deleted]'

    def test_cannot_delete_others_message(self, auth_client):
        client, user = auth_client
        other = UserFactory()
        room = Room.objects.create(room_type='group', name='Chat')
        RoomMember.objects.create(room=room, user=user)
        message = Message.objects.create(room=room, sender=other, content='Not yours')

        response = client.delete(reverse('message_delete', args=[message.id]))
        assert response.status_code == status.HTTP_404_NOT_FOUND
