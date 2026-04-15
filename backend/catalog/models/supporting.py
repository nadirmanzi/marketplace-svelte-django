import uuid

from django.db import models
from django.utils.text import slugify
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFill
from simple_history.models import HistoricalRecords


class ProductImage(models.Model):
    """
    Image gallery for products and variants.
    """

    image_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(
        "catalog.Product",
        on_delete=models.CASCADE,
        related_name="images",
        db_index=True,
    )
    variant = models.ForeignKey(
        "catalog.ProductVariant",
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
    is_feature = models.BooleanField(default=False, help_text="Set as the primary image.")
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Product Image"
        verbose_name_plural = "Product Images"
        ordering = ["order", "created_at"]

    def __str__(self):
        return f"Image for {self.product.name}"


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

    attribute_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, unique=True, db_index=True)
    input_type = models.CharField(max_length=20, choices=InputType.choices, default=InputType.TEXT)
    unit = models.CharField(max_length=20, blank=True, null=True, help_text="e.g., 'GB', 'kg', 'mm'")
    description = models.TextField(blank=True, default="")

    is_filterable = models.BooleanField(default=True, help_text="Should this appear in the sidebar filters?")
    is_required = models.BooleanField(default=False, help_text="Is this attribute mandatory for its category?")

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

    option_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE, related_name="options")
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
    """

    category = models.ForeignKey("catalog.Category", on_delete=models.CASCADE, related_name="category_attributes")
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE, related_name="assigned_categories")
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
    """

    product = models.ForeignKey("catalog.Product", on_delete=models.CASCADE, related_name="attribute_values")
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE)
    value_text = models.TextField(blank=True, null=True)
    value_number = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    value_boolean = models.BooleanField(blank=True, null=True)
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
    """

    variant = models.ForeignKey(
        "catalog.ProductVariant",
        on_delete=models.CASCADE,
        related_name="attribute_values",
    )
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE)
    value_text = models.TextField(blank=True, null=True)
    value_number = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    value_boolean = models.BooleanField(blank=True, null=True)
    value_options = models.ManyToManyField(AttributeOption, blank=True)

    class Meta:
        verbose_name = "Variant Attribute Value"
        verbose_name_plural = "Variant Attribute Values"
        unique_together = ("variant", "attribute")

    def __str__(self):
        return f"{self.variant.sku} [{self.attribute.name}]"
