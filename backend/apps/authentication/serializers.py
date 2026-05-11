from rest_framework import serializers
from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema_serializer
from drf_spectacular.utils import OpenApiResponse, OpenApiExample

User = get_user_model()


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "Valid Registration",
            value={
                "username": "john_doe",
                "password": "strongpassword123",
                "password_confirmation": "strongpassword123"
            }
        )
    ]
)
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
    

@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "User Response",
            value={
                "id": 1,
                "username": "john_doe",
                "email": "john@example.com",
                "role": "viewer",
                "is_active": True
            }
        )
    ]
)
class UserReadSerializer(serializers.ModelSerializer):
    """Only for output. Shows role as a plain string."""
    role = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'role', 'is_active')

    def get_role(self, obj):
        return obj.groups.values_list('name', flat=True).first()


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "Create User",
            value={
                "username": "new_user",
                "email": "user@example.com",
                "password": "strongpassword123",
                "role_assign": "editor",
                "is_active": True
            }
        )
    ]
)
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


    def validate_username(self, value):
        query = User.objects.filter(username=value)
        
        if self.instance:
            query = query.exclude(pk=self.instance.pk)

        if query.exists():
            raise serializers.ValidationError("This username is already taken.")
        
        return value

    def validate(self, attrs):
        if not self.instance and not attrs.get('password'):
            raise serializers.ValidationError({'password': 'Password is required.'})
        return attrs