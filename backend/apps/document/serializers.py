from rest_framework import serializers
from .models import Document
from apps.authentication.permissions import get_user_role
from drf_spectacular.utils import extend_schema_serializer, OpenApiExample


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "Create Document (file upload)",
            value={
                "title": "Project Spec",
                "description": "API documentation file",
                "file": "(binary file)",
                "image": None
            },
            request_only=True
        ),
        OpenApiExample(
            "Document Response",
            value={
                "id": 1,
                "title": "Project Spec",
                "description": "API documentation file",
                "file_url": "https://minio.example.com/files/uuid/file.pdf",
                "image_url": None,
                "uploaded_by": 5,
                "uploaded_by_username": "john_doe",
                "created_at": "2026-01-01T12:00:00Z"
            },
            response_only=True
        )
    ]
)
class DocumentSerializer(serializers.ModelSerializer):
    file_url  = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()
    uploaded_by_username = serializers.CharField(
        source='uploaded_by.username',
        read_only=True
    )

    class Meta:
        model  = Document
        fields = [
            'id',
            'title',
            'description',
            'file',
            'image',
            'file_url',
            'image_url',
            'uploaded_by',
            'uploaded_by_username',
            'created_at',
        ]
        extra_kwargs = {
            'file':  {'write_only': True, 'required': False},
            'image': {'write_only': True, 'required': False},
        }

    def get_file_url(self, obj):
        return obj.get_file_url()

    def get_image_url(self, obj):
        return obj.get_image_url()
    
    def validate(self, attrs):
        request = self.context.get('request')
        user = request.user if request else None

        if self.instance and user:
            is_admin = get_user_role(user) == "admin"

            if not is_admin:
                if 'file' in attrs and attrs['file'] is None:
                    raise serializers.ValidationError({"file": "This field must not be empty!"})
                if 'image' in attrs and attrs['image'] is None:
                    raise serializers.ValidationError({"image": "This field must not be empty!"})
        
        return attrs