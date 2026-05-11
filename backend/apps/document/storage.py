from storages.backends.s3boto3 import S3Boto3Storage
from django.conf import settings


class MinIOStorage(S3Boto3Storage):
    """
    Custom storage that rewrites presigned URLs from the Docker-internal
    hostname (minio:9000) to the public hostname (localhost:9000 in dev,
    or your real domain in production).
    """

    def url(self, name, expire=None):
        
        original_url = super().url(name, expire)

        
        internal = settings.AWS_S3_ENDPOINT_URL
        public = settings.MINIO_PUBLIC_ENDPOINT_URL 

        return original_url.replace(internal, public)