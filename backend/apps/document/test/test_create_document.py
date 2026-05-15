from rest_framework.test import APIClient, APITestCase
from django.core.cache import cache
from apps.document.services import CacheKeyService
from django.urls import reverse
from rest_framework import status
from apps.authentication.test.factory_user import UserFactory
from apps.document.test.factory_document import DocumentFactory
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.models import Group
from apps.document.models import Document
from django.contrib.auth import get_user_model
User = get_user_model()


class CreateDocumentTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.viewer_group, _ = Group.objects.get_or_create(name='viewer')
        cls.editor_group, _ = Group.objects.get_or_create(name='editor')
        cls.admin_group, _ = Group.objects.get_or_create(name='admin')

        cls.admin_user = UserFactory.create(groups=[cls.admin_group])
        cls.editor_user = UserFactory.create(groups=[cls.editor_group])
        cls.viewer_user = UserFactory.create(groups=[cls.viewer_group])

        cls.new_doc = DocumentFactory.build(uploaded_by=cls.editor_user)
        cls.existed_doc = DocumentFactory.create_batch(5)

        cls.list_url = reverse('doc_crud-list')



    def setUp(self):
        self.client = APIClient()
        cache.clear()

    def test_if_viewer_post_doc_error_403(self):
        self.client.force_authenticate(user=self.viewer_user)
        create_dict = {
            'title': self.new_doc.title,
            'description': self.new_doc.description,
            'file': self.new_doc.file,
            'image': self.new_doc.image
        }

        response = self.client.post(self.list_url, create_dict)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


    def test_create_new_doc_invalidate_cache(self):
        self.client.force_authenticate(user=self.editor_user)
        params = {
            'ordering': '-title',
            'title': 't'
        }
        response = self.client.get(self.list_url, query_params=params)
        request = response.renderer_context['request']

        cache_key = CacheKeyService.generate_list_cache_key(request)
        cached_data = cache.get(cache_key)
        self.assertIsNotNone(cached_data, f"Cache key {cache_key} was not set!")


        create_dict = {
            'title': self.new_doc.title,
            'description': self.new_doc.description,
        }
        response = self.client.post(self.list_url, create_dict)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        document = Document.objects.get(title=self.new_doc.title)
        self.assertEqual(document.uploaded_by, self.editor_user)

        cached_data = cache.get(cache_key)
        self.assertIsNone(cached_data)


        