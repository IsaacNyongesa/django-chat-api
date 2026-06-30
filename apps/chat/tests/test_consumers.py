import pytest
from channels.testing import WebsocketCommunicator
from channels.db import database_sync_to_async
from rest_framework_simplejwt.tokens import AccessToken
from config.asgi import application
from apps.users.factories import UserFactory
from apps.chat.models import Room, RoomMember

pytestmark = pytest.mark.django_db(transaction=True)

# Real browsers always send an Origin header on WebSocket upgrades, and
# AllowedHostsOriginValidator rejects connections without one. We replicate
# that here so tests exercise the same code path as production traffic.
ORIGIN_HEADERS = [(b'origin', b'http://localhost')]


@database_sync_to_async
def create_user_and_room():
    user = UserFactory()
    room = Room.objects.create(room_type='group', name='Live Chat')
    RoomMember.objects.create(room=room, user=user)
    token = str(AccessToken.for_user(user))
    return user, room, token


@pytest.mark.asyncio
async def test_authenticated_member_can_connect_and_send_message():
    user, room, token = await create_user_and_room()
    communicator = WebsocketCommunicator(
        application, f'/ws/chat/{room.id}/?token={token}', headers=ORIGIN_HEADERS
    )
    connected, subprotocol_or_close_code = await communicator.connect()
    assert connected, f"close code: {subprotocol_or_close_code}"

    await communicator.send_json_to({'type': 'send_message', 'content': 'Hi there'})
    response = await communicator.receive_json_from()

    assert response['type'] == 'new_message'
    assert response['message']['content'] == 'Hi there'
    await communicator.disconnect()


@pytest.mark.asyncio
async def test_unauthenticated_connection_is_rejected():
    room = await database_sync_to_async(Room.objects.create)(room_type='group', name='Locked')
    communicator = WebsocketCommunicator(application, f'/ws/chat/{room.id}/', headers=ORIGIN_HEADERS)
    connected, _ = await communicator.connect()
    assert connected is False


@pytest.mark.asyncio
async def test_non_member_connection_is_rejected():
    user, room, token = await create_user_and_room()
    other_room = await database_sync_to_async(Room.objects.create)(room_type='group', name='Other')
    communicator = WebsocketCommunicator(
        application, f'/ws/chat/{other_room.id}/?token={token}', headers=ORIGIN_HEADERS
    )
    connected, _ = await communicator.connect()
    assert connected is False
