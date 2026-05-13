from rest_framework.test import APIClient, APITestCase
from django.urls import reverse
from rest_framework import status
from apps.authentication.test.factory_user import UserFactory
from django.conf import settings
from django.contrib.sessions.models import Session
from django.contrib.auth import get_user_model
User = get_user_model()



class LoginTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.valid_user = UserFactory.create()
        cls.login_url = reverse('login')
        cls.invalid_user = UserFactory.build()

    def setUp(self):
        self.client = APIClient()


    def test_successful_login_response_200(self):
        login_dict = {
            'username': self.valid_user.username,
            'password': self.valid_user.raw_password
        }
        # print(f"########### {login_dict}")

        response = self.client.post(self.login_url, login_dict)
        # print(f'################################ {response.cookies}')

        self.assertEqual(response.status_code, status.HTTP_200_OK)


        cookie_name = settings.SESSION_COOKIE_NAME
        # print(f"cookie name ------------------------> {cookie_name}")
        self.assertIn(cookie_name, response.cookies)

        session_key = response.cookies[settings.SESSION_COOKIE_NAME].value
        # print(f"session key -----------------> {session_key}")
    
        # Check if this key exists in the DB
        session_exists = Session.objects.filter(session_key=session_key).exists()
        self.assertTrue(session_exists)

    def test_invalid_username_error_401(self):
        login_dict = {
            'username': self.invalid_user.username,
            'password': self.valid_user.raw_password
        }

        response = self.client.post(self.login_url, login_dict)
        # print(f"################## {response.data}")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data, "Invalid credentials")


    def test_invalid_password_error_401(self):
        login_dict = {
            'username': self.valid_user.username,
            'password': self.invalid_user.raw_password
        }

        response = self.client.post(self.login_url, login_dict)
        # print(f"################## {response.data}")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data, "Invalid credentials")
        
        





    