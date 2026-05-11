# documents/storage.py
from storages.backends.s3boto3 import S3Boto3Storage
from django.conf import settings


class MinIOStorage(S3Boto3Storage):
    """
    Custom storage that rewrites presigned URLs from the Docker-internal
    hostname (minio:9000) to the public hostname (localhost:9000 in dev,
    or your real domain in production).
    """

    def url(self, name, expire=None):
        # Get the URL that django-storages generates (uses minio:9000)
        original_url = super().url(name, expire)

        # Replace the internal Docker hostname with the public one
        internal = settings.AWS_S3_ENDPOINT_URL          # http://minio:9000
        public   = settings.MINIO_PUBLIC_ENDPOINT_URL    # http://localhost:9000

        return original_url.replace(internal, public)