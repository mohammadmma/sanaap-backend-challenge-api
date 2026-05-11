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

    # Full-text style search
    search_fields = ['title', 'description']

    # Controlled ordering
    ordering_fields = ['created_at', 'title']
    ordering = ['-created_at']

    pagination_class = StandardResultsSetPagination

    def get_permissions(self):
        if self.action in ['destroy', 'clear_file', 'clear_image']:
            return [IsAdmin()]
        elif self.action in ['create', 'update', 'partial_update']:
            return [IsEditor()]
        return [IsViewer()]

    # IMPORTANT: include MultiPartParser so the view accepts file uploads
    # Without this, file uploads will be silently ignored
    parser_classes = [
        parsers.MultiPartParser,   # for file uploads via form-data
        parsers.FormParser,        # for form fields alongside files
        parsers.JSONParser,        # for JSON-only requests (no files)
    ]

    def perform_create(self, serializer):
        # Automatically set uploaded_by to the current user
        serializer.save(uploaded_by=self.request.user)

    @action(detail=True, methods=['post'], url_path='clear_file')
    def clear_file(self, request, pk=None):
        obj = self.get_object()

        if obj.file:
            with transaction.atomic():
                obj.file = None
                obj.save()
                return Response({"detail": "File deleted."}, status=status.HTTP_204_NO_CONTENT)
        return Response({"detail": "No file found."}, status=400)
    
    @action(detail=True, methods=['post'], url_path='clear_image')
    def clear_image(self, request, pk=None):
        obj = self.get_object()
        if obj.image:
            with transaction.atomic():
                obj.image = None
                obj.save()
                return Response({"detail": "Image deleted."})
        return Response({"detail": "No image found."}, status=400)