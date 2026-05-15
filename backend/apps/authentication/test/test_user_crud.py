from rest_framework.test import APIClient, APITestCase
from unittest.mock import patch
from django.urls import reverse
from rest_framework import status
from apps.authentication.test.factory_user import UserFactory
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
User = get_user_model()

class UserCRUDTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.admin_group, _ = Group.objects.get_or_create(name='admin')
        cls.viewer_group, _ = Group.objects.get_or_create(name='viewer')
        cls.editor_group, _ = Group.objects.get_or_create(name='editor')

        cls.admin_user = UserFactory.create(groups=[cls.admin_group])
        cls.editor_user = UserFactory.create(groups=[cls.editor_group])
        cls.viewer_user = UserFactory.create(groups=[cls.viewer_group])

        cls.other_admin = UserFactory.create(groups=[cls.admin_group])
        cls.superuser = UserFactory.create(is_superuser=True)

        cls.list_url = reverse('user_crud-list')



    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin_user)

    def test_list_response_200(self):
        url = f'{self.list_url}?ordering=username'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        usernames = [user['username'] for user in response.data['results']]
        results = response.data.get('results')
        count = response.data.get('count')
        self.assertEqual(len(results), 5)
        self.assertEqual(usernames, sorted(usernames))
    
    def test_retrieve_response_200(self):
        url = reverse('user_crud-detail', kwargs={'pk': self.viewer_user.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], self.viewer_user.username)
        

    def test_unauthorized_permission_denied_error_403(self):
        self.client.force_authenticate(user=self.viewer_user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_if_try_update_another_admin_acount_error_400(self):
        url = reverse('user_crud-detail', kwargs={'pk': self.other_admin.id})
        response = self.client.put(url, {'username': 'editor', 'role_assign': 'editor'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, "You can not manipulate this user")

        other_admin_account = User.objects.get(id=self.other_admin.id)
        self.assertEqual(other_admin_account.username, self.other_admin.username)

        other_admin_group = other_admin_account.groups.values_list('name', flat=True).first()
        self.assertEqual(other_admin_group, self.other_admin.groups.values_list('name', flat=True).first())

    def test_if_try_partial_update_other_admin_acount_error_400(self):
        url = reverse('user_crud-detail', kwargs={'pk': self.other_admin.pk})
        response = self.client.patch(url, {'role_assign': 'viewer'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        other_admin_account = User.objects.get(id=self.other_admin.id)
        other_admin_group = other_admin_account.groups.values_list('name', flat=True).first()
        self.assertEqual(other_admin_group, self.other_admin.groups.values_list('name', flat=True).first())

    def test_if_try_update_superuser_acount_error_400(self):
        url = reverse('user_crud-detail', kwargs={'pk': self.superuser.id})
        response = self.client.put(url, {'username': 'hacked_superuser', 'role_assign': 'editor'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, "You can not manipulate this user")

        superuser_account = User.objects.get(id=self.superuser.id)
        self.assertEqual(superuser_account.username, self.superuser.username)

        superuser_group = superuser_account.groups.values_list('name', flat=True).first()
        self.assertEqual(superuser_group, self.superuser.groups.values_list('name', flat=True).first())

    def test_if_try_partial_update_superuser_acount_error_400(self):
        url = reverse('user_crud-detail', kwargs={'pk': self.superuser.pk})
        response = self.client.patch(url, {'role_assign': 'patched_super'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        superuser_account = User.objects.get(id=self.superuser.id)
        superuser_group = superuser_account.groups.values_list('name', flat=True).first()
        self.assertEqual(superuser_group, self.superuser.groups.values_list('name', flat=True).first())


    def test_if_try_delete_another_admin_acount_error_400(self):
        url = reverse('user_crud-detail', kwargs={'pk': self.other_admin.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(User.objects.filter(pk=self.other_admin.pk).exists())

    def test_if_try_delete_superuser_acount_error_400(self):
        url = reverse('user_crud-detail', kwargs={'pk': self.superuser.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_if_try_delete_own_acount_error_400(self):
        url = reverse('user_crud-detail', kwargs={'pk': self.admin_user.pk})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, 'You can not manipulate this user')

    def test_successful_delete_acount_response_204(self):
        url = reverse('user_crud-detail', kwargs={'pk': self.viewer_user.pk})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(User.objects.filter(pk=self.viewer_user.pk).exists())
