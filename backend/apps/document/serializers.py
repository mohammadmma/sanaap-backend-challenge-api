# documents/serializers.py
from rest_framework import serializers
from .models import Document
from apps.authentication.permissions import get_user_role


class DocumentSerializer(serializers.ModelSerializer):
    # These are computed fields — they call the model methods
    file_url  = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()

    class Meta:
        model  = Document
        fields = [
            'id',
            'title',
            'description',
            'file',         # write-only (upload)
            'image',        # write-only (upload)
            'file_url',     # read-only (presigned URL for download)
            'image_url',    # read-only (presigned URL for download)
            'uploaded_by',
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