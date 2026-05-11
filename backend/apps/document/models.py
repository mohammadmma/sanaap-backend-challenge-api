# documents/models.py
import uuid
from django.db import models


def file_upload_path(instance, filename):
    """
    Called automatically when a file is saved.
    Returns the path (key) where it'll be stored in MinIO.
    
    Example result: "files/a3f8c2d1-4b5e-11ee/report.pdf"
    
    Using a UUID in the path prevents two problems:
    1. Name collisions (two users upload "report.pdf")
    2. Predictable URLs (security)
    """
    return f"files/{uuid.uuid4()}/{filename}"


def image_upload_path(instance, filename):
    return f"images/{uuid.uuid4()}/{filename}"


class Document(models.Model):
    title       = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    # These fields store only the PATH (key) in the database.
    # The actual bytes live in MinIO.
    file  = models.FileField(
        upload_to=file_upload_path,
        blank=True,
        null=True,
    )
    image = models.ImageField(
        upload_to=image_upload_path,
        blank=True,
        null=True,
    )

    uploaded_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_file_url(self):
        """Generate a temporary presigned URL for the file."""
        if self.file:
            return self.file.url   # django-storages handles the signing
        return None

    def get_image_url(self):
        """Generate a temporary presigned URL for the image."""
        if self.image:
            return self.image.url
        return None

    def __str__(self):
        return self.title