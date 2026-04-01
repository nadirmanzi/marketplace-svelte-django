"""
DRF serializers for catalog models.

Category serializers:
- CategorySerializer: Flat read-only representation.
- CategoryTreeSerializer: Recursive nested representation.
- CategoryWriteSerializer: Input validation for create/update.

Product serializers:
- ProductSerializer: Flat read-only with variant_count.
- ProductDetailSerializer: Includes nested active variants.
- ProductWriteSerializer: Input for create/update.

Variant serializers:
- ProductVariantSerializer: Read-only variant representation.
- ProductVariantWriteSerializer: Input for create/update.
- StockAdjustmentSerializer: Validates quantity_delta.
"""

from rest_framework import serializers
from .models import Category, Product, ProductVariant


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
    """Compact variant representation for embedding inside product responses."""

    in_stock = serializers.BooleanField(read_only=True)

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
        ]
        read_only_fields = fields


class ProductSerializer(serializers.ModelSerializer):
    """Flat read-only representation of a product blueprint."""

    category_name = serializers.CharField(source="category.name", read_only=True, default=None)
    category_id = serializers.UUIDField(source="category.category_id", read_only=True, allow_null=True)
    user_email = serializers.EmailField(source="user.email", read_only=True)
    active_variant_count = serializers.IntegerField(read_only=True)
    is_published = serializers.BooleanField(read_only=True)

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
        return ProductVariantSummarySerializer(qs, many=True).data


class ProductWriteSerializer(serializers.Serializer):
    """Input serializer for creating and updating products."""

    name = serializers.CharField(max_length=255)
    slug = serializers.SlugField(max_length=280, required=False, allow_blank=True)
    description = serializers.CharField(required=False, allow_blank=True, default="")
    base_price = serializers.DecimalField(max_digits=12, decimal_places=2)
    category = serializers.UUIDField(required=False, allow_null=True)
    status = serializers.ChoiceField(
        choices=Product.Status.choices,
        required=False,
        default=Product.Status.PUBLISHED,
    )

    def validate_base_price(self, value):
        if value < 0:
            raise serializers.ValidationError("Base price cannot be negative.")
        return value

    def validate_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Product name cannot be blank.")
        return value


# ---------------------------------------------------------------------------
# Variant Serializers
# ---------------------------------------------------------------------------


class ProductVariantSerializer(serializers.ModelSerializer):
    """Full read-only variant representation including product context."""

    product_name = serializers.CharField(source="product.name", read_only=True)
    product_id = serializers.UUIDField(source="product.product_id", read_only=True)
    in_stock = serializers.BooleanField(read_only=True)

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
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class ProductVariantWriteSerializer(serializers.Serializer):
    """Input serializer for creating and updating variants."""

    product = serializers.UUIDField(required=False, help_text="Parent product UUID (required on create).")
    sku = serializers.CharField(max_length=100)
    name = serializers.CharField(max_length=255)
    price = serializers.DecimalField(max_digits=12, decimal_places=2)
    stock_quantity = serializers.IntegerField(required=False, default=0, min_value=0)
    metadata = serializers.JSONField(required=False, default=dict)
    is_active = serializers.BooleanField(required=False, default=True)

    def validate_price(self, value):
        if value < 0:
            raise serializers.ValidationError("Price cannot be negative.")
        return value

    def validate_sku(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("SKU cannot be blank.")
        return value


class StockAdjustmentSerializer(serializers.Serializer):
    """Input serializer for the adjust-stock action."""

    quantity_delta = serializers.IntegerField(
        help_text="Positive to add stock, negative to reduce. Cannot be zero.",
    )

    def validate_quantity_delta(self, value):
        if value == 0:
            raise serializers.ValidationError("Stock adjustment delta cannot be zero.")
        return value
