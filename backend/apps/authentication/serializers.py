from rest_framework import serializers
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model

User = get_user_model()


class RegisterValidator(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True, min_length=8)
    password_confirmation = serializers.CharField(required=True, write_only=True)

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("This username is already taken.")
        return value


    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirmation']:
            raise serializers.ValidationError(
                "Password doesn't match its confirmation!"
            )
        attrs.pop('password_confirmation')
        return attrs
    

class UserReadSerializer(serializers.ModelSerializer):
    """Only for output. Shows role as a plain string."""
    role = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'role', 'is_active')

    def get_role(self, obj):
        return obj.groups.values_list('name', flat=True).first()


class UserWriteSerializer(serializers.ModelSerializer):
    """Only for input. Validates incoming data, nothing else."""
    role_assign = serializers.ChoiceField(
        choices=('admin', 'editor', 'viewer'),
        required=False,
        write_only=True,
    )
    password = serializers.CharField(
        write_only=True,
        required=False,
        min_length=8,
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'role_assign', 'is_active')

    # def validate_role_assign(self, group):
    #     valid_roles = ('admin', 'editor', 'viewer')
    #     if group.name not in valid_roles:
    #         raise serializers.ValidationError(
    #             f'Invalid role. Choose from: {", ".join(valid_roles)}'
    #         )
    #     return group

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("This username is already taken.")
        return value

    def validate(self, attrs):
        if not self.instance and not attrs.get('password'):
            raise serializers.ValidationError({'password': 'Password is required.'})
        return attrs