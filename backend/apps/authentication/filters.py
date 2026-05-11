import django_filters
from django.contrib.auth import get_user_model
User = get_user_model()


class UserFilter(django_filters.FilterSet):
    is_active = django_filters.BooleanFilter()
    joined_after = django_filters.DateTimeFilter(
        field_name="date_joined", lookup_expr="gte"
    )
    joined_before = django_filters.DateTimeFilter(
        field_name="date_joined", lookup_expr="lte"
    )
    username = django_filters.CharFilter(
        field_name='username',
        lookup_expr='icontains'
    )
    role = django_filters.CharFilter(method='filter_by_role')

    class Meta:
        model = User
        fields = ['is_active']

    def filter_by_role(self, queryset, name, value):
        return queryset.filter(groups__name=value)