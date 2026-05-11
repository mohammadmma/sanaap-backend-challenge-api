from django.conf import settings
from django.core.cache import cache
from rest_framework import viewsets, parsers, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db import transaction
from apps.authentication.permissions import IsAdmin, IsEditor, IsViewer
from apps.document.filters import DocumentFilter
from apps.document.pagination import StandardResultsSetPagination
from .models import Document
from .serializers import DocumentSerializer


class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.select_related('uploaded_by').all().order_by('-created_at')
    serializer_class = DocumentSerializer

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

    
    parser_classes = [
        parsers.MultiPartParser,   
        parsers.FormParser,        
        parsers.JSONParser,        
    ]


    def _get_detail_cache_key(self, pk):
        return f"document_detail_{pk}"

    def _get_list_cache_pattern(self):
        
        return "document_list_*"

    def _invalidate_document_cache(self, pk=None):
        """Clears detail cache for a specific PK and sweeps all list caches."""
        keys_to_delete = []
        if pk:
            keys_to_delete.append(self._get_detail_cache_key(pk))
        
        
        list_keys = cache.keys(self._get_list_cache_pattern())
        if list_keys:
            keys_to_delete.extend(list_keys)
            
        if keys_to_delete:
            cache.delete_many(keys_to_delete)



    def retrieve(self, request, *args, **kwargs):
        """Cache the detail view of a document."""
        pk = kwargs.get('pk')
        cache_key = self._get_detail_cache_key(pk)
        cached_data = cache.get(cache_key)

        if cached_data is not None:
            return Response(cached_data)


        response = super().retrieve(request, *args, **kwargs)
        cache.set(cache_key, response.data, timeout=getattr(settings, 'DOCUMENT_CACHE_TTL', 2700))
        return response

    def list(self, request, *args, **kwargs):
        """Cache the list view, accounting for query params (filters/pages)."""

        query_string = request.META.get('QUERY_STRING', '')
        cache_key = f"document_list_{query_string}"
        cached_data = cache.get(cache_key)

        if cached_data is not None:
            return Response(cached_data)

        response = super().list(request, *args, **kwargs)
        cache.set(cache_key, response.data, timeout=getattr(settings, 'DOCUMENT_CACHE_TTL', 2700))
        return response



    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)
        self._invalidate_document_cache()

    def perform_update(self, serializer):
        instance = serializer.save()
        self._invalidate_document_cache(instance.pk)

    def perform_destroy(self, instance):
        pk = instance.pk
        instance.delete()
        self._invalidate_document_cache(pk)

    @action(detail=True, methods=['post'], url_path='clear_file')
    def clear_file(self, request, pk=None):
        obj = self.get_object()
        if obj.file:
            with transaction.atomic():
                obj.file = None
                obj.save()
            

            self._invalidate_document_cache(pk)
            return Response({"detail": "File deleted."}, status=status.HTTP_204_NO_CONTENT)
        return Response({"detail": "No file found."}, status=400)
    
    @action(detail=True, methods=['post'], url_path='clear_image')
    def clear_image(self, request, pk=None):
        obj = self.get_object()
        if obj.image:
            with transaction.atomic():
                obj.image = None
                obj.save()
            

            self._invalidate_document_cache(pk)
            return Response({"detail": "Image deleted."})
        return Response({"detail": "No image found."}, status=400)