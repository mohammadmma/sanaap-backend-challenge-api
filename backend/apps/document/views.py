import base64
import logging

# from django.conf import settings
# from django.core.cache import cache
from rest_framework import viewsets, parsers, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db import transaction
from apps.authentication.permissions import IsAdmin, IsEditor, IsViewer
from apps.document.filters import DocumentFilter
from apps.document.pagination import StandardResultsSetPagination
from apps.document.models import Document, DocumentStatus
from apps.document.serializers import DocumentReadSerializer, DocumentWriteSerializer
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from apps.document.services import AbstractDocumentCacheService, DocumentCacheService
from apps.document.tasks import upload_document_files

logger = logging.getLogger(__name__)

class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.select_related('uploaded_by').all().order_by('-created_at')

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]

    filterset_class = DocumentFilter

    search_fields = ['title', 'description']

    ordering_fields = ['created_at', 'title']
    ordering = ['-created_at']

    pagination_class = StandardResultsSetPagination

    def get_permissions(self):
        if self.action in ['destroy', 'clear_file', 'clear_image']:
            return [IsAdmin()]
        elif self.action in ['create', 'update', 'partial_update']:
            return [IsEditor()]
        return [IsViewer()]
    
    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return DocumentWriteSerializer
        return DocumentReadSerializer

    
    parser_classes = [
        parsers.MultiPartParser,   
        parsers.FormParser,        
        parsers.JSONParser,        
    ]

    cache_service_class: type[AbstractDocumentCacheService] = DocumentCacheService

    def get_cache_service(self) -> AbstractDocumentCacheService:
        """
        Factory method (GoF). Subclasses or tests override cache_service_class,
        not this method. One override point, not scattered instantiations.
        """
        if not hasattr(self, '_cache_service'):
            self._cache_service = self.cache_service_class()
        return self._cache_service


    # def _get_detail_cache_key(self, pk):
    #     return f"document_detail_{pk}"

    # def _get_list_cache_pattern(self):
        
    #     return "document_list_*"

    # def _invalidate_document_cache(self, pk=None):
    #     """Clears detail cache for a specific PK and sweeps all list caches."""
    #     keys_to_delete = []
    #     if pk:
    #         keys_to_delete.append(CacheKeyService.generate_detail_cache_key(pk))
        
        
    #     list_keys = cache.keys(CacheKeyService.generate_list_cache_key())
    #     if list_keys:
    #         keys_to_delete.extend(list_keys)
            
    #     if keys_to_delete:
    #         cache.delete_many(keys_to_delete)



    @extend_schema(
    tags=["Documents"],
    summary="Retrieve document",
    description="Returns a single document. Response is cached.",
    responses={200: DocumentReadSerializer}
    )
    def retrieve(self, request, *args, **kwargs):
        """Cache the detail view of a document."""
        pk = kwargs.get('pk')
        # cache_key = CacheKeyService.generate_detail_cache_key(pk)
        # cached_data = cache.get(cache_key)
        cache_service = self.get_cache_service()
        cached_data = cache_service.get_detail(pk)

        if cached_data is not None:
            return Response(cached_data)


        response = super().retrieve(request, *args, **kwargs)
        # cache.set(cache_key, response.data, timeout=getattr(settings, 'DOCUMENT_CACHE_TTL', 2700))
        cache_service.set_detail(pk, response.data)
        return response


    @extend_schema(
        tags=["Documents"],
        summary="List documents",
        description="""
    Returns paginated list of documents.

    Supports:
    - filtering
    - search
    - ordering
    - caching (response may be cached)
    """,
        parameters=[
            OpenApiParameter("title", str, description="Case-insensitive title search"),
            OpenApiParameter("uploaded_by", int),
            OpenApiParameter("created_after", str),
            OpenApiParameter("created_before", str),
            OpenApiParameter("search", str, description="Search in title & description"),
            OpenApiParameter("ordering", str, description="created_at, title"),
            OpenApiParameter("page", int),
            OpenApiParameter("page_size", int),
        ],
        responses={200: DocumentReadSerializer(many=True)}
    )
    def list(self, request, *args, **kwargs):
        """Cache the list view, accounting for query params (filters/pages)."""

        # query_string = request.META.get('QUERY_STRING', '')
        # # query_string = request.query_params.dict().items()
        # print(f"^^^^^^^^^^^^^^^^^^{query_string}")

        # cache_key = CacheKeyService.generate_list_cache_key(request)
        cache_service = self.get_cache_service()
        cached_data = cache_service.get_list(request)

        if cached_data is not None:
            return Response(cached_data)

        response = super().list(request, *args, **kwargs)
        cache_service.set_list(request, response.data)
        return response


    def _extract_files_payload(self, request):
        """
        SRP: isolated helper that extracts and base64-encodes uploaded files.
        Returns a list ready to pass directly to the Celery task.
        Keeping this separate means the create/update methods stay readable.
        """
        payload = []
        for field_name in ('file', 'image'):
            uploaded = request.FILES.get(field_name)
            if uploaded:
                payload.append({
                    'field_name':   field_name,
                    'filename':     uploaded.name,
                    'content_type': uploaded.content_type,
                    'data_b64':     base64.b64encode(uploaded.read()).decode('utf-8'),
                })
        return payload


    # def perform_create(self, serializer):
    #     serializer.save(uploaded_by=self.request.user)
    #     # self._invalidate_document_cache()
    #     self.get_cache_service().invalidate()

    # def perform_update(self, serializer):
    #     instance = serializer.save()
    #     # self._invalidate_document_cache(instance.pk)
    #     self.get_cache_service().invalidate(instance.pk)

    def perform_destroy(self, instance):
        pk = instance.pk
        instance.delete()
        # self._invalidate_document_cache(pk)
        self.get_cache_service().invalidate(pk)

    
    @extend_schema(
        tags=["Documents"],
        summary="Create document",
        description="""
    Creates a document with optional file/image upload.

    Requires:
    - Editor role

    Content-Type must be:
    - multipart/form-data
    """,
        request=DocumentWriteSerializer,
        responses={201: DocumentReadSerializer}
    )
    def create(self, request, *args, **kwargs):
        files_payload = self._extract_files_payload(request)

        # Strip file fields so the write serializer never sees them
        data = request.data.copy()
        data.pop('file', None)
        data.pop('image', None)

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            document = serializer.save(
                uploaded_by=request.user,
                status=DocumentStatus.PENDING if files_payload else DocumentStatus.DONE,
            )

        if files_payload:
            task = upload_document_files.delay(document.id, files_payload)
            document.task_id = task.id
            document.save(update_fields=['task_id'])
            logger.info("Document %s created — upload task %s queued.", document.id, task.id)

        self.get_cache_service().invalidate()
        response_status = status.HTTP_202_ACCEPTED if files_payload else status.HTTP_201_CREATED
        return Response(DocumentReadSerializer(document).data, status=response_status)


    @extend_schema(
        tags=["Documents"],
        summary="Update document",
        description="""
    Updates document fields.

    ⚠️ Non-admin users:
    - Cannot set file/image to null
    """,
        request=DocumentWriteSerializer,
        responses={200: DocumentReadSerializer}
    )
    def update(self, request, *args, **kwargs):
        partial       = kwargs.pop('partial', False)
        instance      = self.get_object()
        files_payload = self._extract_files_payload(request)

        data = request.data.copy()
        data.pop('file', None)
        data.pop('image', None)

        serializer = self.get_serializer(instance, data=data, partial=partial)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            document = serializer.save(
                status=DocumentStatus.PENDING if files_payload else instance.status,
            )

        if files_payload:
            task = upload_document_files.delay(document.id, files_payload)
            document.task_id = task.id
            document.save(update_fields=['task_id'])

        self.get_cache_service().invalidate(instance.pk)
        response_status = status.HTTP_202_ACCEPTED if files_payload else status.HTTP_200_OK
        return Response(DocumentReadSerializer(document).data, status=response_status)
    

    @extend_schema(
        tags=["Documents"],
        summary="Update document",
        description="""
    Updates document fields.

    ⚠️ Non-admin users:
    - Cannot set file/image to null
    """,
        request=DocumentWriteSerializer,
        responses={200: DocumentReadSerializer}
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)
    

    @extend_schema(
    tags=["Documents"],
    summary="Delete document",
    description="Deletes a document (Admin only).",
    responses={
        204: OpenApiResponse(description="Deleted successfully"),
        403: OpenApiResponse(description="Forbidden")
    }
)
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)
    
    @action(detail=True, methods=['get'], url_path='upload-status')
    def upload_status(self, request, pk=None):
        """
        SRP: dedicated endpoint for polling async upload state.
        Clients call this after receiving 202 until status == 'done' | 'failed'.
        """
        document = self.get_object()
        return Response({
            'id':        document.id,
            'status':    document.status,
            'task_id':   document.task_id,
            'file_url':  document.get_file_url(),
            'image_url': document.get_image_url(),
        })


    @extend_schema(
        tags=["Documents"],
        summary="Remove file from document",
        description="""
    Deletes the file associated with the document.

    - Admin only
    - Invalidates cache
    """,
        responses={
            204: OpenApiResponse(description="File deleted"),
            400: OpenApiResponse(description="No file found")
        }
    )
    @action(detail=True, methods=['post'], url_path='clear_file')
    def clear_file(self, request, pk=None):
        obj = self.get_object()
        if obj.file:
            with transaction.atomic():
                obj.file = None
                obj.save()
            

            # self._invalidate_document_cache(pk)
            self.get_cache_service().invalidate(pk)
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({"detail": "No file found."}, status=400)
    

    @extend_schema(
        tags=["Documents"],
        summary="Remove image from document",
        description="""
    Deletes the image associated with the document.

    - Admin only
    """,
        responses={
            200: OpenApiResponse(description="Image deleted"),
            400: OpenApiResponse(description="No image found")
        }
    )
    @action(detail=True, methods=['post'], url_path='clear_image')
    def clear_image(self, request, pk=None):
        obj = self.get_object()
        if obj.image:
            with transaction.atomic():
                obj.image = None
                obj.save()
            

            # self._invalidate_document_cache(pk)
            self.get_cache_service().invalidate(pk)
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({"detail": "No image found."}, status=400)