# documents/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DocumentViewSet

router = DefaultRouter()
router.register(r'doc-crud', DocumentViewSet, basename="doc_crud")

urlpatterns = [
    path('', include(router.urls)),
]