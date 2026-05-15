import uuid
from django.db import models
from django.contrib.auth import get_user_model
User = get_user_model()


def file_upload_path(instance, filename):
    return f"files/{uuid.uuid4()}/{filename}"


def image_upload_path(instance, filename):
    return f"images/{uuid.uuid4()}/{filename}"


class DocumentStatus(models.TextChoices):
    PENDING    = 'pending',    'Pending'
    PROCESSING = 'processing', 'Processing'
    DONE       = 'done',       'Done'
    FAILED     = 'failed',     'Failed'

class Document(models.Model):
    title       = models.CharField(max_length=255, db_index=True)
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
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    status  = models.CharField(
        max_length=20,
        choices=DocumentStatus.choices,
        default=DocumentStatus.PENDING,
        db_index=True,
    )
    task_id = models.CharField(max_length=255, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)

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