from rest_framework import serializers
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