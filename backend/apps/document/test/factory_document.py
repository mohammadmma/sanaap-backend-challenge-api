import factory
from factory import django, Faker, SubFactory
from apps.document.models import Document
from apps.authentication.test.factory_user import UserFactory

class DocumentFactory(django.DjangoModelFactory):
    class Meta:
        model = Document

    title = Faker('sentence', nb_words=4)
    description = Faker('paragraph')
    
    uploaded_by = SubFactory(UserFactory)

    file = django.FileField(filename='test_document.pdf')
    image = django.ImageField(filename='test_image.jpg')