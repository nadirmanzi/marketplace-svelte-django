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
from decimal import Decimal
from django.conf import settings
from django.db import models
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from simple_history.models import HistoricalRecords
from imagekit.models import ImageSpecField, ProcessedImageField
from imagekit.processors import ResizeToFill

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
        upload_to="categories/", blank=True, null=True
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
        blank=True,
        help_text="Stock Keeping Unit — unique identifier for inventory. Auto-generated if not provided.",
    )
    name = models.CharField(
        max_length=255,
        help_text="Variant label, e.g. 'Size L - Red'.",
    )

    # Pricing
    price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Variant-specific price. If null, falls back to product base_price.",
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

    @property
    def effective_price(self) -> Decimal:
        """Return variant price or fallback to product base_price."""
        return self.price if self.price is not None else self.product.base_price


# ---------------------------------------------------------------------------
# Product Image (Gallery)
# ---------------------------------------------------------------------------


class ProductImage(models.Model):
    """
    Image gallery for products and variants.
    """

    image_id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="images",
        db_index=True,
    )
    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="images",
        db_index=True,
        help_text="Optional: link image to a specific variant.",
    )

    image = models.ImageField(upload_to="products/")
    thumbnail = ImageSpecField(
        source="image",
        processors=[ResizeToFill(300, 300)],
        format="WEBP",
        options={"quality": 85},
    )

    alt_text = models.CharField(max_length=255, blank=True, default="")
    is_feature = models.BooleanField(
        default=False, help_text="Set as the primary image."
    )
    order = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Product Image"
        verbose_name_plural = "Product Images"
        ordering = ["order", "created_at"]

    def __str__(self):
        return f"Image for {self.product.name}"


# ---------------------------------------------------------------------------
# Attributes (Specifications)
# ---------------------------------------------------------------------------


class Attribute(models.Model):
    """
    Definition of a product specification (e.g., Color, Memory, Material).
    """

    class InputType(models.TextChoices):
        TEXT = "text", "Text"
        NUMBER = "number", "Number"
        SELECT = "select", "Select (Single)"
        MULTISELECT = "multiselect", "Select (Multiple)"
        BOOLEAN = "boolean", "Boolean"

    attribute_id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False
    )
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, unique=True, db_index=True)
    input_type = models.CharField(
        max_length=20, choices=InputType.choices, default=InputType.TEXT
    )
    unit = models.CharField(
        max_length=20, blank=True, null=True, help_text="e.g., 'GB', 'kg', 'mm'"
    )
    description = models.TextField(blank=True, default="")

    # Config
    is_filterable = models.BooleanField(
        default=True, help_text="Should this appear in the sidebar filters?"
    )
    is_required = models.BooleanField(
        default=False, help_text="Is this attribute mandatory for its category?"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    history = HistoricalRecords()

    class Meta:
        verbose_name = "Attribute"
        verbose_name_plural = "Attributes"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class AttributeOption(models.Model):
    """
    Predefined values for SELECT or MULTISELECT attributes.
    """

    option_id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False
    )
    attribute = models.ForeignKey(
        Attribute, on_delete=models.CASCADE, related_name="options"
    )
    value = models.CharField(max_length=255)

    class Meta:
        verbose_name = "Attribute Option"
        verbose_name_plural = "Attribute Options"
        unique_together = ("attribute", "value")
        ordering = ["value"]

    def __str__(self):
        return f"{self.attribute.name}: {self.value}"


class CategoryAttribute(models.Model):
    """
    Through model linking attributes to specific categories.
    Used for inheritance calculation and validation.
    """

    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name="category_attributes"
    )
    attribute = models.ForeignKey(
        Attribute, on_delete=models.CASCADE, related_name="assigned_categories"
    )
    order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Category Attribute"
        verbose_name_plural = "Category Attributes"
        unique_together = ("category", "attribute")
        ordering = ["order"]

    def __str__(self):
        return f"{self.category.name} -> {self.attribute.name}"


class ProductAttributeValue(models.Model):
    """
    Value for an attribute assigned at the Product (blueprint) level.
    Shared by all variants unless overridden.
    """

    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="attribute_values"
    )
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE)

    # Storage for different types
    value_text = models.TextField(blank=True, null=True)
    value_number = models.DecimalField(
        max_digits=12, decimal_places=2, blank=True, null=True
    )
    value_boolean = models.BooleanField(blank=True, null=True)

    # For SELECT / MULTISELECT
    value_options = models.ManyToManyField(AttributeOption, blank=True)

    class Meta:
        verbose_name = "Product Attribute Value"
        verbose_name_plural = "Product Attribute Values"
        unique_together = ("product", "attribute")

    def __str__(self):
        return f"{self.product.name} [{self.attribute.name}]"


class VariantAttributeValue(models.Model):
    """
    Value for an attribute assigned at the ProductVariant level.
    Overrides or extends the product-level blueprint attributes.
    """

    variant = models.ForeignKey(
        ProductVariant, on_delete=models.CASCADE, related_name="attribute_values"
    )
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE)

    # Storage for different types
    value_text = models.TextField(blank=True, null=True)
    value_number = models.DecimalField(
        max_digits=12, decimal_places=2, blank=True, null=True
    )
    value_boolean = models.BooleanField(blank=True, null=True)

    # For SELECT / MULTISELECT
    value_options = models.ManyToManyField(AttributeOption, blank=True)

    class Meta:
        verbose_name = "Variant Attribute Value"
        verbose_name_plural = "Variant Attribute Values"
        unique_together = ("variant", "attribute")

    def __str__(self):
        return f"{self.variant.sku} [{self.attribute.name}]"
