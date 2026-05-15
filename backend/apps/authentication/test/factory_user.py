from faker import Faker as FakerClass
from factory import django, Faker, post_generation
from django.contrib.auth import get_user_model
User = get_user_model()

class UserFactory(django.DjangoModelFactory):
    class Meta:
        model = User

    username = Faker('user_name')

    @post_generation
    def groups(self, create, extracted, **kwargs):
        if not create or not extracted:
            return

        self.groups.add(*extracted)

    @post_generation
    def password(self, create, extracted, **kwargs):
        password = extracted or FakerClass().password(length=8)
        self.set_password(password)
        self.raw_password = password
    

    
