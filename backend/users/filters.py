import django_filters
from django.db.models import Q
from .models import User

class UserFilter(django_filters.FilterSet):
    """
    Filter set for User model.
    
    Supports filtering by:
    - Text search on email, full_name, telephone_number (icontains)
    - Status flags: is_active, is_staff, is_superuser, is_soft_deleted
    - Date ranges: created_at_after, created_at_before
    """
    email = django_filters.CharFilter(lookup_expr='icontains')
    full_name = django_filters.CharFilter(lookup_expr='icontains')
    telephone_number = django_filters.CharFilter(lookup_expr='icontains')
    
    # Date range filtering
    created_at_after = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_at_before = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    
    class Meta:
        model = User
        fields = [
            'email', 'full_name', 'telephone_number', 
            'is_active', 'is_staff', 'is_superuser', 'is_soft_deleted'
        ]
