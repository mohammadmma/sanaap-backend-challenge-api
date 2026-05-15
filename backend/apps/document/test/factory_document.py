import factory
from factory import django, Faker, SubFactory
from apps.document.models import Document
from apps.authentication.test.factory_user import UserFactory

class DocumentFactory(django.DjangoModelFactory):
    class Meta:
        model = Document

    # Basic Fields
    title = Faker('sentence', nb_words=4)
    description = Faker('paragraph')
    
    # Relationships
    # SubFactory automatically creates a User if you don't provide one
    uploaded_by = SubFactory(UserFactory)

    # File Fields
    # These create in-memory files that behave like real uploads
    file = django.FileField(filename='test_document.pdf')
    image = django.ImageField(filename='test_image.jpg')