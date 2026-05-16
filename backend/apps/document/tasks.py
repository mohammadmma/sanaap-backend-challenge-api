import base64
import uuid
import logging
from io import BytesIO

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from celery import shared_task
from apps.document.models import Document, DocumentStatus
from apps.document.services import DocumentCacheService
from django.conf import settings

logger = logging.getLogger(__name__)

def _get_cache_service():
    """
    DIP (Dependency Inversion): Centralizes cache instantiation.
    If you switch to Memcached, Mock Cache for testing, etc., 
    you only change it here.
    """
    return DocumentCacheService()


def _build_s3_client():
    """
    SRP:  this function has one job — build and return an S3 client.
    DIP:  the task calls this factory instead of calling boto3 directly,
          so in tests you can replace this function with one that returns
          a fake client.
    """
    return boto3.client(
        's3',
        endpoint_url=settings.AWS_S3_ENDPOINT_URL,
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
    folder = 'files' if file_entry['field_name'] == 'file' else 'images'

    object_key = f"{folder}/{uuid.uuid4()}/{file_entry['filename']}"

    file_bytes = base64.b64decode(file_entry['data_b64'])

    s3_client.upload_fileobj(
        BytesIO(file_bytes),
        settings.AWS_STORAGE_BUCKET_NAME,
        object_key,
        ExtraArgs={'ContentType': file_entry['content_type']},
    )

    return object_key

@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def upload_document_files(self, document_id: int, files_data: list[dict]):
    cache_service = _get_cache_service()

    try:
        document = Document.objects.get(pk=document_id)
    except Document.DoesNotExist:
        logger.error("Document %s not found — aborting.", document_id)
        return
    document.status = 'processing'
    document.save(update_fields=['status'])
    
    cache_service.invalidate(pk=document_id)

    try:
        s3_client     = _build_s3_client()
        update_fields = ['status']

        for file_entry in files_data:
            object_key = _upload_one_file(s3_client, file_entry)

            field_name = file_entry['field_name']
            if field_name == 'file':
                document.file.name = object_key
                update_fields.append('file')
            elif field_name == 'image':
                document.image.name = object_key
                update_fields.append('image')

            logger.info("Uploaded %s for Document %s → %s", field_name, document_id, object_key)

        document.status = 'done'
        document.save(update_fields=update_fields)
        cache_service.invalidate(pk=document_id)
        logger.info("Cache successfully flushed by Celery for Document %s", document_id)

    except (BotoCoreError, ClientError) as exc:
        logger.warning(
            "S3 error for Document %s — retry %s/%s: %s",
            document_id, self.request.retries, self.max_retries, exc,
        )
        if self.request.retries >= self.max_retries:
            Document.objects.filter(pk=document_id).update(status='failed')
        raise self.retry(exc=exc)

    except Exception as exc:
        logger.exception("Unexpected error for Document %s.", document_id)
        Document.objects.filter(pk=document_id).update(status='failed')
        raise