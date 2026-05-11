import django_filters
from apps.document.models import Document

class DocumentFilter(django_filters.FilterSet):
    # Time range filtering
    created_after = django_filters.DateTimeFilter(
        field_name="created_at", lookup_expr="gte"
    )
    created_before = django_filters.DateTimeFilter(
        field_name="created_at", lookup_expr="lte"
    )

    # Case-insensitive search on title
    title = django_filters.CharFilter(
        field_name="title", lookup_expr="icontains"
    )

    class Meta:
        model = Document
        fields = ['uploaded_by']