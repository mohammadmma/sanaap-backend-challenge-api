import uuid
from django.db import models


def file_upload_path(instance, filename):
    return f"files/{uuid.uuid4()}/{filename}"


def image_upload_path(instance, filename):
    return f"images/{uuid.uuid4()}/{filename}"


class Document(models.Model):
    title       = models.CharField(max_length=255)
    description = models.TextField(blank=True)

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
            return self.file.url
        return None

    def get_image_url(self):
        """Generate a temporary presigned URL for the image."""
        if self.image:
            return self.image.url
        return None

    def __str__(self):
        return self.title