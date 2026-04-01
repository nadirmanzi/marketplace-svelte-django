"""
Catalog models for marketplace product organization.

Models:
- Category: Self-referential hierarchy for organizing products.
- Product: Blueprint/template for sellable items (not directly listed).
- ProductVariant: The actual sellable entity, linked to a Product blueprint.

All models use UUID primary keys, auto-generated slugs, audit timestamps,
and django-simple-history for full change tracking.
"""

import uuid
from django.conf import settings
from django.db import models
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from simple_history.models import HistoricalRecords

from .managers import CategoryManager, ProductManager, ProductVariantManager


class Category(models.Model):
    """
    Hierarchical product category.

    Supports infinite-depth nesting via self-referential `parent` FK.
    Top-level categories have parent=None.
    """

    # Identity
    category_id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False
    )
    name = models.CharField(max_length=100, db_index=True)
    slug = models.SlugField(max_length=120, unique=True, db_index=True)
    description = models.TextField(blank=True, default="")
    image = models.ImageField(
        upload_to="category_images/", blank=True, null=True
    )

    # Hierarchy
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="subcategories",
        db_index=True,
    )

    # Status
    is_active = models.BooleanField(default=True, db_index=True)

    # Audit
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    # History tracking
    history = HistoricalRecords()

    # Custom manager
    objects = CategoryManager()

    USERNAME_FIELD = None  # Not an auth model

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        ordering = ["name"]
        permissions = [
            ("can_manage_categories", "Can create, update, and deactivate categories"),
        ]

    def __str__(self):
        if self.parent:
            return f"{self.parent.name} → {self.name}"
        return self.name

    def clean(self):
        """Validate hierarchical integrity.

        Raises:
            ValidationError: If category references itself as parent,
                or if a circular reference is detected in the ancestor chain.
        """
        if self.parent_id and self.parent_id == self.pk:
            raise ValidationError(
                {"parent": "A category cannot be its own parent."}
            )

        # Walk up the ancestor chain to detect circular references
        if self.pk and self.parent:
            visited = {self.pk}
            ancestor = self.parent
            while ancestor is not None:
                if ancestor.pk in visited:
                    raise ValidationError(
                        {"parent": "Circular category reference detected."}
                    )
                visited.add(ancestor.pk)
                ancestor = ancestor.parent

    def save(self, *args, **kwargs):
        """Auto-generate slug from name if not provided, then validate.

        If the slug is empty, it is derived from the name. Uniqueness
        collisions are resolved by appending a numeric suffix.
        """
        if not self.slug:
            self.slug = slugify(self.name)

            # Handle slug collisions by appending a suffix
            base_slug = self.slug
            counter = 1
            qs = Category.objects.all()
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            while qs.filter(slug=self.slug).exists():
                self.slug = f"{base_slug}-{counter}"
                counter += 1

        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def is_root(self) -> bool:
        """True if this is a top-level category."""
        return self.parent_id is None

    @property
    def depth(self) -> int:
        """Return the nesting depth (0 for root categories)."""
        level = 0
        ancestor = self.parent
        while ancestor is not None:
            level += 1
            ancestor = ancestor.parent
        return level


# ---------------------------------------------------------------------------
# Product (Blueprint)
# ---------------------------------------------------------------------------


class Product(models.Model):
    """
    Product blueprint template.

    Defines the shared identity and metadata for a group of sellable variants.
    Products are NOT directly listed to end-users — they are displayed
    through their associated ProductVariants.
    """

    class Status(models.TextChoices):
        PUBLISHED = "published", "Published"
        ARCHIVED = "archived", "Archived"

    # Identity
    product_id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False
    )
    name = models.CharField(max_length=255, db_index=True)
    slug = models.SlugField(max_length=280, unique=True, db_index=True)
    description = models.TextField(blank=True, default="")
    base_price = models.DecimalField(
        max_digits=12, decimal_places=2,
        help_text="Default price for variants that don't override it.",
    )

    # Relationships
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="products",
        db_index=True,
        help_text="Seller/creator of this product.",
    )
    category = models.ForeignKey(
        "catalog.Category",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products",
        db_index=True,
    )

    # Status
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PUBLISHED,
        db_index=True,
    )

    # Audit
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    # History tracking
    history = HistoricalRecords()

    # Custom manager
    objects = ProductManager()

    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "Products"
        ordering = ["-created_at"]
        permissions = [
            ("can_manage_products", "Can create, update, and archive products"),
        ]

    def __str__(self):
        return self.name

    def clean(self):
        """Validate price is positive."""
        if self.base_price is not None and self.base_price < 0:
            raise ValidationError(
                {"base_price": "Base price cannot be negative."}
            )

    def save(self, *args, **kwargs):
        """Auto-generate slug from name if not provided."""
        if not self.slug:
            self.slug = slugify(self.name)

            # Handle slug collisions
            base_slug = self.slug
            counter = 1
            qs = Product.objects.all()
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            while qs.filter(slug=self.slug).exists():
                self.slug = f"{base_slug}-{counter}"
                counter += 1

        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def is_published(self) -> bool:
        return self.status == self.Status.PUBLISHED

    @property
    def active_variant_count(self) -> int:
        return self.variants.filter(is_active=True).count()


# ---------------------------------------------------------------------------
# ProductVariant (Sellable Entity)
# ---------------------------------------------------------------------------


class ProductVariant(models.Model):
    """
    Sellable product variant.

    Each variant belongs to a Product blueprint and represents a specific
    configuration (e.g. size, color) with its own price, stock, and metadata.
    This is what customers actually browse and purchase.
    """

    # Identity
    variant_id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="variants",
        db_index=True,
    )
    sku = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        help_text="Stock Keeping Unit — unique identifier for inventory.",
    )
    name = models.CharField(
        max_length=255,
        help_text="Variant label, e.g. 'Size L - Red'.",
    )

    # Pricing
    price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Variant-specific price (overrides product base_price).",
    )

    # Stock
    stock_quantity = models.PositiveIntegerField(
        default=0,
        help_text="Current available stock. Updated via locked transactions.",
    )

    # Flexible attributes
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Flexible key-value attributes (color, size, weight, etc.).",
    )

    # Status
    is_active = models.BooleanField(default=True, db_index=True)

    # Audit
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    history = HistoricalRecords(excluded_fields=['stock_quantity'])

    # Custom manager
    objects = ProductVariantManager()

    class Meta:
        verbose_name = "Product Variant"
        verbose_name_plural = "Product Variants"
        ordering = ["name"]

    def __str__(self):
        return f"{self.product.name} — {self.name}"

    def clean(self):
        """Validate price is positive."""
        if self.price is not None and self.price < 0:
            raise ValidationError(
                {"price": "Variant price cannot be negative."}
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def in_stock(self) -> bool:
        """True if stock_quantity > 0."""
        return self.stock_quantity > 0
