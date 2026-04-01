"""
Django-filter FilterSets for catalog models.

CategoryFilter — name, is_active, parent, date range
ProductFilter — name, status, category, user, date range
ProductVariantFilter — sku, is_active, in_stock, price range, product
"""

import django_filters
from .models import Category, Product, ProductVariant


# ---------------------------------------------------------------------------
# Category Filter
# ---------------------------------------------------------------------------


class CategoryFilter(django_filters.FilterSet):
    """FilterSet for admin category listing."""

    name = django_filters.CharFilter(lookup_expr="icontains")
    is_root = django_filters.BooleanFilter(method="filter_is_root")

    created_at_after = django_filters.DateTimeFilter(
        field_name="created_at", lookup_expr="gte"
    )
    created_at_before = django_filters.DateTimeFilter(
        field_name="created_at", lookup_expr="lte"
    )

    class Meta:
        model = Category
        fields = ["name", "is_active", "parent"]

    def filter_is_root(self, queryset, name, value):
        if value:
            return queryset.filter(parent__isnull=True)
        return queryset.filter(parent__isnull=False)


# ---------------------------------------------------------------------------
# Product Filter
# ---------------------------------------------------------------------------


class ProductFilter(django_filters.FilterSet):
    """FilterSet for product management listing."""

    name = django_filters.CharFilter(lookup_expr="icontains")
    description = django_filters.CharFilter(lookup_expr="icontains")
    min_price = django_filters.NumberFilter(field_name="base_price", lookup_expr="gte")
    max_price = django_filters.NumberFilter(field_name="base_price", lookup_expr="lte")

    created_at_after = django_filters.DateTimeFilter(
        field_name="created_at", lookup_expr="gte"
    )
    created_at_before = django_filters.DateTimeFilter(
        field_name="created_at", lookup_expr="lte"
    )

    class Meta:
        model = Product
        fields = ["name", "status", "category", "user"]


# ---------------------------------------------------------------------------
# ProductVariant Filter
# ---------------------------------------------------------------------------


class ProductVariantFilter(django_filters.FilterSet):
    """FilterSet for variant management listing."""

    sku = django_filters.CharFilter(lookup_expr="icontains")
    name = django_filters.CharFilter(lookup_expr="icontains")
    min_price = django_filters.NumberFilter(field_name="price", lookup_expr="gte")
    max_price = django_filters.NumberFilter(field_name="price", lookup_expr="lte")
    in_stock = django_filters.BooleanFilter(method="filter_in_stock")

    class Meta:
        model = ProductVariant
        fields = ["sku", "name", "is_active", "product"]

    def filter_in_stock(self, queryset, name, value):
        if value:
            return queryset.filter(stock_quantity__gt=0)
        return queryset.filter(stock_quantity=0)
