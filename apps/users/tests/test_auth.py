import pytest
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
from apps.users.factories import UserFactory

pytestmark = pytest.mark.django_db


class TestRegistration:
    def test_register_creates_user_and_returns_tokens(self):
        client = APIClient()
        url = reverse('register')
        payload = {
            'email': 'newuser@example.com',
            'username': 'newuser',
            'password': 'StrongPass123!',
        }
        response = client.post(url, payload, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert 'access' in response.data
        assert 'refresh' in response.data
        assert response.data['user']['email'] == 'newuser@example.com'

    def test_register_rejects_duplicate_email(self):
        UserFactory(email='taken@example.com')
        client = APIClient()
        response = client.post(reverse('register'), {
            'email': 'taken@example.com', 'username': 'someone', 'password': 'StrongPass123!',
        }, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['error']['code'] == 'validation_error'

    def test_register_rejects_short_password(self):
        client = APIClient()
        response = client.post(reverse('register'), {
            'email': 'a@example.com', 'username': 'a', 'password': 'short',
        }, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestLogin:
    def test_login_with_valid_credentials_returns_tokens(self):
        user = UserFactory(email='login@example.com')
        client = APIClient()
        response = client.post(reverse('login'), {
            'email': 'login@example.com', 'password': 'TestPass123!',
        }, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data

    def test_login_with_wrong_password_fails(self):
        UserFactory(email='login2@example.com')
        client = APIClient()
        response = client.post(reverse('login'), {
            'email': 'login2@example.com', 'password': 'WrongPassword!',
        }, format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestMe:
    def test_unauthenticated_request_is_rejected(self):
        client = APIClient()
        response = client.get(reverse('me'))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_authenticated_user_can_fetch_own_profile(self):
        user = UserFactory(email='me@example.com')
        client = APIClient()
        client.force_authenticate(user=user)
        response = client.get(reverse('me'))
        assert response.status_code == status.HTTP_200_OK
        assert response.data['email'] == 'me@example.com'
