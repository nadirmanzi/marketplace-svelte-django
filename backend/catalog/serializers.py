"""
DRF serializers for catalog models.

Features:
- Custom PriceField for consistent non-negative validation.
- ProductImageSerializer for gallery management.
- Dynamic price & image fallbacks (Variant -> Product).
- Structured Attribute System with hierarchical inheritance.
"""

from decimal import Decimal
from rest_framework import serializers
from .models import (
    Category,
    Product,
    ProductVariant,
    ProductImage,
    Attribute,
    AttributeOption,
    ProductAttributeValue,
    VariantAttributeValue,
)


# ---------------------------------------------------------------------------
# Reusable Fields
# ---------------------------------------------------------------------------


class PriceField(serializers.DecimalField):
    """
    Custom DecimalField that enforces non-negative values.
    """

    def __init__(self, **kwargs):
        kwargs.setdefault("max_digits", 12)
        kwargs.setdefault("decimal_places", 2)
        kwargs.setdefault("min_value", Decimal("0.00"))
        super().__init__(**kwargs)


# ---------------------------------------------------------------------------
# Attribute Serializers
# ---------------------------------------------------------------------------


class AttributeOptionSerializer(serializers.ModelSerializer):
    """Predefined choice for select/multiselect attributes."""

    class Meta:
        model = AttributeOption
        fields = ["option_id", "value"]


class AttributeSerializer(serializers.ModelSerializer):
    """Definition of an attribute, including its choices if any."""

    options = AttributeOptionSerializer(many=True, read_only=True)

    class Meta:
        model = Attribute
        fields = [
            "attribute_id",
            "name",
            "slug",
            "input_type",
            "unit",
            "description",
            "is_filterable",
            "is_required",
            "options",
        ]


class AttributeValueSerializer(serializers.Serializer):
    """
    Unified representation of an attribute value for the frontend.
    Handles mapping different DB fields (text, number, options) to a single 'value'.
    """

    attribute_id = serializers.UUIDField(source="attribute.attribute_id", read_only=True)
    name = serializers.CharField(source="attribute.name", read_only=True)
    slug = serializers.CharField(source="attribute.slug", read_only=True)
    unit = serializers.CharField(source="attribute.unit", read_only=True, allow_null=True)
    input_type = serializers.CharField(source="attribute.input_type", read_only=True)
    value = serializers.SerializerMethodField()

    def get_value(self, obj):
        attr = obj.attribute
        if attr.input_type == Attribute.InputType.NUMBER:
            return obj.value_number
        if attr.input_type == Attribute.InputType.BOOLEAN:
            return obj.value_boolean
        if attr.input_type in [Attribute.InputType.SELECT, Attribute.InputType.MULTISELECT]:
            options = obj.value_options.all()
            if attr.input_type == Attribute.InputType.SELECT:
                return options[0].value if options.exists() else None
            return [opt.value for opt in options]
        return obj.value_text


class CategoryAttributeInfoSerializer(serializers.Serializer):
    """Helpful metadata for frontends to render product creation forms."""

    attribute = AttributeSerializer()
    order = serializers.IntegerField()


# ---------------------------------------------------------------------------
# Image Serializers
# ---------------------------------------------------------------------------


class ProductImageSerializer(serializers.ModelSerializer):
    """Gallery image representation with thumbnail link."""

    thumbnail = serializers.ImageField(read_only=True)

    class Meta:
        model = ProductImage
        fields = [
            "image_id",
            "image",
            "thumbnail",
            "alt_text",
            "is_feature",
            "order",
            "variant",
        ]


# ---------------------------------------------------------------------------
# Category Serializers
# ---------------------------------------------------------------------------


