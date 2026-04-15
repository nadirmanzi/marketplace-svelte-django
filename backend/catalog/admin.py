"""
Django admin configuration for catalog models.

Registers Category, Product, and ProductVariant with history
tracking, custom forms, and inline variant editing.
"""

from django.contrib import admin
from django.utils.safestring import mark_safe
from simple_history.admin import SimpleHistoryAdmin
from imagekit.admin import AdminThumbnail

from .models import (
    Category,
    Product,
    ProductVariant,
    ProductImage,
    Attribute,
    AttributeOption,
    CategoryAttribute,
    ProductAttributeValue,
    VariantAttributeValue,
    Discount,
)
from .forms import CategoryAdminForm


# ---------------------------------------------------------------------------
# Category Admin
# ---------------------------------------------------------------------------


class CategoryAttributeInline(admin.TabularInline):
    """Inline for assigning attributes to categories."""

    model = CategoryAttribute
    extra = 0
    raw_id_fields = ("attribute",)


@admin.register(Category)
class CategoryAdmin(SimpleHistoryAdmin):
    """Admin interface for Category with history tracking."""

    form = CategoryAdminForm

    list_display = ("name", "slug", "parent", "is_active", "created_at")
    list_filter = ("is_active", "parent")
    search_fields = ("name", "slug", "description")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("name",)
    readonly_fields = ("category_id", "created_at", "updated_at")
    inlines = [CategoryAttributeInline]

    fieldsets = (
        (None, {"fields": ("category_id", "name", "slug", "description", "image")}),
        ("Hierarchy", {"fields": ("parent",)}),
        ("Status", {"fields": ("is_active",)}),
        ("Timestamps", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )


# ---------------------------------------------------------------------------
# Inlines
# ---------------------------------------------------------------------------


class ProductImageInline(admin.TabularInline):
    """Inline editor for the product/variant image gallery."""

    model = ProductImage
    extra = 0
    fields = ("image", "admin_thumbnail", "alt_text", "is_feature", "order", "variant")
    readonly_fields = ("admin_thumbnail",)

    admin_thumbnail = AdminThumbnail(image_field="thumbnail")


class ProductVariantInline(admin.TabularInline):
    """Inline editor for variants within the Product admin page."""

    model = ProductVariant
    extra = 0
    readonly_fields = ("variant_id", "created_at", "updated_at")
    fields = ("variant_id", "sku", "name", "price", "stock_quantity", "is_active", "metadata")


class ProductAttributeValueInline(admin.TabularInline):
    """Inline for viewing/editing structured attribute values for products."""

    model = ProductAttributeValue
    extra = 0
    raw_id_fields = ("attribute",)


class VariantAttributeValueInline(admin.TabularInline):
    """Inline for viewing/editing structured attribute values for variants."""

    model = VariantAttributeValue
    extra = 0
    raw_id_fields = ("attribute",)


@admin.register(Product)
class ProductAdmin(SimpleHistoryAdmin):
    """Admin interface for Product with inline variants."""

    list_display = ("name", "slug", "status", "base_price", "user", "category", "created_at")
    list_filter = ("status", "category")
    search_fields = ("name", "slug", "description")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("-created_at",)
    readonly_fields = ("product_id", "created_at", "updated_at")
    raw_id_fields = ("user", "category")
    inlines = [ProductVariantInline, ProductImageInline, ProductAttributeValueInline]

    def get_changeform_initial_data(self, request):
        initial = super().get_changeform_initial_data(request)
        initial["user"] = request.user.pk
        return initial

    fieldsets = (
        (None, {"fields": ("product_id", "name", "slug", "description", "base_price")}),
        ("Relationships", {"fields": ("user", "category")}),
        ("Status", {"fields": ("status",)}),
        ("Timestamps", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )


# ---------------------------------------------------------------------------
# ProductVariant Admin
# ---------------------------------------------------------------------------


@admin.register(ProductVariant)
class ProductVariantAdmin(SimpleHistoryAdmin):
    """Standalone admin for ProductVariant with history tracking."""

    list_display = ("sku", "name", "product", "price", "stock_quantity", "is_active", "created_at")
    list_filter = ("is_active", "product")
    search_fields = ("sku", "name")
    ordering = ("name",)
    readonly_fields = ("variant_id", "created_at", "updated_at")
    raw_id_fields = ("product",)
    inlines = [ProductImageInline, VariantAttributeValueInline]

    fieldsets = (
        (None, {"fields": ("variant_id", "product", "sku", "name")}),
        ("Pricing & Stock", {"fields": ("price", "stock_quantity")}),
        ("Attributes", {"fields": ("metadata",)}),
        ("Status", {"fields": ("is_active",)}),
        ("Timestamps", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )


# ---------------------------------------------------------------------------
# Attribute Admin
# ---------------------------------------------------------------------------


class AttributeOptionInline(admin.TabularInline):
    """Inline editor for attribute choices."""

    model = AttributeOption
    extra = 0


@admin.register(Attribute)
class AttributeAdmin(SimpleHistoryAdmin):
    """Admin interface for managing the global attribute definitions."""

    list_display = ("name", "slug", "input_type", "unit", "is_required", "is_filterable")
    list_filter = ("input_type", "is_required", "is_filterable")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [AttributeOptionInline]


# ---------------------------------------------------------------------------
# Discount Admin
# ---------------------------------------------------------------------------


@admin.register(Discount)
class DiscountAdmin(SimpleHistoryAdmin):
    """Admin interface for discount configuration and lifecycle controls."""

    list_display = (
        "name",
        "discount_type_badge",
        "value",
        "scope_summary",
        "status_badge",
        "start_date",
        "end_date",
    )
    list_filter = ()
    search_fields = ("name", "description", "discount_id")
    ordering = ("-start_date",)
    readonly_fields = ("discount_id", "created_at", "updated_at")
    filter_horizontal = ("categories", "products", "variants")
    actions = ("invalidate_selected_discounts",)

    fieldsets = (
        (None, {"fields": ("discount_id", "name", "description")}),
        ("Configuration", {"fields": ("discount_type", "value")}),
        ("Scope", {"fields": ("categories", "products", "variants")}),
        ("Schedule", {"fields": ("start_date", "end_date")}),
        ("Status", {"fields": ("is_active_override",)}),
        ("Timestamps", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def discount_type_badge(self, obj):
        if obj.discount_type == obj.DiscountType.PERCENTAGE:
            return mark_safe(
                '<span style="background-color: #2980b9; color: white; padding: 2px 8px; '
                'border-radius: 10px; font-size: 10px; font-weight: bold;">PERCENT</span>'
            )
        return mark_safe(
            '<span style="background-color: #8e44ad; color: white; padding: 2px 8px; '
            'border-radius: 10px; font-size: 10px; font-weight: bold;">FIXED</span>'
        )

    def status_badge(self, obj):
        if obj.is_active_override:
            return mark_safe(
                '<span style="background-color: #c0392b; color: white; padding: 2px 8px; '
                'border-radius: 10px; font-size: 10px; font-weight: bold;">INVALIDATED</span>'
            )
        if obj.is_active:
            return mark_safe(
                '<span style="background-color: #27ae60; color: white; padding: 2px 8px; '
                'border-radius: 10px; font-size: 10px; font-weight: bold;">ACTIVE</span>'
            )
        return mark_safe(
            '<span style="background-color: #7f8c8d; color: white; padding: 2px 8px; '
            'border-radius: 10px; font-size: 10px; font-weight: bold;">SCHEDULED/EXPIRED</span>'
        )

    def scope_summary(self, obj):
        categories_count = obj.categories.count()
        products_count = obj.products.count()
        variants_count = obj.variants.count()
        return f"C:{categories_count} P:{products_count} V:{variants_count}"

    discount_type_badge.short_description = "Type"
    status_badge.short_description = "Status"
    scope_summary.short_description = "Scopes"

    @admin.action(description="Invalidate selected discounts (kill-switch ON)")
    def invalidate_selected_discounts(self, request, queryset):
        updated = queryset.filter(is_active_override=False).update(is_active_override=True)
        already_invalidated = queryset.count() - updated

        if already_invalidated:
            self.message_user(
                request,
                f"Invalidated {updated} discount(s). {already_invalidated} were already invalidated.",
            )
        else:
            self.message_user(request, f"Invalidated {updated} discount(s).")
