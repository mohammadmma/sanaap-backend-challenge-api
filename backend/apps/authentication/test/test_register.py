from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from faker import Faker

from apps.authentication.test.factory_user import UserFactory
from django.contrib.auth import get_user_model
User = get_user_model()



class UserRegisterTestCase(APITestCase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user_saved = UserFactory.create()

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_object = UserFactory.build()
        cls.client = APIClient()
        cls.signup_url = reverse('register')
        cls.faker_obj = Faker()

    def test_successful_register_response_201(self):
        signup_dict = {
            'username': self.user_object.username,
            'password': 'test_Pass',
            'password_confirmation': 'test_Pass',
        }
        response = self.client.post(self.signup_url, signup_dict)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 2)
        new_user = User.objects.get(username=self.user_object.username)
        new_user_groups = new_user.groups.values().first()
        self.assertEqual(
            new_user.username,
            self.user_object.username,
        )

    def test_if_username_does_exist_error_400(self):
        register_dict = {
            "username": self.user_saved.username,
            "password": '12345678',
            "password_confirmation": '12345678',
        }
        response = self.client.post(self.signup_url, register_dict)
        response_msg = response.data['username'][0]
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(str(response_msg), 'This username is already taken.')