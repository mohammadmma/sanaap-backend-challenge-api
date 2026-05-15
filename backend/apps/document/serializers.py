from rest_framework import serializers
from .models import Document

class DocumentReadSerializer(serializers.ModelSerializer):
    """
    SRP: pure output serializer. Never used for write operations.
    Generates presigned URLs and exposes upload status.
    """
    file_url             = serializers.SerializerMethodField()
    image_url            = serializers.SerializerMethodField()
    uploaded_by_username = serializers.CharField(source='uploaded_by.username', read_only=True)

    class Meta:
        model  = Document
        fields = [
            'id', 'title', 'description',
            'file_url', 'image_url',
            'uploaded_by', 'uploaded_by_username',
            'created_at', 'updated_at',
        ]

    def get_file_url(self, obj):
        return obj.get_file_url()

    def get_image_url(self, obj):
        return obj.get_image_url()
    
class DocumentWriteSerializer(serializers.ModelSerializer):
    """
    SRP: validates only the metadata fields the client sends.
    File bytes are extracted by the View before this serializer is called,
    so this class never touches MinIO — that's the task's job.

    SOLID fix: removed the authorisation check (get_user_role) that was
    leaking into the old single serializer. Authorisation belongs in
    permission classes, not serializers.
    """
    class Meta:
        model  = Document
        fields = ['title', 'description']