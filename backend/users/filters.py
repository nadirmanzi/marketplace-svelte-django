"""
Advanced filtering for User model using django-filter.

This module provides UserFilter which enables powerful query filtering on User model
via REST API query parameters:

URL example: GET /users/?email=john&is_active=true&email_verification_status=verified

Filter Types:
- Text Filters: email, first_name, last_name (case-insensitive contains)
- Computed Filters: full_name (searches both first_name OR last_name with Q objects)
- Exact Filters: telephone_number (E.164 format)
- Choice Filters: email_verification_status, telephone_verification_status
- Boolean Filters: is_active, is_staff, is_superuser, is_soft_deleted
- Date Filters: created_at (range), created_after, created_before

Use Cases:
- Search users by email or name via admin/API
- Filter by verification status (pending, verified, rejected)
- Find active staff members: ?is_staff=true&is_active=true
- List soft-deleted users: ?is_soft_deleted=true
- Find users by creation date: ?created_after=2024-01-01&created_before=2024-12-31
- Filter by phone verification: ?telephone_verification_status=verified

Integration:
- Configured globally in settings.py DEFAULT_FILTER_BACKENDS
- Used automatically by DRF viewsets with FilterSet classes
- Query parameters are case-insensitive and optional

Dependencies:
- django_filters: FilterSet, CharFilter, DateTimeFromToRangeFilter, ChoiceFilter, BooleanFilter
- django.db.models.Q: For combining filters with OR logic in full_name search
"""

import django_filters
from django.contrib.auth import get_user_model
from django_filters import rest_framework as filters

User = get_user_model()


class UserFilter(filters.FilterSet):
    """
    FilterSet for User model.
    
    Supported filters:
    - email: Exact or partial match (case-insensitive)
    - first_name: Partial match (case-insensitive)
    - last_name: Partial match (case-insensitive)
    - full_name: Search both first_name and last_name
    - telephone_number: Exact match
    - email_verification_status: Choice filter
    - telephone_verification_status: Choice filter
    - is_active: Boolean filter
    - is_staff: Boolean filter
    - is_superuser: Boolean filter
    - is_soft_deleted: Boolean filter
    - created_at: Date range filter
    - created_after: Datetime filter (greater than)
    - created_before: Datetime filter (less than)
    """

    # Email filters
    email = django_filters.CharFilter(
        field_name="email",
        lookup_expr="icontains",
        label="Email (contains)",
    )

    # Name filters
    first_name = django_filters.CharFilter(
        field_name="first_name",
        lookup_expr="icontains",
        label="First name (contains)",
    )

    last_name = django_filters.CharFilter(
        field_name="last_name",
        lookup_expr="icontains",
        label="Last name (contains)",
    )

    full_name = django_filters.CharFilter(
        method="filter_full_name",
        label="Full name (contains)",
    )

    # Phone filter
    telephone_number = django_filters.CharFilter(
        field_name="telephone_number",
        lookup_expr="exact",
        label="Phone number (exact)",
    )

    # Verification status filters
    email_verification_status = django_filters.ChoiceFilter(
        field_name="email_verification_status",
        choices=[
            ("pending", "Pending"),
            ("verified", "Verified"),
        ],
        label="Email verification status",
    )

    telephone_verification_status = django_filters.ChoiceFilter(
        field_name="telephone_verification_status",
        choices=[
            ("pending", "Pending"),
            ("verified", "Verified"),
            ("no_number", "No number"),
        ],
        label="Phone verification status",
    )

    # Account status filters
    is_active = django_filters.BooleanFilter(
        field_name="is_active",
        label="Is active",
    )

    is_staff = django_filters.BooleanFilter(
        field_name="is_staff",
        label="Is staff",
    )

    is_superuser = django_filters.BooleanFilter(
        field_name="is_superuser",
        label="Is superuser",
    )

    is_soft_deleted = django_filters.BooleanFilter(
        field_name="is_soft_deleted",
        label="Is soft-deleted",
    )

    # Date/time filters
    created_at = django_filters.DateFromToRangeFilter(
        field_name="created_at",
        label="Created date range",
    )

    created_after = django_filters.DateTimeFilter(
        field_name="created_at",
        lookup_expr="gte",
        label="Created after",
    )

    created_before = django_filters.DateTimeFilter(
        field_name="created_at",
        lookup_expr="lte",
        label="Created before",
    )

    class Meta:
        model = User
        fields = []

    def filter_full_name(self, queryset, name, value):
        """Filter by first_name or last_name with OR logic (case-insensitive contains).
        
        Args:
            queryset: Initial User queryset to filter
            name: Filter field name (unused; method-based filter)
            value: Search string (e.g., "John")
        
        Returns:
            Filtered queryset where first_name contains value OR last_name contains value
        
        Examples:
            value='John' -> Returns users with first_name='John*' OR last_name='John*'
            value='Doe' -> Returns users where any name field contains 'Doe'
            value='' -> Returns original queryset unchanged
        
        Notes:
            - Uses Q objects to combine conditions with OR (|) logic
            - Case-insensitive search via icontains (works across databases)
            - Empty value returns unmodified queryset (user didn't filter)
        """
        # Skip filtering if search value is empty (user didn't provide a search term).
        if not value:
            return queryset
        
        # Use Q objects to combine conditions with OR logic.
        # Returns users matching EITHER first_name OR last_name (not both required).
        # Example: searching "John" finds both "John Doe" and "Jane John" (if last name).
        return queryset.filter(
            django_filters.Q(first_name__icontains=value)
            | django_filters.Q(last_name__icontains=value)
        )
