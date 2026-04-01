"""
Custom managers for catalog models.

Provides filtered querysets for common access patterns:
- active(): Only visible categories.
- roots(): Top-level categories (no parent).
- with_children(): Prefetches subcategories for tree rendering.
"""

from django.db import models


class CategoryQuerySet(models.QuerySet):
    """Chainable queryset methods for Category."""

    def active(self):
        """Return only active (visible) categories."""
        return self.filter(is_active=True)

    def roots(self):
        """Return top-level categories (no parent)."""
        return self.filter(parent__isnull=True)

    def with_children(self):
        """Prefetch immediate subcategories for efficient tree rendering."""
        return self.prefetch_related("subcategories")


class CategoryManager(models.Manager):
    """Default manager for Category, backed by CategoryQuerySet."""

    def get_queryset(self):
        return CategoryQuerySet(self.model, using=self._db)

    def active(self):
        return self.get_queryset().active()

    def roots(self):
        return self.get_queryset().roots()

    def active_roots(self):
        """Convenience: active top-level categories with children prefetched."""
        return self.get_queryset().active().roots().with_children()


# ---------------------------------------------------------------------------
# Product Manager
# ---------------------------------------------------------------------------


class ProductQuerySet(models.QuerySet):
    """Chainable queryset methods for Product."""

    def published(self):
        """Return only published products."""
        return self.filter(status="published")

    def archived(self):
        """Return only archived products."""
        return self.filter(status="archived")

    def by_user(self, user):
        """Return products owned by a specific user."""
        return self.filter(user=user)

    def by_category(self, category):
        """Return products in a specific category."""
        return self.filter(category=category)


class ProductManager(models.Manager):
    """Default manager for Product."""

    def get_queryset(self):
        return ProductQuerySet(self.model, using=self._db)

    def published(self):
        return self.get_queryset().published()

    def by_user(self, user):
        return self.get_queryset().by_user(user)

    def by_category(self, category):
        return self.get_queryset().by_category(category)


# ---------------------------------------------------------------------------
# ProductVariant Manager
# ---------------------------------------------------------------------------


class ProductVariantQuerySet(models.QuerySet):
    """Chainable queryset methods for ProductVariant."""

    def active(self):
        """Return only active variants."""
        return self.filter(is_active=True)

    def in_stock(self):
        """Return variants with stock_quantity > 0."""
        return self.filter(stock_quantity__gt=0)

    def for_product(self, product):
        """Return variants belonging to a specific product."""
        return self.filter(product=product)


class ProductVariantManager(models.Manager):
    """Default manager for ProductVariant."""

    def get_queryset(self):
        return ProductVariantQuerySet(self.model, using=self._db)

    def active(self):
        return self.get_queryset().active()

    def in_stock(self):
        return self.get_queryset().in_stock()

    def for_product(self, product):
        return self.get_queryset().for_product(product)

    def active_in_stock(self):
        """Convenience: active variants that are in stock."""
        return self.get_queryset().active().in_stock()

