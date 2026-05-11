from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import transaction

User = get_user_model()


class UserService:

    @staticmethod
    def create_user(validated_data: dict):
        """Creates a user, hashes password, assigns role."""
        password    = validated_data.pop('password')
        role_assign = validated_data.pop('role_assign', 'viewer')

        with transaction.atomic():
            user = User.objects.create_user(password=password, **validated_data)

            group, _  = Group.objects.get_or_create(name=role_assign)
            user.groups.set([group])

        return user

    @staticmethod
    def update_user(user, validated_data: dict):
        """Updates a user. Password and role are both optional."""
        password    = validated_data.pop('password', None)
        role_assign = validated_data.pop('role_assign', 'viewer')

        with transaction.atomic():
            for field, value in validated_data.items():
                setattr(user, field, value)
            user.save()

            if password:
                user.set_password(password)
                user.save()

            if role_assign:
                group, _ = Group.objects.get_or_create(name=role_assign.name)
                user.groups.set([group])

        return user

    @staticmethod
    def delete_user(requesting_user, target_user) -> None:
        """Deletes a user. Prevents self-deletion."""
        if requesting_user == target_user:
            raise ValueError('You cannot delete your own account.')
        target_user.delete()