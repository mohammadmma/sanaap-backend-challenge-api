from rest_framework.test import APIClient, APITestCase
from django.urls import reverse
from rest_framework import status
from apps.authentication.test.factory_user import UserFactory
from apps.authentication.models import AdminRequestModel
from django.contrib.auth import get_user_model
User = get_user_model()

class AdminDemandTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.demand_url = reverse('admin_demand')
        cls.taken_username = UserFactory.create()
        cls.new_user = UserFactory.build()
    
    def setUp(self):
        self.client = APIClient()

    def test_register_admin_demand_successfully_response_201(self):
        register_dict = {
            'username': self.new_user.username,
            'password': self.new_user.raw_password,
            'password_confirmation': self.new_user.raw_password
        }

        response = self.client.post(self.demand_url, register_dict)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['message'], 'Registered as viewer. Admin request is pending superuser approval.')

        created_user = User.objects.get(username=self.new_user.username)

        # 3. Check if the 'viewer' group is linked to this user
        self.assertTrue(created_user.groups.filter(name='viewer').exists())
        
        # 4. Optional: check the count to ensure they ONLY have one group
        self.assertEqual(created_user.groups.count(), 1)

        request_exists = AdminRequestModel.objects.filter(
        user__username=self.new_user.username
        ).exists()
        
        self.assertTrue(request_exists, "AdminRequestModel record was not created.")

    def test_if_username_already_exist(self):
        register_dict = {
            'username': self.taken_username.username,
            'password': self.new_user.raw_password,
            'password_confirmation': self.new_user.raw_password,
        }
        response = self.client.post(self.demand_url, register_dict)
        # print(f"%%%%%%%%%%%%% {response.data['username'][0]}")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['username'][0], 'This username is already taken.')
        
