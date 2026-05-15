from rest_framework.test import APIClient, APITestCase
from django.urls import reverse
from rest_framework import status
from apps.authentication.test.factory_user import UserFactory
from django.conf import settings
from django.contrib.sessions.models import Session
from django.contrib.auth import get_user_model
User = get_user_model()

class LogoutTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = UserFactory.create()
        cls.logout_url = reverse('logout')
        cls.login_url = reverse('login')

    def setUp(self):
        self.client = APIClient()

    def test_unauthorized_user_error_403(self):
        response = self.client.post(self.logout_url)



        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        detail_code = response.data['detail'].code
        self.assertEqual(detail_code, "not_authenticated")

    def test_logout_successfully_response_200(self):
        valid_user = {
            'username': self.user.username,
            'password': self.user.raw_password,
        }
        self.client.post(self.login_url, valid_user)

        session_key = self.client.cookies[settings.SESSION_COOKIE_NAME].value
    
        session_exists = Session.objects.filter(session_key=session_key).exists()
        self.assertTrue(session_exists)

        logout_response = self.client.post(self.logout_url)

        self.assertEqual(logout_response.status_code, status.HTTP_200_OK)

        session_exists = Session.objects.filter(session_key=session_key).exists()
        self.assertFalse(session_exists)


    