class CategorySerializer(serializers.ModelSerializer):
    """Flat read-only representation of a category."""

    parent_id = serializers.UUIDField(source="parent.category_id", read_only=True, allow_null=True)
    is_root = serializers.BooleanField(read_only=True)
    depth = serializers.IntegerField(read_only=True)
    subcategory_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = [
            "category_id",
            "name",
            "slug",
            "description",
            "image",
            "parent_id",
            "is_active",
            "is_root",
            "depth",
            "subcategory_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_subcategory_count(self, obj) -> int:
        if hasattr(obj, "_prefetched_objects_cache") and "subcategories" in obj._prefetched_objects_cache:
            return len([c for c in obj.subcategories.all() if c.is_active])
        return obj.subcategories.filter(is_active=True).count()


class CategoryTreeSerializer(serializers.ModelSerializer):
    """Recursive nested representation for the full category tree."""

    children = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = [
            "category_id",
            "name",
            "slug",
            "description",
            "image",
            "is_active",
            "children",
        ]
        read_only_fields = fields

    def get_children(self, obj):
        children = obj.subcategories.filter(is_active=True).order_by("name")
        return CategoryTreeSerializer(children, many=True, context=self.context).data


class CategoryWriteSerializer(serializers.Serializer):
    """Input serializer for creating and updating categories."""

    name = serializers.CharField(max_length=100)
    slug = serializers.SlugField(max_length=120, required=False, allow_blank=True)
    description = serializers.CharField(required=False, allow_blank=True, default="")
    image = serializers.ImageField(required=False, allow_null=True)
    parent = serializers.UUIDField(required=False, allow_null=True)
    is_active = serializers.BooleanField(required=False, default=True)

    def validate_parent(self, value):
        if value is None:
            return value
        if not Category.objects.filter(pk=value).exists():
            raise serializers.ValidationError("Parent category does not exist.")
        return value

    def validate_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Category name cannot be blank.")
        return value


# ---------------------------------------------------------------------------
# Product Serializers
# ---------------------------------------------------------------------------


class ProductVariantSummarySerializer(serializers.ModelSerializer):
    """Compact variant representation with fallbacks and attributes."""

    in_stock = serializers.BooleanField(read_only=True)
    price = serializers.DecimalField(
        max_digits=12, decimal_places=2, source="effective_price", read_only=True
    )
    images = serializers.SerializerMethodField()
    attributes = AttributeValueSerializer(source="attribute_values", many=True, read_only=True)

    class Meta:
        model = ProductVariant
        fields = [
            "variant_id",
            "sku",
            "name",
            "price",
            "stock_quantity",
            "metadata",
            "is_active",
            "in_stock",
            "images",
            "attributes",
        ]
        read_only_fields = fields

    def get_images(self, obj):
        """Fallback to product images if variant has none."""
        images = obj.images.all()
        if not images.exists():
            images = obj.product.images.filter(variant__isnull=True)
        return ProductImageSerializer(images, many=True, context=self.context).data


class ProductSerializer(serializers.ModelSerializer):
    """Flat product representation with images and attributes."""

    category_name = serializers.CharField(source="category.name", read_only=True, default=None)
    category_id = serializers.UUIDField(source="category.category_id", read_only=True, allow_null=True)
    user_email = serializers.EmailField(source="user.email", read_only=True)
    active_variant_count = serializers.IntegerField(read_only=True)
    is_published = serializers.BooleanField(read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    attributes = AttributeValueSerializer(source="attribute_values", many=True, read_only=True)

    class Meta:
        model = Product
        fields = [
            "product_id",
            "name",
            "slug",
            "description",
            "base_price",
            "status",
            "is_published",
            "category_id",
            "category_name",
            "user_email",
            "active_variant_count",
            "images",
            "attributes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class ProductDetailSerializer(ProductSerializer):
    """Product with nested active variants for detail views."""

    variants = serializers.SerializerMethodField()

    class Meta(ProductSerializer.Meta):
        fields = ProductSerializer.Meta.fields + ["variants"]

    def get_variants(self, obj):
        qs = obj.variants.filter(is_active=True).order_by("name")
        return ProductVariantSummarySerializer(qs, many=True, context=self.context).data


class ProductWriteSerializer(serializers.Serializer):
    """Input serializer for creating and updating products."""

    name = serializers.CharField(max_length=255)
    slug = serializers.SlugField(max_length=280, required=False, allow_blank=True)
    description = serializers.CharField(required=False, allow_blank=True, default="")
    base_price = PriceField()
    category = serializers.UUIDField(required=False, allow_null=True)
    status = serializers.ChoiceField(
        choices=Product.Status.choices,
        required=False,
        default=Product.Status.PUBLISHED,
    )
    # Add attributes as a flexible dictionary
    attributes = serializers.DictField(required=False, child=serializers.JSONField())
    user = serializers.UUIDField(required=False, allow_null=True)

    def validate_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Product name cannot be blank.")
        return value


# ---------------------------------------------------------------------------
# Variant Serializers
# ---------------------------------------------------------------------------


class ProductVariantSerializer(serializers.ModelSerializer):
    """Detailed variant representation with fallbacks and attributes."""

    product_name = serializers.CharField(source="product.name", read_only=True)
    product_id = serializers.UUIDField(source="product.product_id", read_only=True)
    in_stock = serializers.BooleanField(read_only=True)
    price = serializers.DecimalField(
        max_digits=12, decimal_places=2, source="effective_price", read_only=True
    )
    images = serializers.SerializerMethodField()
    attributes = AttributeValueSerializer(source="attribute_values", many=True, read_only=True)

    class Meta:
        model = ProductVariant
        fields = [
            "variant_id",
            "product_id",
            "product_name",
            "sku",
            "name",
            "price",
            "stock_quantity",
            "metadata",
            "is_active",
            "in_stock",
            "images",
            "attributes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_images(self, obj):
        images = obj.images.all()
        if not images.exists():
            images = obj.product.images.filter(variant__isnull=True)
        return ProductImageSerializer(images, many=True, context=self.context).data


class ProductVariantWriteSerializer(serializers.Serializer):
    """Input serializer for variants with custom PriceField and attributes."""

    product = serializers.UUIDField(required=False)
    sku = serializers.CharField(max_length=100, required=False, allow_blank=True)
    name = serializers.CharField(max_length=255)
    price = PriceField(required=False, allow_null=True)
    stock_quantity = serializers.IntegerField(required=False, default=0, min_value=0)
    metadata = serializers.JSONField(required=False, default=dict)
    is_active = serializers.BooleanField(required=False, default=True)
    attributes = serializers.DictField(required=False, child=serializers.JSONField())

    def validate_sku(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("SKU cannot be blank.")
        return value


class StockAdjustmentSerializer(serializers.Serializer):
    """Input serializer for the adjust-stock action."""

    quantity_delta = serializers.IntegerField()

    def validate_quantity_delta(self, value):
        if value == 0:
            raise serializers.ValidationError("Stock adjustment delta cannot be zero.")
        return value
