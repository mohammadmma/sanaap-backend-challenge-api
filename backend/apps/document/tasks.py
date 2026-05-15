import base64
import uuid
import logging
from io import BytesIO

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from celery import shared_task
# from django.apps import apps
from apps.document.models import Document, DocumentStatus
from django.conf import settings

logger = logging.getLogger(__name__)


def _build_s3_client():
    """
    SRP:  this function has one job — build and return an S3 client.
    DIP:  the task calls this factory instead of calling boto3 directly,
          so in tests you can replace this function with one that returns
          a fake client.
    """
    return boto3.client(
        's3',
        endpoint_url=settings.AWS_S3_ENDPOINT_URL,       # tells boto3 to use MinIO, not AWS
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_S3_REGION_NAME,
    )

def _upload_one_file(s3_client, file_entry: dict) -> str:
    """
    SRP:  upload exactly one file, return its storage key.
          Raises on any failure — the task decides what to do with errors.
    OCP:  adding support for a 'thumbnail' field type means adding one
          more elif here and zero changes to the task or the view.
    """
    # Determine the folder based on what kind of field this is
    folder = 'files' if file_entry['field_name'] == 'file' else 'images'

    # Build a unique path inside MinIO — same pattern your upload_to functions use
    object_key = f"{folder}/{uuid.uuid4()}/{file_entry['filename']}"

    # Convert base64 string back to raw bytes
    file_bytes = base64.b64decode(file_entry['data_b64'])

    # Wrap bytes in a file-like object so upload_fileobj can read it in chunks
    s3_client.upload_fileobj(
        BytesIO(file_bytes),
        settings.AWS_STORAGE_BUCKET_NAME,
        object_key,
        ExtraArgs={'ContentType': file_entry['content_type']},  # e.g. 'image/png', 'application/pdf'
    )

    # Return the key — caller stores this on the model field
    return object_key

@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def upload_document_files(self, document_id: int, files_data: list[dict]):

    try:
        document = Document.objects.get(pk=document_id)
    except Document.DoesNotExist:
        # The document was deleted between the view creating it and the worker
        # picking up the task. Nothing to do — don't retry, just stop cleanly.
        logger.error("Document %s not found — aborting.", document_id)
        return
    # ── Step 2: mark as processing so the client knows work has started ────────
    document.status = 'processing'
    document.save(update_fields=['status'])
    # update_fields=['status'] tells Django to only UPDATE that one column,
    # not re-save the entire row. Faster and avoids race conditions with
    # other fields being modified concurrently.

    try:
        s3_client     = _build_s3_client()
        update_fields = ['status']   # will grow as we successfully upload fields

        for file_entry in files_data:
            # _upload_one_file handles both 'file' and 'image' field_names —
            # the loop treats them identically at this level.
            object_key = _upload_one_file(s3_client, file_entry)

            field_name = file_entry['field_name']
            if field_name == 'file':
                # Assigning to .name sets the path stored in the DB column
                # without triggering another upload through django-storages.
                document.file.name = object_key
                update_fields.append('file')
            elif field_name == 'image':
                document.image.name = object_key
                update_fields.append('image')

            logger.info("Uploaded %s for Document %s → %s", field_name, document_id, object_key)

        # All files uploaded successfully
        document.status = 'done'
        document.save(update_fields=update_fields)
        # update_fields here might be: ['status', 'file', 'image']
        # Only the columns that actually changed get written.
        # ── Step 4: handle failures at two levels ─────────────────────────────────

    except (BotoCoreError, ClientError) as exc:
        # S3/MinIO errors — network blip, wrong credentials, bucket missing, etc.
        # These are potentially transient, so we retry.
        logger.warning(
            "S3 error for Document %s — retry %s/%s: %s",
            document_id, self.request.retries, self.max_retries, exc,
        )
        if self.request.retries >= self.max_retries:
            # Final attempt also failed — mark permanently so the client
            # stops polling and shows an error.
            Document.objects.filter(pk=document_id).update(status='failed')
        raise self.retry(exc=exc)
        # raise self.retry() re-raises the exception AND schedules the task
        # to run again after default_retry_delay seconds.

    except Exception as exc:
        # Unexpected error (bug in our code, etc.) — don't retry, just fail fast.
        logger.exception("Unexpected error for Document %s.", document_id)
        Document.objects.filter(pk=document_id).update(status='failed')
        raise   # re-raise so Celery marks the task as FAILURE in its result backend