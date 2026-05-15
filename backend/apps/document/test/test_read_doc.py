from rest_framework.test import APIClient, APITestCase
from django.core.cache import cache
from apps.document.services import CacheKeyService
from unittest.mock import patch
from django.urls import reverse
from rest_framework import status
from apps.authentication.test.factory_user import UserFactory
from apps.document.test.factory_document import DocumentFactory
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
User = get_user_model()


class ReadDocumentTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.admin_group, _ = Group.objects.get_or_create(name='admin')
        cls.viewer_group, _ = Group.objects.get_or_create(name='viewer')
        cls.editor_group, _ = Group.objects.get_or_create(name='editor')
        cls.admin_user = UserFactory.create(groups=[cls.admin_group])
        cls.editor_user = UserFactory.create(groups=[cls.editor_group])
        cls.viewer_user = UserFactory.create(groups=[cls.viewer_group])

        cls.doc_admin = DocumentFactory.create(uploaded_by=cls.admin_user)
        cls.doc_editor = DocumentFactory.create(uploaded_by=cls.editor_user)
        cls.doc_viewer = DocumentFactory.create(uploaded_by=cls.viewer_user)
        cls.list_url = reverse('doc_crud-list')
        cls.doc_admin_detail_url = reverse('doc_crud-detail', kwargs={'pk': cls.doc_admin.pk})
        cls.doc_editor_detail_url = reverse('doc_crud-detail', kwargs={'pk': cls.doc_editor.pk})
        cls.doc_viewer_detail_url = reverse('doc_crud-detail', kwargs={'pk': cls.doc_viewer.pk})

    def setUp(self):
        self.client = APIClient()
        cache.clear()

    def test_unauthenticated_user_dont_have_access_error_403(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch('django.core.cache.cache.get')
    @patch('django.core.cache.cache.set')
    def test_detail_caching_miss_and_call_cache_set(self, mock_set, mock_get):
        self.client.force_authenticate(user=self.viewer_user)

        mock_get.return_value = None
        
        response = self.client.get(self.doc_admin_detail_url)
        
        self.assertTrue(mock_set.called)
        self.assertEqual(response.status_code, 200)

    def test_update_invalidates_cache(self):
        self.client.force_authenticate(user=self.editor_user)
        
        cache_key = CacheKeyService.generate_detail_cache_key(self.doc_editor.pk)
        cache.set(cache_key, {'title': 'Cached Title'})

        response = self.client.patch(self.doc_editor_detail_url, {'title': 'Database Title'})
        

        self.assertIsNone(cache.get(cache_key))
    
    def test_list_caching(self):
        self.client.force_authenticate(user=self.viewer_user)
        query_params = {
            "ordering": "-title"
        }
        response = self.client.get(self.list_url, query_params=query_params)
        request = response.renderer_context['request']
        cache_key = CacheKeyService.generate_list_cache_key(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        cached_data = cache.get(cache_key)
        self.assertIsNotNone(cached_data, f"Cache key {cache_key} was not set!")
        self.assertEqual(response.data, cached_data)

        
    def test_file_related_path_db(self):
        self.client.force_authenticate(user=self.viewer_user)
        response = self.client.get(self.doc_admin_detail_url)
        file_path = response.data['file_url']

        self.assertEqual(file_path, self.doc_admin.file.url)


    def test_file_image_related_path_db(self):
        self.client.force_authenticate(user=self.viewer_user)
        response = self.client.get(self.doc_admin_detail_url)

        image_path = response.data['image_url']
        self.assertEqual(image_path, self.doc_admin.image.url)