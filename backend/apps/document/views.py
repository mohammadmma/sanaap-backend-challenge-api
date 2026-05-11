# documents/views.py
from rest_framework import viewsets, parsers, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from .models import Document
from .serializers import DocumentSerializer


class DocumentViewSet(viewsets.ModelViewSet):
    permission_classes = [AllowAny]
    queryset = Document.objects.all().order_by('-created_at')
    serializer_class = DocumentSerializer

    # IMPORTANT: include MultiPartParser so the view accepts file uploads
    # Without this, file uploads will be silently ignored
    parser_classes = [
        parsers.MultiPartParser,   # for file uploads via form-data
        parsers.FormParser,        # for form fields alongside files
        parsers.JSONParser,        # for JSON-only requests (no files)
    ]

    # def perform_create(self, serializer):
    #     # Automatically set uploaded_by to the current user
    #     serializer.save(uploaded_by=self.request.user)